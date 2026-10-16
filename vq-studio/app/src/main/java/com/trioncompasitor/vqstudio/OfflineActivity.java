package com.trioncompasitor.vqstudio;

import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.net.Uri;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;

/** Offline-first VQ Studio. The app contains its own persistent model repository. */
public final class OfflineActivity extends Activity {
  private final Handler handler=new Handler(Looper.getMainLooper());
  private final ExecutorService background=Executors.newSingleThreadExecutor();
  private final int mint=Color.rgb(105,245,198);
  private EditText prompt;
  private TextView status,details,asset;
  private ModelViewport viewport;
  private volatile boolean active,auto=true;
  private volatile String selectedId="",displayedSha="";
  private final Runnable tick=new Runnable(){@Override public void run(){
    if(active){refresh();handler.postDelayed(this,500);}
  }};
  @Override public void onCreate(Bundle b){
    super.onCreate(b);
    LinearLayout root=new LinearLayout(this);
    root.setOrientation(LinearLayout.VERTICAL);
    root.setPadding(14,22,14,10);
    root.setBackgroundColor(Color.rgb(3,6,10));
    TextView title=label("VQ  /  OFFLINE MODEL STUDIO",23,mint);
    root.addView(title);
    TextView subtitle=label("100% local • private model repository • no account required",13,Color.LTGRAY);
    root.addView(subtitle);
    status=label("Ready to create an offline model.",14,mint);
    root.addView(status);
    viewport=new ModelViewport(this);
    root.addView(viewport,new LinearLayout.LayoutParams(-1,0,5f));
    asset=label("DEMONSTRATION MESH  •  prompts create real stored OBJs",12,Color.LTGRAY);
    root.addView(asset);
    prompt=new EditText(this);
    prompt.setSingleLine(false);prompt.setMaxLines(3);
    prompt.setHint("Describe a tree, sword, chest or terrain…");
    prompt.setTextColor(Color.WHITE);prompt.setHintTextColor(Color.GRAY);
    prompt.setText("A detailed ancient tree with branches");
    root.addView(prompt);
    LinearLayout line=new LinearLayout(this);
    line.addView(button("Create locally",this::create),new LinearLayout.LayoutParams(0,48*dp(),1));
    line.addView(button("STOP",this::stop),new LinearLayout.LayoutParams(0,48*dp(),.5f));
    root.addView(line);
    LinearLayout line2=new LinearLayout(this);
    line2.addView(button("Trion",this::openTrion),new LinearLayout.LayoutParams(0,47*dp(),1));
    line2.addView(button("Import OBJ",this::chooseObj),new LinearLayout.LayoutParams(0,47*dp(),1));
    line2.addView(button("Edges",()->viewport.toggleWire()),new LinearLayout.LayoutParams(0,47*dp(),.6f));
    line2.addView(button("Spin",()->viewport.toggleOrbit()),new LinearLayout.LayoutParams(0,47*dp(),.6f));
    root.addView(line2);
    root.addView(button("Automatic revision loading ON/OFF",()->{
      auto=!auto;details.setText(auto?
        "Auto ON • new source revisions load while keeping your camera.":
        "Auto OFF • current model remains selected.");
    }));
    details=label("VQ saves verified model versions on this device. No screenshots are retained.",12,Color.rgb(177,208,204));
    root.addView(details);
    setContentView(root);
    handle(getIntent());
  }
  private int dp(){return (int)getResources().getDisplayMetrics().density;}
  private TextView label(String text,int size,int color){
    TextView v=new TextView(this);v.setText(text);v.setTextSize(size);v.setTextColor(color);
    v.setPadding(8,6,8,6);return v;
  }
  private Button button(String label,Runnable r){
    Button b=new Button(this);b.setText(label);b.setAllCaps(false);b.setTextSize(11);
    b.setOnClickListener(v->r.run());return b;
  }
  private void handle(Intent i){
    if(i==null)return;
    String incoming=i.getStringExtra("prompt");
    if(incoming!=null&&!incoming.isEmpty()&&incoming.length()<=500)prompt.setText(incoming);
    String id=i.getStringExtra("job_id");
    if(id!=null&&id.matches("[a-f0-9]{20}")){selectedId=id;displayedSha="";auto=true;}
  }
  @Override protected void onNewIntent(Intent i){super.onNewIntent(i);setIntent(i);handle(i);refresh();}
  @Override protected void onResume(){super.onResume();active=true;handler.removeCallbacks(tick);handler.post(tick);}
  @Override protected void onPause(){active=false;handler.removeCallbacks(tick);super.onPause();}
  @Override protected void onDestroy(){handler.removeCallbacks(tick);background.shutdownNow();super.onDestroy();}
  private void create(){
    final String text=prompt.getText().toString().trim();
    background.execute(()->{
      try{
        String id=OfflineRepository.of(this).submit(text);
        runOnUiThread(()->{selectedId=id;displayedSha="";auto=true;status.setText("Created job "+id.substring(0,8)+" on this phone");});
      }catch(Exception e){runOnUiThread(()->status.setText("Cannot create: "+e.getMessage()));}
    });
  }
  private void stop(){
    final String id=selectedId;
    new AlertDialog.Builder(this).setTitle("Stop local model generation?")
      .setMessage("The worker stops at its next checkpoint. Previous saved revisions remain safe.")
      .setNegativeButton("Continue",null)
      .setPositiveButton("Stop",(d,w)->{
        boolean requested=OfflineRepository.of(this).stop(id);
        status.setText(requested?"Local STOP requested":"No active generation for the selected job");
      }).show();
  }
  private void refresh(){
    if(!active)return;
    background.execute(()->{
      OfflineRepository store=OfflineRepository.of(this);
      OfflineRepository.Snapshot s=selectedId.isEmpty()?store.latest():store.get(selectedId);
      if(s.id.isEmpty())return;
      byte[] obj=null;String newHash=s.sha;
      if(auto&&s.rev>0&&!newHash.equals(displayedSha)){
        try{obj=store.load(s);}catch(Exception e){final String msg=e.getMessage();runOnUiThread(()->details.setText("Integrity check failed: "+msg));}
      }
      final byte[] bytes=obj;
      runOnUiThread(()->{
        if(!active)return;
        status.setText("LOCAL "+s.state.toUpperCase()+" • "+s.detail);
        if(bytes!=null&&!newHash.equals(displayedSha)&&auto){
          try{
            MeshData mesh=MeshData.read(new ByteArrayInputStream(bytes),s.shape+" • version "+s.rev);
            viewport.setMeshKeepingCamera(mesh);
            displayedSha=newHash;
            asset.setText("LOCAL "+s.shape+" • "+s.triangles+" triangles • rev "+s.rev+" • SHA "+s.sha.substring(0,10));
          }catch(Exception e){details.setText("OBJ failed validation: "+e.getMessage());}
        }
        if(s.rev>0)details.setText("LOCAL REPOSITORY • job "+s.id.substring(0,8)+
          " • revision "+s.rev+" • validated OBJ saved privately");
      });
    });
  }
  private void openTrion(){
    Intent i=new Intent();i.setClassName("com.trioncompasitor.assistant",
        "com.trioncompasitor.assistant.VQBridgeActivity");
    i.putExtra("job_id",selectedId);
    try{startActivity(i);}catch(Exception e){
      new AlertDialog.Builder(this).setTitle("Trion not installed")
          .setMessage("VQ Studio generates and saves models fully offline by itself. Trion is optional.")
          .setPositiveButton("OK",null).show();
    }
  }
  private void chooseObj(){
    Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*");
    i.addCategory(Intent.CATEGORY_OPENABLE);
    startActivityForResult(i,7);
  }
  @Override protected void onActivityResult(int req,int res,Intent data){
    super.onActivityResult(req,res,data);
    if(req!=7||res!=RESULT_OK||data==null||data.getData()==null)return;
    Uri uri=data.getData();
    background.execute(()->{
      try(InputStream source=getContentResolver().openInputStream(uri)){
        MeshData obj=MeshData.read(source,"Imported local OBJ");
        runOnUiThread(()->{
          auto=false;displayedSha="";
          viewport.setMeshKeepingCamera(obj);
          asset.setText("Imported OBJ • "+obj.triangles.length+" triangles");
          details.setText("Manual model loaded • auto follow paused");
        });
      }catch(Exception e){runOnUiThread(()->status.setText("Import error: "+e.getMessage()));}
    });
  }
}