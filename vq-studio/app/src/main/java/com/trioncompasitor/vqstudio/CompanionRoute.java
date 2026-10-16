package com.trioncompasitor.vqstudio;

import android.content.Context;
import android.content.pm.ProviderInfo;
import android.net.Uri;
import java.io.IOException;

/** Strict allowlist for the two supported Trion editions.
 * The selected edition is remembered when Trion opens VQ Studio, so
 * stable and preview builds never accidentally swap job/control contexts.
 */
public final class CompanionRoute {
    public static final String STABLE="com.trioncompasitor.assistant";
    public static final String PREVIEW="com.trioncompasitor.assistant.deltaeditionxxx";
    private static final String PREFS="vq-trion-companion";
    private CompanionRoute(){}
    public static boolean allowed(String value){
        return STABLE.equals(value)||PREVIEW.equals(value);
    }
    public static void remember(Context context,String value){
        if(allowed(value))context.getSharedPreferences(PREFS,0).edit()
            .putString("last_trion_package",value).apply();
    }
    public static String trionPackage(Context context)throws IOException{
        String preferred=context.getSharedPreferences(PREFS,0)
            .getString("last_trion_package","");
        String[] candidates=new String[]{preferred,PREVIEW,STABLE};
        for(String pkg:candidates){
            if(!allowed(pkg))continue;
            String authority=pkg+".vq.snapshots";
            ProviderInfo info=context.getPackageManager()
                .resolveContentProvider(authority,0);
            if(info!=null&&pkg.equals(info.packageName)
               &&"com.trioncompasitor.assistant.VQLiveSnapshotProvider".equals(info.name))
                return pkg;
        }
        throw new IOException("Install a Trion edition with the VQ bridge enabled");
    }
    public static Uri provider(Context context)throws IOException{
        return Uri.parse("content://"+trionPackage(context)+".vq.snapshots");
    }
}