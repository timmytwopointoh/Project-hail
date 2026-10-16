package game.ashenveil.veilbound;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Shader;
import android.view.View;

/**
 * Native fullscreen startup canvas. Progress comes from completed CPU/GL work,
 * not an arbitrary timer. The overlay stays until the first rendered frame.
 */
public final class LoadingView extends View {
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF rect=new RectF();
    private final Bitmap knight;
    private int percent=0;
    private String stage="Preparing the realm";
    private boolean error=false;

    public LoadingView(Context context){
        super(context);
        knight=BitmapFactory.decodeResource(getResources(),R.drawable.veilbound_icon);
        setLayerType(View.LAYER_TYPE_SOFTWARE,null);
        setContentDescription("Veilbound startup loading progress");
    }
    public void update(int value,String label){
        percent=Math.max(0,Math.min(100,value));
        stage=label==null?"Preparing the realm":label;
        error=false;invalidate();
    }
    public void failed(String label){
        error=true;stage=label==null?"The realm could not awaken":label;
        invalidate();
    }
    @Override protected void onDraw(Canvas canvas){
        super.onDraw(canvas);
        float w=getWidth(),h=getHeight();
        paint.reset();paint.setAntiAlias(true);
        paint.setShader(new LinearGradient(0,0,w,h,
              new int[]{Color.rgb(6,11,17),Color.rgb(14,27,34),
                        Color.rgb(3,8,13)},null,Shader.TileMode.CLAMP));
        canvas.drawRect(0,0,w,h,paint);paint.setShader(null);
        float scale=Math.min(w/1200f,h/620f);
        canvas.save();canvas.translate(w*.5f,h*.5f);canvas.scale(scale,scale);
        paint.setColor(Color.rgb(68,89,89));paint.setStrokeWidth(1.4f);
        paint.setStyle(Paint.Style.STROKE);
        canvas.drawCircle(-360,0,240,paint);
        canvas.drawCircle(-360,0,233,paint);
        paint.setStyle(Paint.Style.FILL);
        if(knight!=null){
            rect.set(-535,-215,-185,135);
            paint.setAlpha(235);
            canvas.drawBitmap(knight,null,rect,paint);
            paint.setAlpha(255);
        }
        label(canvas,"VEILBOUND",60,-109,65,Color.rgb(222,186,137),true);
        label(canvas,"ASH OF THE BELLS",65,-64,22,Color.rgb(214,223,223),false);
        label(canvas,"THE SEVENTH BELL REMEMBERS",70,3,16,
              Color.rgb(112,159,159),false);
        label(canvas,stage,70,100,20,error?Color.rgb(224,105,80):
              Color.rgb(222,225,214),false);
        rect.set(70,132,493,146);paint.setColor(Color.rgb(38,52,54));
        canvas.drawRoundRect(rect,6,6,paint);
        rect.set(70,132,70+423*percent/100f,146);
        paint.setColor(error?Color.rgb(190,65,50):Color.rgb(97,199,164));
        canvas.drawRoundRect(rect,6,6,paint);
        label(canvas,error?"STARTUP ERROR":percent+"%  /  REAL ASSET PREPARATION",
              70,181,16,Color.rgb(166,183,177),false);
        label(canvas,"NATIVE ANDROID  •  OFFLINE  •  NO DOWNLOADS",
              70,242,14,Color.rgb(105,137,137),false);
        canvas.restore();
    }
    private void label(Canvas c,String value,float x,float y,float size,
                       int color,boolean heavy){
        paint.setShader(null);paint.setColor(color);
        paint.setTypeface(android.graphics.Typeface.create(
            heavy?"serif":"sans-serif",heavy?1:0));
        paint.setTextSize(size);paint.setStyle(Paint.Style.FILL);
        c.drawText(value,x,y,paint);
    }
}
