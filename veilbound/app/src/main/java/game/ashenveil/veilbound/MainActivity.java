package game.ashenveil.veilbound;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.opengl.GLSurfaceView;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.view.WindowManager;
import android.widget.FrameLayout;

/** Actual native fullscreen Android game Activity (OpenGL ES + Canvas). */
public final class MainActivity extends Activity {
    private GLSurfaceView scene;
    private WorldState game;
    private WardenHud hud;

    private void immersive(){
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                View.SYSTEM_UI_FLAG_FULLSCREEN |
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE);
        immersive();
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        game=new WorldState();
        scene=new GLSurfaceView(this);
        scene.setEGLContextClientVersion(2);
        scene.setPreserveEGLContextOnPause(true);
        scene.setRenderer(new ValeRenderer(game));
        scene.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);
        hud=new WardenHud(this,game);
        FrameLayout frame=new FrameLayout(this);
        frame.addView(scene,new FrameLayout.LayoutParams(-1,-1));
        frame.addView(hud,new FrameLayout.LayoutParams(-1,-1));
        setContentView(frame);
        Log.i("VEILBOUND_STATE","activity_created native_gl=true mode=title");
    }
    @Override protected void onResume(){
        super.onResume();immersive();
        if(scene!=null)scene.onResume();
    }
    @Override protected void onPause(){
        if(scene!=null)scene.onPause();super.onPause();
    }
    @Override protected void onNewIntent(Intent intent){
        super.onNewIntent(intent);
        setIntent(intent);
        if("game.ashenveil.veilbound.INSPECT".equals(intent.getAction())){
            WorldState.Snapshot s=game.snapshot();
            Log.i("VEILBOUND_STATE","INSPECT mode="+s.mode+" x="+s.x+" z="+s.z+
                  " hp="+s.health+" stamina="+s.stamina+" sigils="+s.fragments);
        }
    }
    @Override public void onWindowFocusChanged(boolean focus){
        super.onWindowFocusChanged(focus);
        if(focus)immersive();
    }
}