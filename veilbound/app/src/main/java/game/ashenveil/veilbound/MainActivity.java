package game.ashenveil.veilbound;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.opengl.GLSurfaceView;
import android.os.Bundle;
import android.net.Uri;
import android.widget.Toast;
import java.io.InputStream;
import android.util.Log;
import android.view.View;
import android.view.WindowManager;
import android.widget.FrameLayout;

/** Actual native fullscreen Android game Activity (OpenGL ES + Canvas). */
public final class MainActivity extends Activity {
    private GLSurfaceView scene;
    private WorldState game;
    private WardenHud hud;
    private ValeRenderer renderer;
    private FrameLayout root;
    private LoadingView splash;
    private volatile boolean foreground=true;
    private static final int REQUEST_OBJ=7210;

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
        root=new FrameLayout(this);
        splash=new LoadingView(this);
        root.addView(splash,new FrameLayout.LayoutParams(-1,-1));
        setContentView(root);
        splash.update(1,"Preparing the Bellwarden");
        Log.i("VEILBOUND_BOOT","SPLASH_VISIBLE source=real_loading_tasks");
        // Heavy procedural geometry and PBR atlas generation run away from
        // Android UI and OpenGL threads. The scene is installed only after
        // the immutable CPU bundle is ready.
        new Thread(new Runnable(){
            @Override public void run(){
                try{
                    final BootAssets prebuilt=BootAssets.prepare(new BootAssets.Progress(){
                        @Override public void stage(final int percent,final String description){
                            Log.i("VEILBOUND_BOOT","STAGE percent="+percent+" label="+description);
                            runOnUiThread(new Runnable(){
                                @Override public void run(){
                                    if(splash!=null)splash.update(percent,description);
                                }
                            });
                        }
                    });
                    runOnUiThread(new Runnable(){
                        @Override public void run(){createGameScene(prebuilt);}
                    });
                }catch(final Throwable fault){
                    Log.e("VEILBOUND_BOOT","Startup preprocessing failed",fault);
                    runOnUiThread(new Runnable(){
                        @Override public void run(){
                            if(splash!=null)splash.failed("Asset preparation failed");
                        }
                    });
                }
            }
        },"VeilboundAssetBaker").start();
    }
    private void createGameScene(BootAssets prebuilt){
        if(isFinishing())return;
        game=new WorldState();
        scene=new GLSurfaceView(this);
        scene.setEGLContextClientVersion(2);
        scene.setPreserveEGLContextOnPause(true);
        renderer=new ValeRenderer(game,prebuilt,new ValeRenderer.StartupListener(){
            @Override public void stage(final int percent,final String description){
                Log.i("VEILBOUND_BOOT","GL_STAGE percent="+percent+" label="+description);
                runOnUiThread(new Runnable(){
                    @Override public void run(){
                        if(splash!=null)splash.update(percent,description);
                    }
                });
            }
            @Override public void ready(){
                runOnUiThread(new Runnable(){
                    @Override public void run(){
                        if(splash!=null){
                            splash.update(100,"The Bellwarden awakens");
                            root.removeView(splash);splash=null;
                        }
                        Log.i("VEILBOUND_BOOT","FIRST_FRAME_READY");
                    }
                });
            }
        });
        scene.setRenderer(renderer);
        scene.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);
        hud=new WardenHud(this,game);
        hud.setImportAction(new Runnable(){
            @Override public void run(){chooseObjFile();}
        });
        root.addView(scene,0,new FrameLayout.LayoutParams(-1,-1));
        root.addView(hud,1,new FrameLayout.LayoutParams(-1,-1));
        if(foreground)scene.onResume();
        Log.i("VEILBOUND_STATE","activity_created native_gl=true mode=title");
    }
    @Override protected void onResume(){
        super.onResume();foreground=true;immersive();
        if(scene!=null)scene.onResume();
    }
    @Override protected void onPause(){
        foreground=false;
        if(scene!=null)scene.onPause();super.onPause();
    }
    @Override protected void onNewIntent(Intent intent){
        super.onNewIntent(intent);
        setIntent(intent);
        if(game!=null&&"game.ashenveil.veilbound.INSPECT".equals(intent.getAction())){
            WorldState.Snapshot s=game.snapshot();
            Log.i("VEILBOUND_STATE","INSPECT mode="+s.mode+" x="+s.x+" z="+s.z+
                  " hp="+s.health+" stamina="+s.stamina+" sigils="+s.fragments);
        }
    }
    private void chooseObjFile(){
        Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        try{startActivityForResult(intent,REQUEST_OBJ);}
        catch(Exception error){
            Toast.makeText(this,"File picker unavailable",Toast.LENGTH_LONG).show();
        }
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request!=REQUEST_OBJ||result!=RESULT_OK||data==null||data.getData()==null)return;
        final Uri uri=data.getData();
        new Thread(new Runnable(){
            @Override public void run(){
                try(InputStream stream=getContentResolver().openInputStream(uri)){
                    if(stream==null)throw new java.io.IOException("Cannot open OBJ file");
                    final ArtKit.Model imported=ObjMeshLoader.load(stream);
                    renderer.stageImportedMesh(imported);
                    runOnUiThread(new Runnable(){
                        @Override public void run(){
                            game.studio.selectImported();
                            Toast.makeText(MainActivity.this,
                                "Imported "+imported.triangleCount+" triangles into the Atelier",
                                Toast.LENGTH_LONG).show();
                        }
                    });
                }catch(final Exception error){
                    Log.e("VEILBOUND_STUDIO","Import failed",error);
                    runOnUiThread(new Runnable(){
                        @Override public void run(){
                            Toast.makeText(MainActivity.this,
                                "OBJ import failed: "+error.getMessage(),
                                Toast.LENGTH_LONG).show();
                        }
                    });
                }catch(final OutOfMemoryError error){
                    Log.e("VEILBOUND_STUDIO","Imported mesh exceeds device memory",error);
                    runOnUiThread(new Runnable(){
                        @Override public void run(){
                            Toast.makeText(MainActivity.this,
                                "Model too large for this device's available memory",
                                Toast.LENGTH_LONG).show();
                        }
                    });
                }
            }
        },"VeilboundObjImporter").start();
    }
        @Override public void onWindowFocusChanged(boolean focus){
        super.onWindowFocusChanged(focus);
        if(focus)immersive();
    }
}