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
    boolean stable=names!=null&&Arrays.asList(names)
      .contains("com.trioncompasitor.assistant");
    boolean preview=names!=null&&Arrays.asList(names)
      .contains("com.trioncompasitor.assistant.deltaeditionxxx");
    boolean debug=(getContext().getApplicationInfo().flags&
      android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE)!=0;
    if(!stable&&!(debug&&preview))
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
    throw new FileNotFoundException("Raw 3D mesh files are private to VQ Studio");
  }
  @Override public Cursor query(Uri uri,String[] p,String s,String[] a,String o){allowTrion();throw new UnsupportedOperationException();}
  @Override public String getType(Uri uri){allowTrion();return null;}
  @Override public Uri insert(Uri uri,ContentValues v){allowTrion();throw new UnsupportedOperationException();}
  @Override public int update(Uri uri,ContentValues v,String s,String[] a){allowTrion();throw new UnsupportedOperationException();}
  @Override public int delete(Uri uri,String s,String[] a){allowTrion();throw new UnsupportedOperationException();}
}