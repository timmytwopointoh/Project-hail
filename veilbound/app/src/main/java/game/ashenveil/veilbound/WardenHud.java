package game.ashenveil.veilbound;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Shader;
import android.util.Log;
import android.view.MotionEvent;
import android.view.View;

/** Native Canvas HUD, dialogue and multitouch controls above native OpenGL 3D. */
public final class WardenHud extends View {
    private final WorldState game;
    private final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF rect=new RectF();
    private int joystickPointer=-1,cameraPointer=-1;
    private float stickX=0,stickY=0,prevCamX=0;
    private long lastDiagnostic=0;
    private float paintAlpha=1;
    private static final int GOLD=Color.rgb(229,192,139);
    private static final int PALE=Color.rgb(221,231,225);
    private static final int MIST=Color.rgb(123,166,167);
    private static final int EMBER=Color.rgb(246,138,70);
    private final float[] lastCamera={0};

    public WardenHud(Context context,WorldState state){
        super(context);game=state;setLayerType(View.LAYER_TYPE_SOFTWARE,null);
        setFocusable(true);setContentDescription("Veilbound native touch controls");
    }
    private void fill(Canvas canvas,int color,float alpha){
        p.reset();p.setAntiAlias(true);p.setColor(color);
        p.setAlpha((int)(255*Math.max(0,Math.min(1,alpha))));
        p.setStyle(Paint.Style.FILL);
    }
    private void text(Canvas c,String value,float x,float y,float size,int color,boolean bold,boolean centered){
        fill(c,color,1);p.setTypeface(bold?android.graphics.Typeface.create("serif",1):
                       android.graphics.Typeface.create("sans-serif",0));
        p.setTextSize(size);
        if(centered)p.setTextAlign(Paint.Align.CENTER);
        p.setShadowLayer(bold?9:2,0,1,Color.argb(115,0,0,0));
        c.drawText(value,x,y,p);p.clearShadowLayer();
    }
    private void thinLine(Canvas c,float x,float y,float toX,float toY,int color,float alpha,float width){
        fill(c,color,alpha);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(width);c.drawLine(x,y,toX,toY,p);
    }
    private void pane(Canvas c,float left,float top,float right,float bottom,float radius){
        fill(c,Color.rgb(11,17,22),.83f);
        rect.set(left,top,right,bottom);c.drawRoundRect(rect,radius,radius,p);
        fill(c,GOLD,.42f);p.setStrokeWidth(1.3f);p.setStyle(Paint.Style.STROKE);
        c.drawRoundRect(rect,radius,radius,p);
        thinLine(c,left+15,top+2,right-15,top+2,GOLD,.55f,1);
    }
    private void bar(Canvas c,float x,float y,float w,float value,int color){
        fill(c,Color.BLACK,.53f);rect.set(x,y,x+w,y+9);c.drawRoundRect(rect,3,3,p);
        fill(c,color,.88f);rect.set(x,y,x+w*Math.max(0,Math.min(1,value)),y+9);
        c.drawRoundRect(rect,3,3,p);
        fill(c,PALE,.28f);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(.8f);
        rect.set(x,y,x+w,y+9);c.drawRoundRect(rect,3,3,p);
    }
    private void control(Canvas c,float x,float y,float r,String glyph,String label,int tint){
        fill(c,Color.rgb(9,17,23),.67f);
        c.drawCircle(x,y,r,p);
        fill(c,tint,.65f);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.8f);
        c.drawCircle(x,y,r,p);c.drawCircle(x,y,r-6,p);
        text(c,glyph,x,y+8,r*.68f,PALE,true,true);
        text(c,label,x,y+r+15,11,MIST,true,true);
    }
    private void frame(Canvas c,float left,float top,float right,float bottom){
        float k=20;
        thinLine(c,left,top,left+k,top,GOLD,.9f,2);
        thinLine(c,left,top,left,top+k,GOLD,.9f,2);
        thinLine(c,right-k,top,right,top,GOLD,.9f,2);
        thinLine(c,right,top,right,top+k,GOLD,.9f,2);
        thinLine(c,left,bottom-k,left,bottom,GOLD,.9f,2);
        thinLine(c,left,bottom,left+k,bottom,GOLD,.9f,2);
        thinLine(c,right-k,bottom,right,bottom,GOLD,.9f,2);
        thinLine(c,right,bottom-k,right,bottom,GOLD,.9f,2);
    }
    @Override protected void onDraw(Canvas canvas){
        super.onDraw(canvas);
        float sx=getWidth()/1000f,sy=getHeight()/600f;
        if(sx<=0||sy<=0)return;
        canvas.save();canvas.scale(sx,sy);
        WorldState.Snapshot s=game.snapshot();
        if(s.mode.equals("title"))drawTitle(canvas);
        else if(s.mode.equals("story"))drawStory(canvas);
        else if(s.mode.equals("dead"))drawEnd(canvas,false);
        else if(s.mode.equals("victory"))drawEnd(canvas,true);
        else drawGameplay(canvas,s);
        canvas.restore();
        long now=System.currentTimeMillis();
        if(now-lastDiagnostic>1400){
            lastDiagnostic=now;
            Log.i("VEILBOUND_STATE","mode="+s.mode+" hp="+s.health+
                  " stamina="+s.stamina+" sigils="+s.fragments+
                  " enemies="+s.foes+" x="+(int)s.x+" z="+(int)s.z);
        }
        postInvalidateDelayed(32);
    }
    private void drawTitle(Canvas c){
        fill(c,Color.rgb(2,7,12),.58f);c.drawRect(0,0,1000,600,p);
        pane(c,220,76,780,524,10);frame(c,228,83,772,518);
        text(c,"AN ORIGINAL DARK FANTASY TALE",500,134,15,MIST,false,true);
        thinLine(c,310,159,690,159,GOLD,.5f,1.3f);
        text(c,"VEILBOUND",500,253,75,GOLD,true,true);
        text(c,"ASH OF THE BELLS",500,307,25,PALE,true,true);
        text(c,"WHEN THE SEVENTH BELL FELL SILENT",500,352,16,MIST,false,true);
        text(c,"THE DEAD BEGAN TO REMEMBER",500,378,16,MIST,false,true);
        fill(c,EMBER,.17f);rect.set(349,419,651,480);c.drawRoundRect(rect,7,7,p);
        fill(c,GOLD,1);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.4f);
        c.drawRoundRect(rect,7,7,p);
        text(c,"BEGIN THE PILGRIMAGE",500,456,21,PALE,true,true);
        text(c,"NATIVE 3D PROLOGUE  •  OFFLINE",500,506,11,MIST,false,true);
    }
    private void drawStory(Canvas c){
        fill(c,Color.rgb(2,7,12),.69f);c.drawRect(0,0,1000,600,p);
        pane(c,200,95,800,510,11);
        text(c,"PROLOGUE — THE UNSUNG BELL",500,146,18,GOLD,true,true);
        thinLine(c,265,170,735,170,GOLD,.42f,1);
        text(c,"Six bells have gone silent.",500,231,27,PALE,true,true);
        text(c,"Only one still remembers your name.",500,275,25,PALE,false,true);
        text(c,"You are the final Bellwarden.",500,326,20,MIST,false,true);
        text(c,"Find the last ember beneath Mourning Vale.",500,359,20,MIST,false,true);
        text(c,"But beware what the ward bells were made to hide.",500,392,17,MIST,false,true);
        text(c,"TOUCH TO ENTER THE VALE",500,470,18,GOLD,true,true);
    }
    private void drawEnd(Canvas c,boolean victory){
        fill(c,Color.rgb(4,7,11),.70f);c.drawRect(0,0,1000,600,p);
        pane(c,220,110,780,502,10);
        text(c,victory?"THE FIRST BELL WAKES":"THE EMBER REMAINS",
                500,209,45,victory?GOLD:PALE,true,true);
        text(c,victory?"We were never keeping the darkness out.":
                       "Death is not the end of your vow.",500,270,22,MIST,false,true);
        text(c,victory?"The true pilgrimage has just begun.":
                      "Rise at the last ember and try again.",500,315,18,MIST,false,true);
        text(c,victory?"RETURN TO TITLE":"RISE AGAIN",500,424,23,GOLD,true,true);
    }
    private void drawGameplay(Canvas c,WorldState.Snapshot s){
        pane(c,20,18,350,110,6);
        text(c,"THE LAST BELLWARDEN",38,40,17,GOLD,true,false);
        text(c,"LIFE",39,65,12,PALE,true,false);
        bar(c,94,54,235,s.health/100f,Color.rgb(176,57,56));
        text(c,"VIGOR",39,91,12,MIST,true,false);
        bar(c,94,80,235,s.stamina/100f,Color.rgb(125,178,139));
        pane(c,582,18,982,91,6);
        text(c,"MOURNING VALE   •   CHAPTER I",602,42,15,GOLD,true,false);
        text(c,s.objective,602,75,15,PALE,false,false);
        if(s.bossAlive&&s.z>46){
            text(c,"ASH KNIGHT",500,42,18,PALE,true,true);
            bar(c,403,56,194,s.bossHealth/260f,EMBER);
        }
        if(!s.message.isEmpty()){
            pane(c,241,115,759,175,5);
            text(c,s.message.length()>54?s.message.substring(0,54):s.message,
                    500,151,15,GOLD,true,true);
        }
        fill(c,PALE,.28f);p.setStrokeWidth(.9f);p.setStyle(Paint.Style.STROKE);
        c.drawCircle(500,300,7,p);c.drawLine(486,300,493,300,p);c.drawLine(507,300,514,300,p);
        // Left thumb movement zone.
        fill(c,Color.rgb(5,15,20),.49f);c.drawCircle(123,487,83,p);
        fill(c,MIST,.51f);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(2.1f);
        c.drawCircle(123,487,82,p);
        fill(c,PALE,.22f);c.drawCircle(123+stickX*48,487+stickY*48,34,p);
        fill(c,PALE,.45f);p.setStyle(Paint.Style.STROKE);
        c.drawCircle(123+stickX*48,487+stickY*48,34,p);
        text(c,"MOVE",123,586,11,MIST,true,true);
        control(c,905,484,51,"✦","ATTACK",GOLD);
        control(c,806,520,41,"↝","DODGE",MIST);
        control(c,908,365,33,"✧","INTERACT",EMBER);
        text(c,"DRAG RIGHT SIDE TO ORBIT CAMERA",500,582,11,MIST,false,true);
    }
    private float normX(float raw){return raw*1000f/Math.max(1,getWidth());}
    private float normY(float raw){return raw*600f/Math.max(1,getHeight());}
    private static boolean near(float x,float y,float bx,float by,float radius){
        return (x-bx)*(x-bx)+(y-by)*(y-by)<radius*radius;
    }
    @Override public boolean onTouchEvent(MotionEvent event){
        int index=event.getActionIndex(),action=event.getActionMasked();
        if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){
            float x=normX(event.getX(index)),y=normY(event.getY(index));
            WorldState.Snapshot s=game.snapshot();
            if(!s.mode.equals("playing")){
                game.start();invalidate();return true;
            }
            if(s.dialogue&&x>230&&x<780&&y<185){game.dismissStory();return true;}
            if(near(x,y,905,484,76)){game.attack();return true;}
            if(near(x,y,806,520,65)){game.roll();return true;}
            if(near(x,y,908,365,60)){game.interact();return true;}
            if(x<340&&joystickPointer<0){
                joystickPointer=event.getPointerId(index);updateStick(x,y);return true;
            }
            if(cameraPointer<0){
                cameraPointer=event.getPointerId(index);
                prevCamX=x;return true;
            }
        }else if(action==MotionEvent.ACTION_MOVE){
            for(int i=0;i<event.getPointerCount();i++){
                int id=event.getPointerId(i);
                float x=normX(event.getX(i)),y=normY(event.getY(i));
                if(id==joystickPointer)updateStick(x,y);
                else if(id==cameraPointer){
                    game.orbit((x-prevCamX)*.006f);prevCamX=x;
                }
            }
        }else if(action==MotionEvent.ACTION_POINTER_UP||action==MotionEvent.ACTION_UP||
                 action==MotionEvent.ACTION_CANCEL){
            int id=event.getPointerId(index);
            if(id==joystickPointer){joystickPointer=-1;stickX=0;stickY=0;game.movement(0,0);}
            if(id==cameraPointer)cameraPointer=-1;
            if(action==MotionEvent.ACTION_CANCEL||action==MotionEvent.ACTION_UP){
                joystickPointer=-1;cameraPointer=-1;stickX=0;stickY=0;game.movement(0,0);
            }
        }
        return true;
    }
    private void updateStick(float x,float y){
        float dx=(x-123)/80f,dy=(y-487)/80f;
        float n=(float)Math.hypot(dx,dy);
        if(n>1){dx/=n;dy/=n;}
        stickX=dx;stickY=dy;game.movement(dx,-dy);
        invalidate();
    }
}