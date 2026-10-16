package com.trioncompasitor.vqstudio;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
/**
 * Completely offline deterministic model recipes. Accepts ordinary language
 * hints but NOT arbitrary text-to-mesh AI. No files, network, or code execution.
 */
public final class OfflineGeometry {
  private OfflineGeometry(){}
  public static String supported(String prompt){
    String p=prompt.toLowerCase(Locale.ROOT);
    if(p.matches("(?s).*\\b(sword|blade|dagger)\\b.*"))return "sword";
    if(p.matches("(?s).*\\b(chest|crate|box)\\b.*"))return "chest";
    if(p.matches("(?s).*\\b(terrain|hill|mountain|landscape)\\b.*"))return "terrain";
    if(p.matches("(?s).*\\b(tree|forest|pine|oak)\\b.*"))return "tree";
    throw new IllegalArgumentException("Supported offline shapes: tree, sword, chest, or terrain. Include one in your prompt.");
  }
  public static byte[] generate(String prompt,int detail,BooleanSupplier cancel)throws Exception{
    if(prompt==null||prompt.trim().isEmpty()||prompt.length()>500)
      throw new IllegalArgumentException("Write a prompt of 1–500 characters");
    if(detail!=1&&detail!=2)throw new IllegalArgumentException("Invalid revision");
    String shape=supported(prompt);
    String p=prompt.toLowerCase(Locale.ROOT);
    float factor=p.contains("small")?0.75f:p.contains("large")||p.contains("giant")?1.3f:1f;
    Maker m=new Maker(cancel);
    if(shape.equals("tree")){
      m.box(0,.75f,0,.25f,1.5f,.25f);
      m.cone(0,1.7f,0,.83f,1.85f,detail==1?7:16);
      if(detail==2){
        for(int i=0;i<7;i++){
          double angle=i*Math.PI*2/7;
          float x=(float)Math.cos(angle)*.35f,z=(float)Math.sin(angle)*.35f;
          m.cone(x,1.23f,z,.38f,.76f,10);
        }
      }
    }else if(shape.equals("sword")){
      m.box(0,.48f,0,.15f,.96f,.14f); // hilt
      m.box(0,.98f,0,.95f,.12f,.22f); // crossguard
      m.box(0,2.02f,0,.24f,2f,.09f); // blade
      m.cone(0,3.1f,0,.18f,.35f,detail==1?4:8);
      if(detail==2)m.box(0,.28f,0,.30f,.18f,.24f);
    }else if(shape.equals("chest")){
      m.box(0,.53f,0,1.8f,1.06f,1.05f);
      m.box(0,1.2f,0,1.9f,.3f,1.1f);
      if(detail==2){
        for(float x:new float[]{-.7f,.7f}){
          m.box(x,.58f,.54f,.13f,.94f,.10f);
          m.box(x,.58f,-.54f,.13f,.94f,.10f);
        }
        m.box(0,.77f,.57f,.25f,.31f,.12f);
      }
    }else{
      int n=detail==1?8:22;
      int[][] v=new int[n+1][n+1];
      for(int i=0;i<=n;i++)for(int j=0;j<=n;j++){
        float x=(float)(i-n/2.0)*.27f,y=(float)(.7*Math.exp(-Math.pow((i-n*.47)/n*3,2)-Math.pow((j-n*.51)/n*3,2))
              +.12*Math.sin(i*.8)*Math.cos(j*.7));
        float z=(float)(j-n/2.0)*.27f;
        v[i][j]=m.vertex(x,y,z);
      }
      for(int i=0;i<n;i++)for(int j=0;j<n;j++){
        m.face(v[i][j],v[i+1][j],v[i+1][j+1]);
        m.face(v[i][j],v[i+1][j+1],v[i][j+1]);
      }
    }
    return m.serialize(factor);
  }
  public interface BooleanSupplier{boolean cancelled();}
  private static final class Maker{
    private final ArrayList<float[]> vertices=new ArrayList<>();
    private final ArrayList<int[]> triangles=new ArrayList<>();
    private final BooleanSupplier cancelled;
    Maker(BooleanSupplier stop){cancelled=stop;}
    int vertex(float x,float y,float z){
      if(cancelled.cancelled())throw new IllegalStateException("Cancelled");
      if(vertices.size()>40000)throw new IllegalArgumentException("Model budget exceeded");
      vertices.add(new float[]{x,y,z});return vertices.size();
    }
    void face(int a,int b,int c){triangles.add(new int[]{a,b,c});}
    void box(float x,float y,float z,float w,float h,float d){
      float[][] vv={{-1,-1,-1},{1,-1,-1},{1,1,-1},{-1,1,-1},
          {-1,-1,1},{1,-1,1},{1,1,1},{-1,1,1}};
      int[] idx=new int[8];
      for(int i=0;i<8;i++)idx[i]=vertex(x+vv[i][0]*w/2,y+vv[i][1]*h/2,z+vv[i][2]*d/2);
      int[][] ff={{0,2,1},{0,3,2},{4,5,6},{4,6,7},
          {0,1,5},{0,5,4},{1,2,6},{1,6,5},{2,3,7},{2,7,6},{3,0,4},{3,4,7}};
      for(int[] f:ff)face(idx[f[0]],idx[f[1]],idx[f[2]]);
    }
    void cone(float x,float y,float z,float radius,float height,int segments){
      int apex=vertex(x,y+height/2,z);
      int center=vertex(x,y-height/2,z);
      int[] perimeter=new int[segments];
      for(int i=0;i<segments;i++){
        double rad=Math.PI*2*i/segments;
        perimeter[i]=vertex(x+radius*(float)Math.cos(rad),y-height/2,z+radius*(float)Math.sin(rad));
      }
      for(int i=0;i<segments;i++){
        int a=perimeter[i],b=perimeter[(i+1)%segments];
        face(apex,a,b);face(center,b,a);
      }
    }
    byte[] serialize(float scale){
      if(vertices.size()<3||triangles.isEmpty())throw new IllegalArgumentException("Empty source");
      StringBuilder b=new StringBuilder("# VEYLQUORIN OFFLINE PROCEDURAL OBJ\n");
      for(float[] p:vertices)b.append(String.format(Locale.ROOT,"v %.5f %.5f %.5f\n",p[0]*scale,p[1]*scale,p[2]*scale));
      for(int[] f:triangles)b.append("f ").append(f[0]).append(" ").append(f[1]).append(" ").append(f[2]).append("\n");
      byte[] out=b.toString().getBytes(StandardCharsets.UTF_8);
      if(out.length>8*1024*1024)throw new IllegalArgumentException("Model exceeds limit");
      return out;
    }
  }
}