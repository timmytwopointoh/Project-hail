package com.trioncompasitor.vqstudio;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
public final class VQProtocol {
  public static final String REPO="timmytwopointoh/Project-hail";
  public static final String BRANCH="app/vq-studio-companion-v1";
  public static final String WORKFLOW="vq-studio-jobs.yml";
  public static final String TRION_PACKAGE="com.trioncompasitor.assistant";
  public static final String TRION_BRIDGE=TRION_PACKAGE+".VQBridgeActivity";
  public static final String STUDIO_PACKAGE="com.trioncompasitor.vqstudio";
  public static final String SHOW_JOB=STUDIO_PACKAGE+".SHOW_JOB";
  public static final List<String> MODELS=Arrays.asList(
      "ancient_tree","ceremonial_sword","cargo_cart","treasure_chest",
      "ancient_gate_standard","ancient_gate_mobile","forest_tree_mobile",
      "rolling_terrain");
  private VQProtocol(){}
  public static String newRequestId(){return UUID.randomUUID().toString().replace("-","").substring(0,16);}
  public static String direction(String input){
    if(input==null)return "";
    String s=input.trim().replaceAll("[\\p{Cntrl}&&[^\\n\\t]]","");
    if(s.length()>700)throw new IllegalArgumentException("Direction limit is 700 characters");
    return s;
  }
  public static boolean validRequestId(String s){return s!=null&&s.matches("[a-f0-9]{16}");}
  public static boolean validRunId(String s){return s!=null&&s.matches("[1-9][0-9]{0,17}");}
}