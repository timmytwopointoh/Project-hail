package com.trioncompasitor.vqstudio;

import android.content.Context;
import android.graphics.*;
import android.view.*;
import android.os.SystemClock;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;

/** A real, orbitable geometry viewport—not a video feed or a fake new mesh. */
public final class ModelViewport extends View {
  private final Paint paint=new Paint(3);
  private MeshData mesh=MeshData.sample();
  private float yaw=.7f,pitch=.24f,zoom=1f;
  private float lastX,lastY;
  private boolean wire=true,spin=true;
  private long lastFrame=SystemClock.uptimeMillis();
  private static final class Face {
    final float depth;
    final Path path;
    final int fill;
    Face(float depth,Path path,int fill){this.depth=depth;this.path=path;this.fill=fill;}
  }
  public ModelViewport(Context context){super(context);setLayerType(View.LAYER_TYPE_SOFTWARE,null);}
  public void setMesh(MeshData source){mesh=source;zoom=1f;invalidate();}
  /** Replace geometry but preserve user yaw, pitch, zoom, rotation and edge mode. */
  public void setMeshKeepingCamera(MeshData source){
    if(source==null||source.triangles.length==0)throw new IllegalArgumentException("Empty model revision");
    mesh=source;
    invalidate();
  }
  public String meshName(){return mesh.label;}
  /** Test the exact camera and effect values before/after a source revision. */
  public String cameraFingerprint(){
    return Float.floatToIntBits(yaw)+":"+Float.floatToIntBits(pitch)+":"+
           Float.floatToIntBits(zoom)+":"+wire+":"+spin;
  }
  public void toggleWire(){wire=!wire;invalidate();}
  public void toggleOrbit(){spin=!spin;invalidate();}
  @Override protected void onDraw(Canvas canvas){
    super.onDraw(canvas);
    int width=getWidth(),height=getHeight();
    canvas.drawColor(Color.BLACK);
    paint.setShader(new RadialGradient(width*.5f,height*.48f,Math.max(width,height)*.65f,
        new int[]{Color.rgb(12,29,42),Color.rgb(4,9,15),Color.BLACK},
        null,Shader.TileMode.CLAMP));
    canvas.drawRect(0,0,width,height,paint);paint.setShader(null);
    MeshData data=mesh;
    if(data==null||data.vertices.length==0)return;
    long now=SystemClock.uptimeMillis(), elapsed=Math.max(0,Math.min(50,now-lastFrame));
    lastFrame=now;
    if(spin)yaw+=(elapsed/1000f)*.22f;
    float[][] vertices=data.vertices;
    float[] min={Float.MAX_VALUE,Float.MAX_VALUE,Float.MAX_VALUE};
    float[] max={-Float.MAX_VALUE,-Float.MAX_VALUE,-Float.MAX_VALUE};
    for(float[] p:vertices)for(int k=0;k<3;k++){
      min[k]=Math.min(min[k],p[k]);max[k]=Math.max(max[k],p[k]);
    }
    float[] center={(max[0]+min[0])*.5f,(max[1]+min[1])*.5f,(max[2]+min[2])*.5f};
    float size=Math.max(.0001f,Math.max(max[0]-min[0],Math.max(max[1]-min[1],max[2]-min[2])));
    float scale=(Math.min(width,height)*.66f/size)*zoom;
    float cy=(float)Math.cos(yaw),sy=(float)Math.sin(yaw);
    float cp=(float)Math.cos(pitch),sp=(float)Math.sin(pitch);
    float[][] projected=new float[vertices.length][3];
    for(int i=0;i<vertices.length;i++){
      float x=vertices[i][0]-center[0],y=vertices[i][1]-center[1],z=vertices[i][2]-center[2];
      float rx=cy*x+sy*z;
      float rz=-sy*x+cy*z;
      float ry=cp*y-sp*rz;
      float depth=sp*y+cp*rz;
      projected[i][0]=width*.5f+rx*scale;
      projected[i][1]=height*.48f-ry*scale;
      projected[i][2]=depth;
    }
    ArrayList<Face> faces=new ArrayList<>();
    int stride=Math.max(1,(int)Math.ceil(data.triangles.length/3500.0));
    for(int i=0;i<data.triangles.length;i+=stride){
      int[] t=data.triangles[i];
      float[] a=projected[t[0]],b=projected[t[1]],c=projected[t[2]];
      float ax=b[0]-a[0],ay=b[1]-a[1],bx=c[0]-a[0],by=c[1]-a[1];
      float signed=ax*by-ay*bx;
      float intensity=Math.min(1f,.35f+Math.abs(signed)/(scale*scale+1f)*.95f);
      int base= (int)(60+115*intensity);
      int color=Color.rgb(Math.min(220,base),Math.min(238,base+35),Math.min(255,base+48));
      Path path=new Path();path.moveTo(a[0],a[1]);path.lineTo(b[0],b[1]);path.lineTo(c[0],c[1]);path.close();
      faces.add(new Face((a[2]+b[2]+c[2])/3f,path,color));
    }
    Collections.sort(faces,Comparator.comparingDouble(f->f.depth));
    for(Face f:faces){
      paint.setColor(f.fill);paint.setStyle(Paint.Style.FILL);paint.setShader(null);canvas.drawPath(f.path,paint);
      if(wire){
        paint.setColor(Color.argb(82,20,255,206));
        paint.setStrokeWidth(Math.max(1f,width/700f));
        paint.setStyle(Paint.Style.STROKE);
        canvas.drawPath(f.path,paint);
      }
    }
    paint.setStyle(Paint.Style.FILL);paint.setShader(null);
    paint.setColor(Color.rgb(122,243,208));paint.setTextSize(Math.max(13,getResources().getDisplayMetrics().scaledDensity*12));
    canvas.drawText("VQ • 3D INSPECTION SPACE",18,28,paint);
    paint.setColor(Color.rgb(168,188,196));
    canvas.drawText(data.triangles.length+" triangles  •  drag to orbit  •  two fingers to zoom",18,height-21,paint);
    if(isAttachedToWindow()&&getVisibility()==VISIBLE&&spin)postInvalidateDelayed(50);
  }
  @Override public boolean onTouchEvent(android.view.MotionEvent e){
    switch(e.getActionMasked()){
      case MotionEvent.ACTION_DOWN:
        lastX=e.getX();lastY=e.getY();return true;
      case MotionEvent.ACTION_POINTER_DOWN:
        return true;
      case MotionEvent.ACTION_MOVE:
        if(e.getPointerCount()>=2){
          float dy=e.getY(1)-e.getY(0),dx=e.getX(1)-e.getX(0);
          float spacing=(float)Math.hypot(dx,dy);
          // A measured two-finger drag changes zoom in bounded increments.
          zoom=Math.max(.30f,Math.min(3.5f,zoom+(spacing-Math.min(getWidth(),getHeight())*.35f)*.000025f));
        }else{
          yaw+=(e.getX()-lastX)*.009f;
          pitch=Math.max(-1.25f,Math.min(1.25f,pitch+(e.getY()-lastY)*.009f));
          lastX=e.getX();lastY=e.getY();
        }
        invalidate();return true;
    }
    return true;
  }
}