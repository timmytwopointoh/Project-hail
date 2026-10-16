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
    private float labLastX=0,labLastY=0,labPinchDistance=0;
    private int labDragPointer=-1;
    private Runnable importAction;
    private long lastStudioDiagnosticUptime=0;
    private long lastDiagnostic=0;
    private float paintAlpha=1;
    private static final int GOLD=Color.rgb(229,192,139);
    private static final int PALE=Color.rgb(221,231,225);
    private static final int MIST=Color.rgb(123,166,167);
    private static final int EMBER=Color.rgb(246,138,70);
    private final float[] lastCamera={0};

    public void setImportAction(Runnable action){importAction=action;}
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
        p.setTextAlign(centered?Paint.Align.CENTER:Paint.Align.LEFT);
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
        if(s.mode.equals("lab"))drawModelAtelier(canvas);
        else if(s.mode.equals("title"))drawTitle(canvas);
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
                  " enemies="+s.foes+" lock="+s.targetIndex+" x="+(int)s.x+" z="+(int)s.z);
        }
        postInvalidateDelayed(32);
    }
    private void drawTitle(Canvas c){
        fill(c,Color.rgb(2,7,12),.58f);c.drawRect(0,0,1000,600,p);
        pane(c,220,62,780,541,10);frame(c,228,68,772,535);
        text(c,"AN ORIGINAL DARK FANTASY TALE",500,134,15,MIST,false,true);
        thinLine(c,310,159,690,159,GOLD,.5f,1.3f);
        text(c,"VEILBOUND",500,253,75,GOLD,true,true);
        text(c,"ASH OF THE BELLS",500,307,25,PALE,true,true);
        text(c,"WHEN THE SEVENTH BELL FELL SILENT",500,352,16,MIST,false,true);
        text(c,"THE DEAD BEGAN TO REMEMBER",500,378,16,MIST,false,true);
        fill(c,EMBER,.17f);rect.set(349,419,651,480);c.drawRoundRect(rect,7,7,p);
        fill(c,GOLD,1);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.4f);
        c.drawRoundRect(rect,7,7,p);
        text(c,"BEGIN THE PILGRIMAGE",500,448,21,PALE,true,true);
        fill(c,Color.rgb(14,26,31),.86f);
        rect.set(350,472,650,521);c.drawRoundRect(rect,7,7,p);
        fill(c,MIST,.83f);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.4f);
        c.drawRoundRect(rect,7,7,p);
        text(c,"OPEN THE MODEL ATELIER",500,503,16,GOLD,true,true);
        text(c,"NATIVE 3D PROLOGUE  •  OFFLINE",500,555,11,MIST,false,true);
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
        text(c,"THE LAST BELLWARDEN",39,40,16,GOLD,true,false);
        text(c,"LIFE",39,65,12,PALE,true,false);
        bar(c,94,54,235,s.health/100f,Color.rgb(176,57,56));
        text(c,"VIGOR",39,91,12,MIST,true,false);
        bar(c,94,80,235,s.stamina/100f,Color.rgb(125,178,139));
        pane(c,582,18,982,91,6);
        text(c,"MOURNING VALE  /  CHAPTER I",602,42,14,GOLD,true,false);
        text(c,s.objective.length()>36?s.objective.substring(0,36):s.objective,602,75,14,PALE,false,false);
        if(s.targetIndex>=0){
            text(c,"LOCKED  ·  "+s.targetName,500,107,14,GOLD,true,true);
        }
        if(s.bossAlive&&s.z>46){
            text(c,"ASH KNIGHT",500,42,18,PALE,true,true);
            bar(c,403,56,194,s.bossHealth/260f,EMBER);
        }
        if(!s.message.isEmpty()){
            pane(c,241,115,759,175,5);
            text(c,s.message.length()>54?s.message.substring(0,54):s.message,
                    500,151,15,GOLD,true,true);
        }
        // Subtle location compass and narrative chapter seal.
        fill(c,GOLD,.37f);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.3f);
        c.drawCircle(501,38,21,p);
        c.drawLine(501,12,501,20,p);c.drawLine(501,56,501,64,p);
        text(c,"N",501,43,14,GOLD,true,true);
        for(int i=0;i<5;i++){
            float x=379+i*60;
            thinLine(c,x,21,x,25,i==2?GOLD:MIST,i==2?.75f:.35f,1);
        }
        // Stronger vignette-like corner ornaments, without covering touch zones.
        thinLine(c,10,198,10,157,GOLD,.24f,1.4f);
        thinLine(c,10,198,29,198,GOLD,.24f,1.4f);
        thinLine(c,991,194,991,161,GOLD,.24f,1.4f);
        thinLine(c,991,194,972,194,GOLD,.24f,1.4f);
                fill(c,PALE,.28f);p.setStrokeWidth(.9f);p.setStyle(Paint.Style.STROKE);
        c.drawCircle(500,300,7,p);c.drawLine(486,300,493,300,p);c.drawLine(507,300,514,300,p);
        // Left thumb movement zone.
        fill(c,Color.rgb(5,15,20),.49f);c.drawCircle(123,487,83,p);
        fill(c,MIST,.51f);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(2.1f);
        c.drawCircle(123,487,82,p);
        fill(c,PALE,.22f);c.drawCircle(123+stickX*48,487+stickY*48,34,p);
        fill(c,PALE,.45f);p.setStyle(Paint.Style.STROKE);
        c.drawCircle(123+stickX*48,487+stickY*48,34,p);
        text(c,"MOVE",123,587,12,MIST,true,true);
        control(c,905,484,51,"✦","ATTACK",GOLD);
        control(c,806,520,41,"↝","DODGE",MIST);
        control(c,908,365,33,"✧","INTERACT",EMBER);
        control(c,791,387,34,"◎",s.targetIndex>=0?"RELEASE":"LOCK",
                s.targetIndex>=0?GOLD:MIST);
        text(c,"DRAG RIGHT SIDE TO ORBIT CAMERA",500,582,11,MIST,false,true);
    }
    /**
     * Character workshop HUD. Fullscreen native 3D remains visible behind
     * transparent inspection controls. No WebView or browser UI.
     */
    private void drawModelAtelier(Canvas c){
        ModelStudio.Snapshot m=game.studio.snapshot();
        pane(c,14,10,986,102,8);
        frame(c,21,15,979,97);
        text(c,"◀  BACK",35,47,17,GOLD,true,false);
        text(c,"VEILFORGE TESTING GROUNDS",500,39,25,PALE,true,true);
        text(c,ModelStudio.ITEMS[m.item],500,78,19,GOLD,true,true);
        text(c,"IMPORT OBJ",170,158,14,GOLD,true,true);
        text(c,m.ultraMesh?"SCULPT: ULTRA":"SCULPT: LITE",429,158,14,GOLD,true,true);
        text(c,"HAND DETAIL",660,158,14,GOLD,true,true);
        text(c,"−",827,159,35,GOLD,true,true);
        text(c,"+",931,159,35,GOLD,true,true);
        text(c,"ZOOM",883,165,12,MIST,true,true);
        text(c,"CAMERA  "+String.format(java.util.Locale.US,"%.1fm",m.zoom),
             824,43,14,MIST,true,false);
        text(c,"Drag to orbit • Pinch to zoom • Two fingers to pan",500,126,14,MIST,false,true);
        // Crosshair and subtle stone platform reference remain visible in 3D.
        thinLine(c,493,302,507,302,GOLD,.24f,1);
        thinLine(c,500,295,500,309,GOLD,.24f,1);
        pane(c,22,471,978,594,9);
        text(c,"◀",285,526,34,GOLD,true,true);
        text(c,"NEXT MODEL  ▶",637,525,18,GOLD,true,true);
        text(c,"←  PREVIOUS",169,525,16,PALE,true,true);
        text(c,"LIGHTING",47,565,11,MIST,true,false);
        text(c,ModelStudio.LIGHTS[m.light],180,565,14,GOLD,true,true);
        text(c,"MATERIAL",327,565,11,MIST,true,false);
        text(c,ModelStudio.MATERIALS[m.material],520,565,14,GOLD,true,true);
        text(c,m.autoTurn?"⏸ AUTO ORBIT":"▶ AUTO ORBIT",764,565,13,PALE,true,true);
        text(c,"RESET",920,565,14,PALE,true,true);
        // Orientation marker: a calibrated studio model, not a combat arena.
        text(c,(m.item==11||m.item==12||m.item==13)?
            "TAP TO REVIEW: "+game.studio.reviewViewName()+"  •  FRONT / SIDE / BACK / 3/4":
            "0°  —  90°  —  180°  —  270°",500,456,12,MIST,false,true);
        if(android.os.SystemClock.uptimeMillis()-lastStudioDiagnosticUptime>1150){
            lastStudioDiagnosticUptime=android.os.SystemClock.uptimeMillis();
            Log.i("VEILBOUND_STUDIO","item="+m.item+" name="+ModelStudio.ITEMS[m.item]+
                " light="+m.light+" material="+m.material+
                " yaw="+m.yaw+" pitch="+m.pitch+" zoom="+m.zoom);
        }
    }
    private float normX(float raw){return raw*1000f/Math.max(1,getWidth());}
    private float normY(float raw){return raw*600f/Math.max(1,getHeight());}
    private static boolean near(float x,float y,float bx,float by,float radius){
        return (x-bx)*(x-bx)+(y-by)*(y-by)<radius*radius;
    }
    @Override public boolean onTouchEvent(MotionEvent event){
        if("lab".equals(game.snapshot().mode))return onLabTouch(event);
        int index=event.getActionIndex(),action=event.getActionMasked();
        if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){
            float x=normX(event.getX(index)),y=normY(event.getY(index));
            WorldState.Snapshot s=game.snapshot();
            if(s.mode.equals("title")&&x>345&&x<655&&y>466&&y<532){
                game.enterStudio();invalidate();return true;
            }
            if(!s.mode.equals("playing")){
                game.start();invalidate();return true;
            }
            if(s.dialogue&&x>230&&x<780&&y<185){game.dismissStory();return true;}
            if(near(x,y,905,484,76)){game.attack();return true;}
            if(near(x,y,806,520,65)){game.roll();return true;}
            if(near(x,y,908,365,60)){game.interact();return true;}
            if(near(x,y,791,387,46)){game.toggleLock();return true;}
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
    private boolean onLabTouch(MotionEvent event){
        int action=event.getActionMasked(),idx=event.getActionIndex();
        ModelStudio lab=game.studio;
        if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){
            float x=normX(event.getX(idx)),y=normY(event.getY(idx));
            if(action==MotionEvent.ACTION_DOWN){
                if(y<100&&x<145){
                    game.exitStudio();
                    Log.i("VEILBOUND_STATE","mode=title studio_exit_via_touch");
                    invalidate();return true;
                }
                if(y>120&&y<213&&x<310){
                    if(importAction!=null)importAction.run();
                    return true;
                }
                if(y>120&&y<213&&x>310&&x<567){
                    lab.toggleMeshDetail();invalidate();return true;
                }
                if(y>120&&y<213&&x>570){
                    if(x<766)lab.focusDetail();
                    else if(x<874)lab.dolly(.235f);
                    else lab.dolly(-.235f);
                    invalidate();return true;
                }
                // Human-specific, reproducible 4-angle camera control.
                if(y>432&&y<481&&x>300&&x<700&&(lab.snapshot().item==11||lab.snapshot().item==12||lab.snapshot().item==13)){
                    lab.nextReviewView();invalidate();return true;
                }
                if(y>485&&y<548){
                    if(x<440){lab.nextItem(-1);invalidate();return true;}
                    if(x>540){lab.nextItem(1);invalidate();return true;}
                }
                if(y>=548){
                    if(x<300)lab.nextLight();
                    else if(x<665)lab.nextMaterial();
                    else if(x<847)lab.toggleTurntable();
                    else lab.reset();
                    invalidate();return true;
                }
                labDragPointer=event.getPointerId(idx);
                labLastX=x;labLastY=y;
            }else if(event.getPointerCount()>=2){
                float dx=normX(event.getX(0)-event.getX(1));
                float dy=normY(event.getY(0)-event.getY(1));
                labPinchDistance=(float)Math.hypot(dx,dy);
            }
        }else if(action==MotionEvent.ACTION_MOVE){
            if(event.getPointerCount()>=2){
                float x0=normX(event.getX(0)),y0=normY(event.getY(0));
                float x1=normX(event.getX(1)),y1=normY(event.getY(1));
                float distance=(float)Math.hypot(x0-x1,y0-y1);
                if(labPinchDistance>5&&distance>5)
                    lab.dolly((float)Math.log(labPinchDistance/distance));
                labPinchDistance=distance;
                float centerX=(x0+x1)*.5f,centerY=(y0+y1)*.5f;
                lab.pan((centerX-labLastX)*.008f,(labLastY-centerY)*.007f);
                labLastX=centerX;labLastY=centerY;
            }else if(event.getPointerCount()==1){
                int id=event.getPointerId(0);
                float x=normX(event.getX(0)),y=normY(event.getY(0));
                if(id==labDragPointer){
                    lab.orbit((x-labLastX)*.011f,(labLastY-y)*.009f);
                    labLastX=x;labLastY=y;
                }else{
                    labDragPointer=id;labLastX=x;labLastY=y;
                }
            }
            invalidate();
        }else if(action==MotionEvent.ACTION_POINTER_UP){
            labPinchDistance=0;
            labDragPointer=-1;
        }else if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_CANCEL){
            labPinchDistance=0;
            labDragPointer=-1;
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