package com.trioncompasitor.vqstudio;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * FORGE/1 is a bounded, human-readable construction language, NOT an asset set.
 * Every vertex is generated from dimensions; no premade OBJ or template models.
 *
 * FORGE/1
 * model clockwork_fox
 * part body ellipsoid 0 1 0 1.4 .7 .55
 * part left_ear taper -.43 1.7 0 .27 .54 .22
 * part right_ear taper .43 1.7 0 .27 .54 .22
 * part leg_l cylinder -.45 .48 0 .25 .94 .25
 * part leg_r cylinder .45 .48 0 .25 .94 .25
 *
 * Units are meters, Y-up. A part has named identity, type, center and bounds.
 * Rigging, physics and photorealism are separate downstream gates.
 */
public final class ForgeSpec {
  public static final int MAX_PARTS=64;
  public static final int MAX_TRIANGLES=25000;
  private ForgeSpec(){}
  public static final class Part {
    public final String name,type;
    public final float x,y,z,w,h,d;
    Part(String name,String type,float x,float y,float z,float w,float h,float d){
      this.name=name;this.type=type;this.x=x;this.y=y;this.z=z;this.w=w;this.h=h;this.d=d;
    }
  }
  public static final class Blueprint {
    public final String title;
    public final List<Part> parts;
    public final String explanation;
    Blueprint(String title,List<Part> parts,String explanation){
      this.title=title;this.parts=Collections.unmodifiableList(parts);this.explanation=explanation;
    }
    public String serialize(){
      StringBuilder b=new StringBuilder("FORGE/1\nmodel ").append(title).append('\n');
      for(Part p:parts)b.append(String.format(Locale.ROOT,
        "part %s %s %.4f %.4f %.4f %.4f %.4f %.4f\n",
        p.name,p.type,p.x,p.y,p.z,p.w,p.h,p.d));
      return b.toString();
    }
  }
  private static float valid(String s){
    float f=Float.parseFloat(s);
    if(!Float.isFinite(f)||Math.abs(f)>100)throw new IllegalArgumentException("Non-finite or unbounded geometry");
    return f;
  }
  private static Part part(String id,String type,float x,float y,float z,float w,float h,float d){
    if(!id.matches("[a-zA-Z][a-zA-Z0-9_]{0,39}"))
      throw new IllegalArgumentException("Use named geometry parts, not arbitrary code");
    if(!Arrays.asList("box","ellipsoid","taper","cylinder","capsule","ring").contains(type))
      throw new IllegalArgumentException("Unsupported geometric tool: "+type);
    if(w<=.005f||h<=.005f||d<=.005f||w>30||h>30||d>30)
      throw new IllegalArgumentException("Every part needs positive bounded dimensions");
    if(Math.abs(x)>50||Math.abs(y)>50||Math.abs(z)>50)
      throw new IllegalArgumentException("Part center exceeds build space");
    return new Part(id,type,x,y,z,w,h,d);
  }
  public static Blueprint parse(String text){
    if(text==null||text.length()>5000||!text.startsWith("FORGE/1\n"))
      throw new IllegalArgumentException("Expected FORGE/1 construction plan");
    String title="untitled";ArrayList<Part> parts=new ArrayList<>();Set<String> names=new HashSet<>();
    String[] lines=text.split("\\r?\\n");
    for(int i=1;i<lines.length;i++){
      String line=lines[i].trim();
      if(line.isEmpty()||line.startsWith("#"))continue;
      String[] p=line.split("\\s+");
      if("model".equals(p[0])&&p.length==2&&p[1].matches("[a-zA-Z][a-zA-Z0-9_]{0,39}")){
        title=p[1];continue;
      }
      if(!"part".equals(p[0])||p.length!=9)
        throw new IllegalArgumentException("Line "+(i+1)+": expected part NAME TYPE X Y Z WIDTH HEIGHT DEPTH");
      if(parts.size()>=MAX_PARTS)throw new IllegalArgumentException("Too many structural parts");
      if(!names.add(p[1]))throw new IllegalArgumentException("Duplicate part name: "+p[1]);
      parts.add(part(p[1],p[2],valid(p[3]),valid(p[4]),valid(p[5]),
          valid(p[6]),valid(p[7]),valid(p[8])));
    }
    if(parts.isEmpty())throw new IllegalArgumentException("Describe at least one geometric part");
    return new Blueprint(title,parts,"Explicit dimensional construction plan; geometry generated locally");
  }
  private static void add(ArrayList<Part> p,String n,String t,float x,float y,float z,float w,float h,float d){
    p.add(part(n,t,x,y,z,w,h,d));
  }
  /** Conservative offline natural-language planning: supported mechanical
   * families can vary dimensions, count and proportion; unrecognized concepts
   * are rejected instead of producing a misleading 'generic' object.
   */
  public static Blueprint compile(String request){
    if(request==null||request.trim().isEmpty()||request.length()>5000)
      throw new IllegalArgumentException("Describe a model or provide a FORGE/1 plan");
    if(request.startsWith("FORGE/1\n"))return parse(request);
    if(request.startsWith("FORGE/2\n"))return ForgeLang2.parse(request);
    if(ForgeLang2.isExpandedFamily(request))return ForgeLang2.compile(request);
    String s=request.toLowerCase(Locale.ROOT);
    ArrayList<Part> p=new ArrayList<>();
    float scale=s.matches("(?s).*\\b(tiny|miniature|small)\\b.*")?.7f:
      s.matches("(?s).*\\b(huge|giant|large)\\b.*")?1.4f:1f;
    boolean longish=s.matches("(?s).*\\b(tall|long|elongated)\\b.*");
    boolean wide=s.matches("(?s).*\\b(wide|broad|thick)\\b.*");
    String title;
    if(s.matches("(?s).*\\b(tree|oak|pine|forest)\\b.*")){
      title="procedural_tree";
      float height=(longish?2.8f:2.0f)*scale, width=(wide?1.8f:1.1f)*scale;
      add(p,"trunk","cylinder",0,height*.36f,0,.23f*scale,height*.72f,.23f*scale);
      add(p,"crown","ellipsoid",0,height*.84f,0,width,height*.7f,width);
      if(s.contains("branch")||s.contains("ancient")||s.contains("old")){
        add(p,"branch_left","taper",-width*.40f,height*.69f,0,width*.90f,.19f*scale,.22f*scale);
        add(p,"branch_right","taper",width*.4f,height*.75f,0,width*.90f,.16f*scale,.22f*scale);
      }
    }else if(s.matches("(?s).*\\b(sword|blade|dagger)\\b.*")){
      title="procedural_blade";float h=(longish?2.4f:1.7f)*scale;
      add(p,"handle","cylinder",0,.25f*scale,0,.15f*scale,.50f*scale,.15f*scale);
      add(p,"guard","box",0,.53f*scale,0,(wide?1.1f:.7f)*scale,.12f*scale,.18f*scale);
      add(p,"blade","taper",0,.55f*scale+h*.5f,0,.23f*scale,h,.09f*scale);
    }else if(s.matches("(?s).*\\b(chest|crate|box|container)\\b.*")){
      title="procedural_container";
      float width=(wide?2.4f:1.6f)*scale;
      add(p,"body","box",0,.52f*scale,0,width,1.0f*scale,1.0f*scale);
      add(p,"lid","box",0,1.12f*scale,0,width*1.05f,.2f*scale,1.1f*scale);
      add(p,"lock","box",0,.72f*scale,.53f*scale,.2f*scale,.24f*scale,.09f*scale);
    }else if(s.matches("(?s).*\\b(hill|terrain|ground|mountain|landscape)\\b.*")){
      title="procedural_landform";
      float spread=(wide?5.5f:3.2f)*scale;
      add(p,"ground","box",0,-.16f*scale,0,spread,.30f*scale,spread);
      add(p,"mound","ellipsoid",0,.20f*scale,0,spread*.72f,(longish?2.3f:1.3f)*scale,spread*.72f);
    }else{
      throw new IllegalArgumentException("No matching geometric construction rules yet. Describe basic shapes with FORGE/1 part commands; a new object family requires a planner/tool implementation, not a copied asset.");
    }
    return new Blueprint(title,p,"Constructed with "+p.size()+" named parts; scale="+scale+"; no prefabricated meshes");
  }
  /** Reapply previously VERIFIED geometric strategy to a new dimensional
   * request. It re-generates all vertices; no old OBJ is ever loaded or copied.
   * Only transformations that this compiler can actually satisfy are accepted.
   */
  public static Blueprint adapt(Blueprint previous,String direction){
    if(previous==null||direction==null)throw new IllegalArgumentException("No verified past plan");
    String s=direction.toLowerCase(Locale.ROOT);
    float size=s.contains("smaller")||s.contains("miniature")?.75f:
      s.contains("larger")||s.contains("bigger")||s.contains("giant")?1.3f:1f;
    float tall=s.contains("taller")||s.contains("higher")?1.25f:
      s.contains("shorter")?.80f:1f;
    float wide=s.contains("wider")||s.contains("broader")?1.25f:
      s.contains("narrower")?.80f:1f;
    if(size==1f&&tall==1f&&wide==1f)
      throw new IllegalArgumentException("Say larger, smaller, taller, shorter, wider or narrower when reusing the last verified geometry technique");
    ArrayList<Part> rebuilt=new ArrayList<>();
    for(Part p:previous.parts)rebuilt.add(part(p.name,p.type,
      p.x*size*wide,p.y*size*tall,p.z*size*wide,
      p.w*size*wide,p.h*size*tall,p.d*size*wide));
    return new Blueprint(previous.title,rebuilt,
      "Reused verified proportional construction strategy; regenerated every triangle");
  }
  private static final class Mesh {
    final StringBuilder out=new StringBuilder("# FORGE/1 original procedural OBJ\n");
    int vertices=0,triangles=0;
    int vertex(float x,float y,float z){
      if(++vertices>MAX_TRIANGLES*3)throw new IllegalArgumentException("Vertex budget exceeded");
      out.append(String.format(Locale.ROOT,"v %.5f %.5f %.5f\n",x,y,z));return vertices;
    }
    void tri(int a,int b,int c){
      if(++triangles>MAX_TRIANGLES)throw new IllegalArgumentException("Triangle budget exceeded");
      if(a==b||b==c||a==c)throw new IllegalArgumentException("Degenerate face indices");
      out.append("f ").append(a).append(' ').append(b).append(' ').append(c).append('\n');
    }
    void make(Part p,int revision){
      out.append("g ").append(p.name).append('\n');
      if(p.type.equals("box")){box(p);return;}
      if(p.type.equals("ring")){ring(p,revision);return;}
      int segments=revision==1?10:20,rings=revision==1?6:12;
      int[][] grid=new int[rings+1][segments];
      for(int j=0;j<=rings;j++){
        float phi=(float)((j+.0001)*Math.PI/(rings+.0002));
        for(int k=0;k<segments;k++){
          double a=2*Math.PI*k/segments;float x,y,z;
          if(p.type.equals("ellipsoid")){
            x=p.x+(float)Math.sin(phi)*(float)Math.cos(a)*p.w*.5f;
            y=p.y+(float)Math.cos(phi)*p.h*.5f;
            z=p.z+(float)Math.sin(phi)*(float)Math.sin(a)*p.d*.5f;
          }else{
            float f=j/(float)rings;float radius=p.type.equals("taper")?(.85f-.79f*f):1f;
            if(p.type.equals("capsule")){
              float cap=Math.min(p.h*.48f,Math.min(p.w,p.d)*.5f);
              float inset=Math.min(f*p.h,(1-f)*p.h);
              if(inset<cap){float t=(cap-inset)/cap;radius=(float)Math.sqrt(Math.max(.00001f,1f-t*t));}
            }
            x=p.x+(float)Math.cos(a)*p.w*.5f*radius;
            y=p.y-p.h*.5f+f*p.h;
            z=p.z+(float)Math.sin(a)*p.d*.5f*radius;
          }
          grid[j][k]=vertex(x,y,z);
        }
      }
      for(int j=0;j<rings;j++)for(int k=0;k<segments;k++){
        int n=(k+1)%segments;
        tri(grid[j][k],grid[j+1][k],grid[j+1][n]);
        tri(grid[j][k],grid[j+1][n],grid[j][n]);
      }
    }
    /** True parametric torus, not a reused wheel or image asset. */
    void ring(Part p,int revision){
      int around=revision==1?16:32,across=revision==1?6:10;
      float tube=Math.min(p.h*.5f,Math.min(p.w,p.d)*.24f);
      float rx=p.w*.5f-tube,rz=p.d*.5f-tube;
      if(rx<=.005f||rz<=.005f)throw new IllegalArgumentException("Ring requires space around its center hole");
      int[][] v=new int[around][across];
      for(int i=0;i<around;i++){
        double a=2*Math.PI*i/around;
        for(int j=0;j<across;j++){
          double t=2*Math.PI*j/across;
          float x=p.x+(rx+tube*(float)Math.cos(t))*(float)Math.cos(a);
          float y=p.y+tube*(float)Math.sin(t);
          float z=p.z+(rz+tube*(float)Math.cos(t))*(float)Math.sin(a);
          v[i][j]=vertex(x,y,z);
        }
      }
      for(int i=0;i<around;i++)for(int j=0;j<across;j++){
        int ni=(i+1)%around,nj=(j+1)%across;
        tri(v[i][j],v[ni][j],v[ni][nj]);
        tri(v[i][j],v[ni][nj],v[i][nj]);
      }
    }
    void box(Part p){
      int[] v=new int[8];int i=0;
      for(int z=-1;z<=1;z+=2)for(int y=-1;y<=1;y+=2)for(int x=-1;x<=1;x+=2)
        v[i++]=vertex(p.x+x*p.w*.5f,p.y+y*p.h*.5f,p.z+z*p.d*.5f);
      int[][] f={{0,1,3},{0,3,2},{4,7,5},{4,6,7},{0,4,5},{0,5,1},
        {2,3,7},{2,7,6},{0,2,6},{0,6,4},{1,5,7},{1,7,3}};
      for(int[] t:f)tri(v[t[0]],v[t[1]],v[t[2]]);
    }
  }
  public static byte[] build(Blueprint b,int revision,OfflineGeometry.BooleanSupplier cancel){
    if(revision!=1&&revision!=2)throw new IllegalArgumentException("Revision must be 1 or 2");
    Mesh mesh=new Mesh();
    for(Part p:b.parts){
      if(cancel.cancelled())throw new IllegalStateException("Stopped at geometry checkpoint");
      mesh.make(p,revision);
    }
    if(mesh.triangles==0)throw new IllegalArgumentException("Empty geometry");
    byte[] obj=mesh.out.toString().getBytes(StandardCharsets.UTF_8);
    if(obj.length>8*1024*1024)throw new IllegalArgumentException("OBJ exceeds safe local size");
    return obj;
  }
}