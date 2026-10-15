package game.ashenveil.veilbound;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Android-independent OBJ mesh importer for the 3D Model Atelier.
 * Supports triangular/quadrilateral/n-gon faces, positive/negative indices,
 * optionally-authored vertex normals, embedded RGB vertex colours, comments.
 *
 * Streams text instead of reading all file bytes. Floats are interleaved as
 * the renderer expects: position XYZ / normalized normal XYZ / color RGB.
 * Model is centered horizontally, grounded and normalized to a 3.3 unit
 * longest dimension for camera framing. Materials/textures are not yet
 * interpreted; OBJ MTL/UV support is a future render-material milestone.
 */
public final class ObjMeshLoader {
    private ObjMeshLoader(){}
    private static final class Floats {
        float[] data=new float[8192];
        int count;
        void add(float x){if(count==data.length)data=Arrays.copyOf(data,data.length*2);data[count++]=x;}
        float get(int index){return data[index];}
        int size(){return count;}
        float[] array(){return Arrays.copyOf(data,count);}
    }
    private static final class FaceVertex {
        final int pos,norm;
        FaceVertex(int p,int n){pos=p;norm=n;}
    }
    private static int index(String raw,int size){
        if(raw==null||raw.length()==0)return -1;
        int n=Integer.parseInt(raw);
        int id=n>0?n-1:size+n;
        if(id<0||id>=size)throw new IllegalArgumentException("Invalid OBJ index "+raw);
        return id;
    }
    private static float parse(String x){float f=Float.parseFloat(x);if(!Float.isFinite(f))throw new IllegalArgumentException("Non-finite OBJ vertex");return f;}
    private static float clamp(float x){return Math.max(0f,Math.min(1.4f,x));}
    private static float unitColor(String raw){
        float f=parse(raw);
        return clamp(f>1.5f?f/255f:f);
    }
    private static void addVertex(Floats output,Floats positions,Floats normals,
                                  Floats colors,FaceVertex v,
                                  float nx,float ny,float nz){
        int p=v.pos*3;
        output.add(positions.get(p));output.add(positions.get(p+1));output.add(positions.get(p+2));
        if(v.norm>=0){
            int at=v.norm*3;
            nx=normals.get(at);ny=normals.get(at+1);nz=normals.get(at+2);
            float length=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(length>.0001f){nx/=length;ny/=length;nz/=length;}
        }
        output.add(nx);output.add(ny);output.add(nz);
        int at=v.pos*3;
        output.add(colors.get(at));output.add(colors.get(at+1));output.add(colors.get(at+2));
    }
    private static FaceVertex parseFace(String raw,int pCount,int nCount){
        String[] t=raw.split("/",-1);
        int p=index(t[0],pCount);
        int n=t.length>2&&t[2].length()>0?index(t[2],nCount):-1;
        return new FaceVertex(p,n);
    }
    public static ArtKit.Model load(InputStream in)throws IOException{
        return load(new InputStreamReader(in,StandardCharsets.UTF_8));
    }
    public static ArtKit.Model load(Reader input)throws IOException{
        Floats positions=new Floats(),normals=new Floats(),colors=new Floats(),vertices=new Floats();
        int faces=0,lines=0;
        try(BufferedReader reader=new BufferedReader(input,65536)){
            String line;
            while((line=reader.readLine())!=null){
                lines++;
                line=line.trim();
                if(line.isEmpty()||line.charAt(0)=='#')continue;
                int space=line.indexOf(' ');
                if(space<0)continue;
                String op=line.substring(0,space);
                if(!"v".equals(op)&&!"vn".equals(op)&&!"f".equals(op))continue;
                String[] t=line.substring(space+1).trim().split("\\s+");
                if("v".equals(op)){
                    if(t.length<3)throw new IOException("Incomplete vertex at line "+lines);
                    for(int i=0;i<3;i++)positions.add(parse(t[i]));
                    if(t.length>=6){
                        for(int i=3;i<6;i++)colors.add(unitColor(t[i]));
                    }else{
                        colors.add(.62f);colors.add(.66f);colors.add(.70f);
                    }
                }else if("vn".equals(op)){
                    if(t.length<3)throw new IOException("Incomplete normal at "+lines);
                    for(int i=0;i<3;i++)normals.add(parse(t[i]));
                }else{
                    if(t.length<3)continue;
                    int pCount=positions.size()/3,nCount=normals.size()/3;
                    List<FaceVertex> polygon=new ArrayList<>(t.length);
                    for(String part:t){if(part.charAt(0)=='#')break;polygon.add(parseFace(part,pCount,nCount));}
                    if(polygon.size()<3)continue;
                    for(int k=1;k<polygon.size()-1;k++){
                        FaceVertex a=polygon.get(0),b=polygon.get(k),c=polygon.get(k+1);
                        float ax=positions.get(a.pos*3),ay=positions.get(a.pos*3+1),az=positions.get(a.pos*3+2);
                        float bx=positions.get(b.pos*3),by=positions.get(b.pos*3+1),bz=positions.get(b.pos*3+2);
                        float cx=positions.get(c.pos*3),cy=positions.get(c.pos*3+1),cz=positions.get(c.pos*3+2);
                        float ux=bx-ax,uy=by-ay,uz=bz-az;
                        float vx=cx-ax,vy=cy-ay,vz=cz-az;
                        float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
                        float len=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
                        if(len<1e-9f)continue;
                        nx/=len;ny/=len;nz/=len;
                        addVertex(vertices,positions,normals,colors,a,nx,ny,nz);
                        addVertex(vertices,positions,normals,colors,b,nx,ny,nz);
                        addVertex(vertices,positions,normals,colors,c,nx,ny,nz);
                        faces++;
                    }
                }
            }
        }catch(IllegalArgumentException e){
            throw new IOException("Invalid OBJ data at line "+lines+": "+e.getMessage(),e);
        }
        if(faces==0)throw new IOException("OBJ file contains no valid polygon faces");
        float[] output=vertices.array();
        float lowX=Float.MAX_VALUE,lowY=Float.MAX_VALUE,lowZ=Float.MAX_VALUE;
        float hiX=-Float.MAX_VALUE,hiY=-Float.MAX_VALUE,hiZ=-Float.MAX_VALUE;
        for(int p=0;p<output.length;p+=9){
            lowX=Math.min(lowX,output[p]);hiX=Math.max(hiX,output[p]);
            lowY=Math.min(lowY,output[p+1]);hiY=Math.max(hiY,output[p+1]);
            lowZ=Math.min(lowZ,output[p+2]);hiZ=Math.max(hiZ,output[p+2]);
        }
        float span=Math.max(.00001f,Math.max(hiX-lowX,Math.max(hiY-lowY,hiZ-lowZ)));
        float scale=3.30f/span,centX=(lowX+hiX)*.5f,centZ=(lowZ+hiZ)*.5f;
        for(int p=0;p<output.length;p+=9){
            output[p]=(output[p]-centX)*scale;
            output[p+1]=(output[p+1]-lowY)*scale;
            output[p+2]=(output[p+2]-centZ)*scale;
        }
        return new ArtKit.Model(output);
    }
}
