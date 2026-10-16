package com.trioncompasitor.vqstudio;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

/** Bounded, read-only triangle OBJ parser for the mobile VQ preview. */
public final class MeshData {
  public final float[][] vertices;
  public final int[][] triangles;
  public final String label;
  private MeshData(float[][] v,int[][] t,String s){vertices=v;triangles=t;label=s;}
  public static MeshData sample(){
    float[][] v={{-1f,-1f,-1f},{1f,-1f,-1f},{1f,1f,-1f},{-1f,1f,-1f},
                 {-1f,-1f,1f},{1f,-1f,1f},{1f,1f,1f},{-1f,1f,1f},
                 {0,1.9f,0}};
    int[][] t={{0,2,1},{0,3,2},{4,5,6},{4,6,7},
       {0,1,5},{0,5,4},{1,2,6},{1,6,5},{2,3,7},{2,7,6},{3,0,4},{3,4,7},
       {3,6,8},{3,8,7},{2,8,6}};
    return new MeshData(v,t,"DEMONSTRATION MESH — NOT A GENERATED MODEL");
  }
  public static MeshData read(InputStream stream,String name)throws IOException{
    if(stream==null)throw new IOException("No OBJ stream");
    ArrayList<float[]> verts=new ArrayList<>();
    ArrayList<int[]> tris=new ArrayList<>();
    try(BufferedReader r=new BufferedReader(new InputStreamReader(
              new BoundedInputStream(stream,8*1024*1024),StandardCharsets.UTF_8))){
      String line;
      int lines=0;
      while((line=r.readLine())!=null){
        if(++lines>240000)throw new IOException("OBJ has too many lines");
        line=line.trim();
        if(line.startsWith("v ")){
          String[] a=line.split("\\s+");
          if(a.length<4)throw new IOException("Invalid vertex");
          if(verts.size()>=140000)throw new IOException("OBJ vertex limit");
          float[] p={Float.parseFloat(a[1]),Float.parseFloat(a[2]),Float.parseFloat(a[3])};
          for(float f:p)if(!Float.isFinite(f)||Math.abs(f)>100000)throw new IOException("Nonfinite/out-of-bounds vertex");
          verts.add(p);
        }else if(line.startsWith("f ")){
          String[] a=line.split("\\s+");
          if(a.length!=4)throw new IOException("Triangulated OBJ required");
          if(tris.size()>=120000)throw new IOException("OBJ triangle limit");
          int[] face=new int[3];
          for(int i=0;i<3;i++){
            String idx=a[i+1].split("/",-1)[0];
            int k=Integer.parseInt(idx);
            face[i]=k>0?k-1:verts.size()+k;
            if(face[i]<0||face[i]>=verts.size())throw new IOException("Face index out of range");
          }
          tris.add(face);
        }
      }
    }catch(NumberFormatException e){throw new IOException("Bad OBJ numeric value",e);}
    if(verts.size()<3||tris.isEmpty())throw new IOException("OBJ contains no triangle geometry");
    return new MeshData(verts.toArray(new float[0][]),tris.toArray(new int[0][]),name);
  }
  /** Fail closed on oversize files, including streams without known lengths. */
  private static final class BoundedInputStream extends FilterInputStream{
    long remaining;
    BoundedInputStream(InputStream in,long cap){super(in);remaining=cap;}
    @Override public int read()throws IOException{
      int x=super.read();if(x>=0&&--remaining<0)throw new IOException("OBJ over 8 MB");return x;
    }
    @Override public int read(byte[] b,int off,int len)throws IOException{
      int n=super.read(b,off,len);
      if(n>0&&(remaining-=n)<0)throw new IOException("OBJ over 8 MB");
      return n;
    }
  }
}