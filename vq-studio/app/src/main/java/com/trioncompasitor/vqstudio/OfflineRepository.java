package com.trioncompasitor.vqstudio;

import android.content.*;
import android.database.*;
import android.database.sqlite.*;
import android.os.*;
import org.json.*;
import java.io.*;
import java.security.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
/** Private on-device model repository: SQLite job index + immutable OBJ versions. */
public final class OfflineRepository extends SQLiteOpenHelper {
  private static OfflineRepository singleton;
  public static synchronized OfflineRepository of(Context c){
    if(singleton==null)singleton=new OfflineRepository(c.getApplicationContext());
    return singleton;
  }
  private final Context context;
  private final ExecutorService worker=Executors.newSingleThreadExecutor();
  private final ConcurrentHashMap<String,AtomicBoolean> cancellations=new ConcurrentHashMap<>();
  private OfflineRepository(Context c){super(c,"vq_models.sqlite",null,1);context=c;}
  @Override public void onCreate(SQLiteDatabase db){
    db.execSQL("CREATE TABLE jobs (id TEXT PRIMARY KEY,prompt TEXT NOT NULL, shape TEXT NOT NULL, state TEXT NOT NULL, rev INTEGER NOT NULL, sha TEXT NOT NULL, triangles INTEGER NOT NULL, detail TEXT NOT NULL, updated INTEGER NOT NULL)");
    db.execSQL("CREATE TABLE revisions (job TEXT NOT NULL,rev INTEGER NOT NULL,sha TEXT NOT NULL,bytes INTEGER NOT NULL,triangles INTEGER NOT NULL,PRIMARY KEY(job,rev))");
  }
  @Override public void onUpgrade(SQLiteDatabase db,int oldVersion,int newVersion){
    throw new IllegalStateException("VQ repository requires explicit migration");
  }
  public static String sha(byte[] data)throws Exception{
    byte[] digest=MessageDigest.getInstance("SHA-256").digest(data);
    StringBuilder b=new StringBuilder();
    for(byte v:digest)b.append(String.format(Locale.ROOT,"%02x",v&255));
    return b.toString();
  }
  private File dir(){
    File d=new File(context.getFilesDir(),"model_repository");
    if(!d.exists()&&!d.mkdirs())throw new IllegalStateException("Could not make local repository");
    return d;
  }
  public synchronized String submit(String prompt)throws Exception{
    if(prompt==null||prompt.trim().isEmpty()||prompt.length()>500)
      throw new IllegalArgumentException("Prompt must be 1–500 characters");
    String shape=OfflineGeometry.supported(prompt);
    String id=UUID.randomUUID().toString().replace("-","").substring(0,20);
    ContentValues v=new ContentValues();
    v.put("id",id);v.put("prompt",prompt);v.put("shape",shape);
    v.put("state","queued");v.put("rev",0);v.put("sha","");v.put("triangles",0);
    v.put("detail","Queued in private on-device model repository");
    v.put("updated",System.currentTimeMillis());
    getWritableDatabase().insertOrThrow("jobs",null,v);
    AtomicBoolean cancel=new AtomicBoolean(false);
    cancellations.put(id,cancel);
    worker.execute(()->run(id,prompt,cancel));
    return id;
  }
  private void set(String id,String state,int revision,String sha,int triangles,String detail){
    ContentValues cv=new ContentValues();cv.put("state",state);cv.put("rev",revision);
    cv.put("sha",sha);cv.put("triangles",triangles);cv.put("detail",detail);
    cv.put("updated",System.currentTimeMillis());
    getWritableDatabase().update("jobs",cv,"id=?",new String[]{id});
  }
  private void run(String id,String prompt,AtomicBoolean cancel){
    try{
      set(id,"working",0,"",0,"Planning supported primitive geometry");
      for(int rev=1;rev<=2;rev++){
        if(cancel.get())throw new InterruptedException("Stop requested");
        set(id,"working",rev-1,"",0,"Building local source revision "+rev);
        byte[] obj=OfflineGeometry.generate(prompt,rev,cancel::get);
        if(cancel.get())throw new InterruptedException("Stop requested");
        MeshData mesh=MeshData.read(new ByteArrayInputStream(obj),"VQ offline revision "+rev);
        String hash=sha(obj);
        File dir=dir(), file=new File(dir,id+"-r"+rev+".obj");
        File temp=new File(dir,id+"-r"+rev+".tmp");
        try(FileOutputStream stream=new FileOutputStream(temp)){
          stream.write(obj);stream.getFD().sync();
        }
        if(!temp.renameTo(file))throw new IOException("Atomic local OBJ save failed");
        if(cancel.get())throw new InterruptedException("Stop requested");
        getWritableDatabase().beginTransaction();
        try{
          ContentValues row=new ContentValues();row.put("job",id);row.put("rev",rev);
          row.put("sha",hash);row.put("bytes",obj.length);
          row.put("triangles",mesh.triangles.length);
          getWritableDatabase().insertOrThrow("revisions",null,row);
          set(id,rev==2?"complete":"working",rev,hash,mesh.triangles.length,
              rev==2?"Saved detailed OBJ • ready for review":"Base OBJ saved • refining geometry locally");
          getWritableDatabase().setTransactionSuccessful();
        }finally{getWritableDatabase().endTransaction();}
      }
    }catch(InterruptedException ex){
      Snapshot last=get(id);set(id,"cancelled",last.rev,last.sha,last.triangles,"Stopped locally • previous model retained");
      Thread.currentThread().interrupt();
    }catch(Exception ex){
      Snapshot last=get(id);set(id,"failed",last.rev,last.sha,last.triangles,"Failed: "+ex.getMessage());
    }finally{cancellations.remove(id);}
  }
  public synchronized boolean stop(String id){
    if(!valid(id))return false;
    AtomicBoolean c=cancellations.get(id);
    if(c==null)return false;
    c.set(true);return true;
  }
  public synchronized Snapshot latest(){
    try(Cursor c=getReadableDatabase().rawQuery("SELECT id,prompt,shape,state,rev,sha,triangles,detail FROM jobs ORDER BY updated DESC LIMIT 1",null)){
      return c.moveToFirst()?read(c):Snapshot.empty();
    }
  }
  public synchronized Snapshot get(String id){
    if(!valid(id))return Snapshot.empty();
    try(Cursor c=getReadableDatabase().rawQuery("SELECT id,prompt,shape,state,rev,sha,triangles,detail FROM jobs WHERE id=?",new String[]{id})){
      return c.moveToFirst()?read(c):Snapshot.empty();
    }
  }
  private Snapshot read(Cursor c){
    return new Snapshot(c.getString(0),c.getString(1),c.getString(2),c.getString(3),
        c.getInt(4),c.getString(5),c.getInt(6),c.getString(7));
  }
  private static boolean valid(String id){return id!=null&&id.matches("[a-f0-9]{20}");}
  public synchronized byte[] load(Snapshot snap)throws Exception{
    if(snap==null||snap.rev<=0||!valid(snap.id)||!snap.sha.matches("[a-f0-9]{64}"))
      throw new FileNotFoundException("No generated local OBJ");
    File target=new File(dir(),snap.id+"-r"+snap.rev+".obj");
    if(!target.isFile()||target.length()>8*1024*1024)throw new FileNotFoundException("Missing local revision");
    ByteArrayOutputStream out=new ByteArrayOutputStream();
    try(InputStream in=new FileInputStream(target)){
      byte[] buf=new byte[8192];int n;
      while((n=in.read(buf))!=-1){if(out.size()+n>8*1024*1024)throw new IOException("Oversized OBJ");out.write(buf,0,n);}
    }
    byte[] bytes=out.toByteArray();
    if(!sha(bytes).equals(snap.sha))throw new SecurityException("Local geometry SHA-256 mismatch");
    return bytes;
  }
  public static final class Snapshot {
    public final String id,prompt,shape,state,sha,detail;
    public final int rev,triangles;
    Snapshot(String id,String p,String shape,String state,int rev,String sha,int t,String detail){
      this.id=id;prompt=p;this.shape=shape;this.state=state;this.rev=rev;this.sha=sha;triangles=t;this.detail=detail;
    }
    public static Snapshot empty(){return new Snapshot("","","","idle",0,"",0,"No local models yet");}
    public Bundle bundle(){
      Bundle out=new Bundle();
      out.putString("id",id);out.putString("prompt",prompt);out.putString("shape",shape);
      out.putString("state",state);out.putString("sha256",sha);out.putString("detail",detail);
      out.putInt("revision",rev);out.putInt("triangles",triangles);return out;
    }
  }
}