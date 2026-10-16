package com.trioncompasitor.vqstudio;
import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.os.*;
import java.io.*;
import java.util.*;

/** Android IPC boundary: accepts commands ONLY from installed Trion Assistant. */
public final class OfflineProvider extends ContentProvider {
  public static final String AUTHORITY="com.trioncompasitor.vqstudio.repository";
  @Override public boolean onCreate(){return true;}
  private void allowTrion(){
    int uid=Binder.getCallingUid();
    String[] names=getContext().getPackageManager().getPackagesForUid(uid);
    if(names==null||!Arrays.asList(names).contains("com.trioncompasitor.assistant"))
      throw new SecurityException("Only Trion Assistant may control VQ's private repository");
  }
  @Override public Bundle call(String method,String arg,Bundle extra){
    allowTrion();
    OfflineRepository r=OfflineRepository.of(getContext());
    Bundle out=new Bundle();
    switch(method){
      case "submit":
        String prompt=extra==null?"":extra.getString("prompt","");
        try{
          String id=r.submit(prompt);out.putString("state","queued");out.putString("id",id);
          return out;
        }catch(Exception e){out.putString("state","error");out.putString("message",e.getMessage());return out;}
      case "status":
        String key=extra==null?"":extra.getString("id","");
        return (key.isEmpty()?r.latest():r.get(key)).bundle();
      case "stop":
        String id=extra==null?"":extra.getString("id","");
        out.putBoolean("requested",r.stop(id));return out;
      default:throw new UnsupportedOperationException("Unsupported local VQ operation");
    }
  }
  @Override public android.os.ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{
    allowTrion();
    if(!"r".equals(mode)||uri==null||!AUTHORITY.equals(uri.getAuthority()))
      throw new FileNotFoundException("Only read-only VQ source is supported");
    java.util.List<String> parts=uri.getPathSegments();
    if(parts.size()!=3||!"mesh".equals(parts.get(0))||
       !parts.get(1).matches("[a-f0-9]{20}")||
       !parts.get(2).matches("[12]"))
      throw new FileNotFoundException("Unknown private asset revision");
    String id=parts.get(1);
    int rev=Integer.parseInt(parts.get(2));
    OfflineRepository repo=OfflineRepository.of(getContext());
    OfflineRepository.Snapshot snapshot=repo.get(id);
    if(snapshot.id.isEmpty()||snapshot.rev!=rev||!snapshot.sha.matches("[a-f0-9]{64}"))
      throw new FileNotFoundException("Source revision not approved for transfer");
    // Read and digest-verify the exact saved local OBJ before transferring it.
    try{
      byte[] verified=repo.load(snapshot);
      if(verified.length>256*1024)throw new FileNotFoundException("Use bounded mobile model export");
      File path=new File(new File(getContext().getFilesDir(),"model_repository"),id+"-r"+rev+".obj");
      return android.os.ParcelFileDescriptor.open(path,android.os.ParcelFileDescriptor.MODE_READ_ONLY);
    }catch(FileNotFoundException e){throw e;}
     catch(Exception e){throw new FileNotFoundException("VQ model integrity verification failed");}
  }
  @Override public Cursor query(Uri uri,String[] p,String s,String[] a,String o){allowTrion();throw new UnsupportedOperationException();}
  @Override public String getType(Uri uri){allowTrion();return null;}
  @Override public Uri insert(Uri uri,ContentValues v){allowTrion();throw new UnsupportedOperationException();}
  @Override public int update(Uri uri,ContentValues v,String s,String[] a){allowTrion();throw new UnsupportedOperationException();}
  @Override public int delete(Uri uri,String s,String[] a){allowTrion();throw new UnsupportedOperationException();}
}