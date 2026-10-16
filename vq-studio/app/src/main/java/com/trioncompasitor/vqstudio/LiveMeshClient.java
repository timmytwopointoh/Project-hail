package com.trioncompasitor.vqstudio;

import android.content.*;
import android.net.Uri;
import android.os.Bundle;
import java.io.*;
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.util.Locale;

/** Caller of Trion's UID-checked provider. NO GitHub token in VQ Studio. */
public final class LiveMeshClient {
    private LiveMeshClient(){}
    public static final class Snapshot {
        public final String requestId,runId,sha,stage,asset;
        public final int sequence,triangles;
        public final MeshData mesh;
        Snapshot(String requestId,String runId,String sha,String stage,String asset,
                 int sequence,int triangles,MeshData mesh){
            this.requestId=requestId;this.runId=runId;this.sha=sha;this.stage=stage;
            this.asset=asset;this.sequence=sequence;this.triangles=triangles;this.mesh=mesh;
        }
        public String identity(){return requestId+":"+runId+":"+sequence+":"+sha;}
    }
    public static Snapshot latest(Context app,String requestId,String runId)throws Exception{
        return latest(app,requestId,runId,null);
    }
    /** The already-loaded hash is checked before opening or parsing an OBJ.
     * Unchanged revisions use a tiny metadata response, not another mesh copy.
     */
    public static Snapshot latest(Context app,String requestId,String runId,
                                  String alreadyLoaded)throws Exception{
        if(!VQProtocol.validRequestId(requestId)||!VQProtocol.validRunId(runId))
            throw new IOException("No verified model run to follow yet");
        Bundle request=new Bundle();
        request.putString("request_id",requestId);
        request.putString("run_id",runId);
        Bundle response;
        try{response=app.getContentResolver().call(CompanionRoute.provider(app),"latest",null,request);}
        catch(IllegalArgumentException e){throw new IOException(
           "Install the VQ-enabled Trion companion and connect GitHub",e);}
        if(response!=null&&"available".equals(response.getString("state",""))){
            String sha=response.getString("sha256","");
            int sequence=response.getInt("sequence",0);
            String identity=requestId+":"+runId+":"+sequence+":"+sha;
            if(sha.matches("[a-f0-9]{64}")&&sequence>=1&&sequence<=2
               &&identity.equals(alreadyLoaded))return null;
        }
        return readVerifiedResponse(app,requestId,runId,response);
    }
    /** Explicit, debug-only, paired emulator data-path check. */
    public static Snapshot pairedTestFixture(Context app,int revision)throws Exception{
        if((app.getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE)==0)throw new SecurityException("Paired test not available in production");
        if(revision!=1&&revision!=2)throw new IOException("Unknown test revision");
        Bundle args=new Bundle();
        args.putInt("revision",revision);
        Bundle result=app.getContentResolver().call(CompanionRoute.provider(app),"debug_fixture",null,args);
        return readVerifiedResponse(app,"eeeeeeeeeeeeeeee","999999999",result);
    }
    private static Snapshot readVerifiedResponse(Context app,String requestId,
                                                 String runId,Bundle response)throws Exception{
        if(response==null)throw new IOException("Trion model provider is unavailable");
        String state=response.getString("state","");
        if("no_verified_snapshot_yet".equals(state))return null;
        if(!"available".equals(state))
            throw new IOException(response.getString("message","No verified worker mesh available"));
        String sha=response.getString("sha256","");
        String uri=response.getString("uri","");
        int sequence=response.getInt("sequence",0),triangles=response.getInt("triangles",0);
        String stage=response.getString("quality_stage","");
        if(!sha.matches("[a-f0-9]{64}")||
           !(sequence==1&&"geometry_integrity".equals(stage)||
             sequence==2&&"technical_review".equals(stage))||
           triangles<=0||triangles>120000)
            throw new IOException("Trion returned an invalid revision proof");
        Uri source=Uri.parse(uri);
        if(!"content".equals(source.getScheme())||
           !CompanionRoute.provider(app).getAuthority().equals(source.getAuthority())||
           !("/mesh/"+sha).equals(source.getPath()))
            throw new IOException("VQ model URI is not the authenticated local provider");
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        MeshData mesh;
        try(InputStream sourceStream=app.getContentResolver().openInputStream(source)){
            if(sourceStream==null)throw new IOException("Verified mesh stream missing");
            try(DigestInputStream checked=new DigestInputStream(sourceStream,digest)){
                mesh=MeshData.read(checked,"VQ "+response.getString("source_asset","worker model")+
                     " / "+stage+" / rev "+sequence);
            }
        }
        StringBuilder actual=new StringBuilder();
        for(byte b:digest.digest())actual.append(String.format(Locale.ROOT,"%02x",b&255));
        if(!sha.equals(actual.toString()))
            throw new IOException("VQ rejected changed or corrupted mesh content");
        if(mesh.triangles.length!=triangles)
            throw new IOException("Model triangle count differs from signed-in run metadata");
        return new Snapshot(requestId,runId,sha,stage,
                response.getString("source_asset","worker asset"),
                sequence,triangles,mesh);
    }
}