package com.trioncompasitor.vqstudio;

import android.app.*;
import android.os.*;
import android.content.*;
import android.graphics.Color;
import android.net.Uri;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;

/**
 * VQ Studio is a companion: GitHub live workflow telemetry, local 3D viewport,
 * explicit Trion-only start/cancel controls. No GitHub tokens in this app.
 */
public final class MainActivity extends Activity {
  private static final int PICK_OBJ=7;
  private final Handler timer=new Handler(Looper.getMainLooper());
  private final ExecutorService io=Executors.newSingleThreadExecutor();
  private volatile boolean active=false,autoLoad=true;
  private volatile boolean pairedIntegrationTest=false;
  private volatile String loadedSnapshotKey="";
  private volatile long lastAnonymousPollMs=0;
  private final java.util.concurrent.atomic.AtomicBoolean refreshBusy=
      new java.util.concurrent.atomic.AtomicBoolean(false);
  private TextView status,history,meshLabel,small;
  private ModelViewport viewport;
  private volatile String requestId="",runId="";
  private LinearLayout root;
  private final int mint=Color.rgb(94,244,198),ink=Color.rgb(224,238,238);
  private final Runnable updater=new Runnable(){@Override public void run(){
    if(!active)return;
    refresh();
    timer.postDelayed(this,15000);
  }};
  @Override public void onCreate(Bundle b){
    super.onCreate(b);
    requestId=getPreferences(0).getString("request_id","");
    runId=getPreferences(0).getString("run_id","");
    handleIntent(getIntent());
    root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
    root.setBackgroundColor(Color.BLACK);
    root.setPadding(dp(12),dp(12),dp(12),dp(8));
    TextView title=text("VQ  /  MODEL STUDIO",23,mint);
    root.addView(title);
    status=text("Connecting to VQ worker status…",12,ink);root.addView(status);
    viewport=new ModelViewport(this);
    root.addView(viewport,new LinearLayout.LayoutParams(-1,0,5));
    meshLabel=text("DEMONSTRATION MESH — not a worker result",12,Color.LTGRAY);root.addView(meshLabel);
    LinearLayout buttons=new LinearLayout(this);
    buttons.setOrientation(LinearLayout.HORIZONTAL);
    buttons.addView(button("Trion controls",this::openTrion),new LinearLayout.LayoutParams(0,dp(55),1));
    buttons.addView(button("Import OBJ",this::pickModel),new LinearLayout.LayoutParams(0,dp(55),1));
    root.addView(buttons);
    LinearLayout toggles=new LinearLayout(this);
    toggles.addView(button("Glow edges",()->viewport.toggleWire()),new LinearLayout.LayoutParams(0,dp(48),1));
    toggles.addView(button("Rotate / stop",()->viewport.toggleOrbit()),new LinearLayout.LayoutParams(0,dp(48),1));
    toggles.addView(button("Update",this::refresh),new LinearLayout.LayoutParams(0,dp(48),1));
    root.addView(toggles);
    root.addView(button("Open current model snapshots on GitHub",this::openRunArtifacts));
    root.addView(button("Automatic verified mesh loading ON/OFF",()->{
      autoLoad=!autoLoad;
      small.setText(autoLoad?
        "AUTO ON • next integrity-verified 3D snapshot replaces geometry; camera remains unchanged.":
        "AUTO OFF • imported/selected mesh remains unchanged until you turn loading on.");
      if(autoLoad)refresh();
    }));
    small=text("AUTO ON • verified worker revisions appear in this 3D viewer. Camera orbit and zoom are preserved.",12,ink);
    root.addView(small);
    ScrollView scroll=new ScrollView(this);
    history=text("No worker update yet.",12,Color.rgb(159,210,210));history.setTextIsSelectable(true);
    scroll.addView(history);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,3));
    setContentView(root);
    maybeRunPairedTest(getIntent());
  }
  /**
   * Test-only Android IPC: Trion serves an actual procedural model via a
   * UID-restricted read-only provider; VQ rechecks SHA and retains camera.
   */
  private boolean maybeRunPairedTest(Intent intent){
    if(!BuildConfig.DEBUG||intent==null||
       !intent.getBooleanExtra("vq_pair_test",false))return false;
    int revision=intent.getIntExtra("vq_pair_revision",0);
    if(revision!=1&&revision!=2)return false;
    pairedIntegrationTest=true;
    io.execute(()->{
      try{
        LiveMeshClient.Snapshot snap=LiveMeshClient.pairedTestFixture(this,revision);
        runOnUiThread(()->{
          String before=viewport.cameraFingerprint();
          viewport.setMeshKeepingCamera(snap.mesh);
          String after=viewport.cameraFingerprint();
          if(!before.equals(after)){
            android.util.Log.e("VQ_PAIR","CAMERA_CHANGED rev="+revision);
            status.setText("Paired test failed: camera changed");
            return;
          }
          loadedSnapshotKey=snap.identity();
          meshLabel.setText("TRION VERIFIED MESH rev "+revision+" • "+snap.triangles+
                 " triangles • SHA "+snap.sha.substring(0,16));
          small.setText("PAIRED TEST: model rev "+revision+
            " arrived from Trion over verified Android provider");
          status.setText("TRION ⇄ VQ VERIFIED • revision "+revision);
          history.setText("Trion provided "+snap.mesh.label+" / SHA256 "+snap.sha+
            "\nCamera preserved: "+before.equals(after)+
            "\nOnly the VQ Studio app UID can read this mesh.");
          android.util.Log.i("VQ_PAIR",
             "TRANSFER_VERIFIED rev="+revision+
             " sha="+snap.sha+" triangles="+snap.triangles+
             " camera_preserved=true");
        });
      }catch(Exception error){
        String msg=error.getMessage();
        android.util.Log.e("VQ_PAIR","TRANSFER_FAILED rev="+revision+" "+msg,error);
        runOnUiThread(()->status.setText("PAIRED TEST FAILED: "+msg));
      }
    });
    return true;
  }
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density);}
  private TextView text(String txt,int size,int color){
    TextView t=new TextView(this);t.setText(txt);t.setTextSize(size);t.setTextColor(color);
    t.setPadding(dp(7),dp(5),dp(7),dp(5));return t;
  }
  private Button button(String label,Runnable task){
    Button b=new Button(this);b.setText(label);b.setAllCaps(false);
    b.setTextSize(11);b.setOnClickListener(v->task.run());return b;
  }
  private void handleIntent(Intent intent){
    if(intent==null)return;
    if(VQProtocol.SHOW_JOB.equals(intent.getAction())){
      String id=intent.getStringExtra("request_id");
      String run=intent.getStringExtra("run_id");
      if(VQProtocol.validRequestId(id)&&!id.equals(requestId)){
        requestId=id;runId="";loadedSnapshotKey="";autoLoad=true;
      }
      if(VQProtocol.validRunId(run))runId=run;
      getPreferences(0).edit().putString("request_id",requestId)
          .putString("run_id",runId).apply();
    }
  }
  @Override protected void onNewIntent(Intent i){
    super.onNewIntent(i);setIntent(i);handleIntent(i);
    if(!maybeRunPairedTest(i))refresh();
  }
  @Override protected void onResume(){
    super.onResume();active=true;timer.removeCallbacks(updater);
    if(!pairedIntegrationTest)timer.post(updater);
  }
  @Override protected void onPause(){active=false;timer.removeCallbacks(updater);super.onPause();}
  @Override protected void onDestroy(){timer.removeCallbacks(updater);io.shutdownNow();super.onDestroy();}
  private void openRunArtifacts(){
    if(!VQProtocol.validRunId(runId)){status.setText("No verified VQ workflow run selected yet.");return;}
    Intent web=new Intent(Intent.ACTION_VIEW,Uri.parse(
      "https://github.com/"+VQProtocol.REPO+"/actions/runs/"+runId));
    try{startActivity(web);}catch(Exception e){status.setText("No browser available to open worker artifacts");}
  }
  private void openTrion(){
    Intent intent=new Intent();
    intent.setClassName(VQProtocol.TRION_PACKAGE,VQProtocol.TRION_BRIDGE);
    intent.putExtra("request_id",requestId);intent.putExtra("run_id",runId);
    try{startActivity(intent);}catch(Exception e){
      new AlertDialog.Builder(this).setTitle("Trion bridge not installed")
        .setMessage("Install the companion version of Trion Assistant to submit, stop and correct VQ jobs. VQ Studio never receives or stores your GitHub token.")
        .setPositiveButton("OK",null).show();
    }
  }
  private void pickModel(){
    Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
    i.setType("*/*");i.addCategory(Intent.CATEGORY_OPENABLE);
    startActivityForResult(i,PICK_OBJ);
  }
  @Override protected void onActivityResult(int request,int result,Intent data){
    super.onActivityResult(request,result,data);
    if(request!=PICK_OBJ||result!=RESULT_OK||data==null)return;
    final Uri uri=data.getData();
    if(uri==null)return;
    status.setText("Loading real source OBJ…");
    io.execute(()->{
      try(InputStream in=getContentResolver().openInputStream(uri)){
        MeshData mesh=MeshData.read(in,"Imported real OBJ / "+uri.getLastPathSegment());
        runOnUiThread(()->{
          autoLoad=false;
          loadedSnapshotKey="";
          small.setText("AUTO OFF • manually imported model protected; enable auto loading to follow VQ.");
          viewport.setMesh(mesh);
          meshLabel.setText(mesh.label+" • "+mesh.triangles.length+" triangles");
          status.setText("Local OBJ loaded; remote job progress is shown below");
        });
      }catch(Exception e){
        runOnUiThread(()->new AlertDialog.Builder(this).setTitle("OBJ import failed")
          .setMessage(e.getMessage()).setPositiveButton("OK",null).show());
      }
    });
  }
  private static String get(String endpoint)throws Exception{
    if(!endpoint.startsWith("https://api.github.com/repos/timmytwopointoh/Project-hail/actions/"))
      throw new IOException("Untrusted status endpoint");
    HttpURLConnection h=(HttpURLConnection)new URL(endpoint).openConnection();
    h.setConnectTimeout(10000);h.setReadTimeout(12000);
    h.setRequestProperty("Accept","application/vnd.github+json");
    h.setRequestProperty("User-Agent","VQStudio/0.1");
    try{
      if(h.getResponseCode()!=200)throw new IOException("GitHub status unavailable (HTTP "+h.getResponseCode()+")");
      try(InputStream in=h.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream()){
        byte[] buf=new byte[8192];int n;while((n=in.read(buf))>=0){
          if(out.size()+n>600000)throw new IOException("Excess status data");
          out.write(buf,0,n);
        }
        return out.toString("UTF-8");
      }
    }finally{h.disconnect();}
  }
  private void loadVerifiedRevision(String requestedId,String selectedRun){
    try{
      LiveMeshClient.Snapshot snap=LiveMeshClient.latest(this,requestedId,selectedRun);
      if(snap==null)return;
      if(snap.identity().equals(loadedSnapshotKey))return;
      runOnUiThread(()->{
        if(!active||!autoLoad||!requestedId.equals(requestId)
           ||(!runId.isEmpty()&&!selectedRun.equals(runId)))return;
        viewport.setMeshKeepingCamera(snap.mesh);
        loadedSnapshotKey=snap.identity();
        runId=snap.runId;
        getPreferences(0).edit().putString("run_id",snap.runId).apply();
        meshLabel.setText(snap.mesh.label+" • "+snap.triangles+
                          " triangles • SHA256 "+snap.sha.substring(0,12));
        small.setText("AUTO ON • live revision "+snap.sequence+
          " loaded without camera reset • "+snap.stage+
          " • geometry hash verified; artist approval still required");
      });
    }catch(Exception e){
      final String message=e.getMessage()==null?"Model update not yet available":e.getMessage();
      runOnUiThread(()->{
        if(active&&autoLoad)
          small.setText("AUTO ON • waiting for verified model: "+message+
             " • current mesh retained");
      });
    }
  }
  private boolean authenticatedStatus(){
    try{
      android.os.Bundle args=new android.os.Bundle();
      String requested=requestId,wanted=runId;
      args.putString("request_id",requested);
      args.putString("run_id",wanted);
      android.os.Bundle out=getContentResolver().call(
         Uri.parse("content://com.trioncompasitor.assistant.vq.snapshots"),
         "status",null,args);
      if(out==null)return false;
      String state=out.getString("state","");
      if("available".equals(state)){
        String matchingRun=out.getString("run_id","");
        if(!VQProtocol.validRunId(matchingRun))return false;
        final String headline=out.getString("headline","");
        final String description=out.getString("progress","");
        runOnUiThread(()->{
          if(!active||!requested.equals(requestId))return;
          if(!matchingRun.equals(runId)){runId=matchingRun;loadedSnapshotKey="";}
          getPreferences(0).edit().putString("run_id",matchingRun).apply();
          status.setText(headline);history.setText(description);
        });
        if(autoLoad)loadVerifiedRevision(requested,matchingRun);
        return true;
      }
      if("no_job".equals(state)){
        runOnUiThread(()->{
          if(!active)return;
          status.setText(out.getString("headline","Trion is connected"));
          history.setText(out.getString("progress","No current VQ job"));
        });
        return true;
      }
      return false;
    }catch(Exception e){
      // Trion not installed, token not connected, or bridge temporarily offline.
      // Public status remains a degraded, rate-limited fallback.
      return false;
    }
  }
  private void refresh(){
    if(!active||!refreshBusy.compareAndSet(false,true))return;
    io.execute(()->{
      try{
        if(authenticatedStatus())return;
        long now=System.currentTimeMillis();
        if(now-lastAnonymousPollMs<180000L)return;
        lastAnonymousPollMs=now;
        String base="https://api.github.com/repos/"+VQProtocol.REPO+"/actions/";
        JSONObject payload=new JSONObject(get(base+"workflows/"+VQProtocol.WORKFLOW+"/runs?branch="+
          URLEncoder.encode(VQProtocol.BRANCH,"UTF-8")+"&per_page=12"));
        JSONArray runs=payload.optJSONArray("workflow_runs");
        JSONObject chosen=null;
        if(runs!=null){
          for(int i=0;i<runs.length();i++){
            JSONObject item=runs.getJSONObject(i);
            String title=item.optString("display_title","");
            if(VQProtocol.validRequestId(requestId)&&title.contains(requestId)){
              chosen=item;break;
            }
            if(VQProtocol.validRunId(runId)&&runId.equals(item.optString("id"))){chosen=item;break;}
          }
        }
        String headline,progress;
        if(chosen==null){
          headline="ONLINE • no matching VQ model job"+(requestId.isEmpty()?"":" / "+requestId);
          progress="Trion can submit a catalog model. The editor shows a demonstration mesh until you import actual OBJ data.\n";
        }else{
          String id=chosen.getString("id");
          String state=chosen.optString("status","unknown");
          String conclusion=chosen.optString("conclusion","");
          headline="VQ WORKER • "+state+(conclusion.equals("null")?"":" / "+conclusion);
          StringBuilder trace=new StringBuilder();
          trace.append(chosen.optString("display_title")).append("\n");
          trace.append("Run: ").append(id).append("\n");
          trace.append("Updated: ").append(chosen.optString("updated_at","")).append("\n\n");
          JSONObject jobs=new JSONObject(get(base+"runs/"+id+"/jobs?per_page=20"));
          JSONArray list=jobs.optJSONArray("jobs");
          if(list!=null)for(int i=0;i<list.length();i++){
            JSONObject j=list.getJSONObject(i);
            trace.append("● ").append(j.optString("name")).append(" [")
                .append(j.optString("conclusion").equals("null")?j.optString("status"):j.optString("conclusion")).append("]\n");
            JSONArray steps=j.optJSONArray("steps");
            if(steps!=null)for(int k=0;k<steps.length();k++){
              JSONObject step=steps.getJSONObject(k);
              trace.append("  ").append(step.optString("status").equals("completed")?"✓":"·").append(" ")
                  .append(step.optString("name")).append("\n");
            }
          }
          progress=trace.toString();
          String finalId=id;
          runOnUiThread(()->{
            if(!finalId.equals(runId)){runId=finalId;loadedSnapshotKey="";}
            getPreferences(0).edit().putString("run_id",finalId).apply();
          });
        }
        final String a=headline,b=progress;
        runOnUiThread(()->{if(!active)return;status.setText(a);history.setText(b);});
        // Source updates are fetched through Trion's caller-restricted ContentProvider,
        // never via a token stored in VQ Studio. Each revision is verified twice.
        if(chosen!=null&&autoLoad){
          final String chosenRun=chosen.optString("id","");
          final String chosenRequest=requestId;
          if(VQProtocol.validRequestId(chosenRequest)&&VQProtocol.validRunId(chosenRun))
            loadVerifiedRevision(chosenRequest,chosenRun);
        }
      }catch(Exception e){
        runOnUiThread(()->{if(!active)return;status.setText("NETWORK UNAVAILABLE • local 3D viewer still works");
          history.setText("Worker status could not be refreshed: "+e.getMessage()+
             "\nNo evidence of a new model update. Use Trion to inspect authenticated jobs.");});
      }finally{
        refreshBusy.set(false);
      }
    });
  }
}