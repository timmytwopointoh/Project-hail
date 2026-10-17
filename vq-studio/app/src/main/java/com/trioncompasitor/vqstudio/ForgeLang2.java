package com.trioncompasitor.vqstudio;

import java.util.*;

/**
 * FORGE/2 compiles relations and symmetry into an explicit, validated FORGE
 * blueprint. All shapes are generated algorithmically at build time.
 *
 * FORGE/2
 * model antenna_bot
 * part body box 0 1 0 1 .9 .55
 * part head capsule 0 1.8 0 .6 .65 .55
 * attach head body top 0.05
 * part left_eye ellipsoid -.17 0 0 .1 .12 .09
 * attach left_eye head front 0.20
 * mirror left_eye right_eye x
 *
 * Operations are sequential: a part must exist before it can be attached or
 * mirrored. No arbitrary code, assets, file references, or expression eval.
 */
public final class ForgeLang2 {
  private ForgeLang2(){}
  private static boolean word(String text,String words){
    return text.matches("(?s).*\\b("+words+")\\b.*");
  }
  public static boolean isExpandedFamily(String request){
    String s=request.toLowerCase(Locale.ROOT);
    return word(s,"robot|android|automaton|bridge|wheel|tire");
  }
  private static String ident(String input){
    if(!input.matches("[A-Za-z][A-Za-z0-9_]{0,39}"))
      throw new IllegalArgumentException("Invalid named part: "+input);
    return input;
  }
  private static float number(String text){
    float v;
    try{v=Float.parseFloat(text);}catch(NumberFormatException e){
      throw new IllegalArgumentException("Invalid spatial offset: "+text);
    }
    if(!Float.isFinite(v)||v<0||v>5)
      throw new IllegalArgumentException("Attachment gap must be between 0 and 5 meters");
    return v;
  }
  public static ForgeSpec.Blueprint parse(String source){
    if(source==null||source.length()>5000||!source.startsWith("FORGE/2\n"))
      throw new IllegalArgumentException("Expected FORGE/2 document under 5000 characters");
    LinkedHashMap<String,ForgeSpec.Part> parts=new LinkedHashMap<>();
    String title="untitled";
    String[] lines=source.split("\\r?\\n");
    for(int index=1;index<lines.length;index++){
      String line=lines[index].trim();
      if(line.isEmpty()||line.startsWith("#"))continue;
      String[] p=line.split("\\s+");
      if("model".equals(p[0])){
        if(p.length!=2)throw new IllegalArgumentException("Model requires one identifier");
        title=ident(p[1]);continue;
      }
      if("part".equals(p[0])){
        if(p.length!=9)throw new IllegalArgumentException("part NAME TOOL X Y Z WIDTH HEIGHT DEPTH");
        if(parts.size()>=ForgeSpec.MAX_PARTS)throw new IllegalArgumentException("Model part budget exceeded");
        String name=ident(p[1]);
        if(parts.containsKey(name))throw new IllegalArgumentException("Duplicate part: "+name);
        ForgeSpec.Part part=ForgeSpec.parse("FORGE/1\nmodel isolated\n"+line+"\n").parts.get(0);
        parts.put(name,part);continue;
      }
      if("mirror".equals(p[0])){
        if(p.length!=4||(!p[3].equals("x")&&!p[3].equals("z")))
          throw new IllegalArgumentException("mirror SOURCE NEWNAME x|z");
        ForgeSpec.Part from=parts.get(p[1]);String newName=ident(p[2]);
        if(from==null||parts.containsKey(newName))throw new IllegalArgumentException("Mirror source missing or destination already exists");
        if(parts.size()>=ForgeSpec.MAX_PARTS)throw new IllegalArgumentException("Model part budget exceeded");
        float x=p[3].equals("x")?-from.x:from.x;
        float z=p[3].equals("z")?-from.z:from.z;
        parts.put(newName,new ForgeSpec.Part(newName,from.type,x,from.y,z,from.w,from.h,from.d));
        continue;
      }
      if("attach".equals(p[0])){
        if(p.length!=5)throw new IllegalArgumentException("attach CHILD PARENT top|bottom|left|right|front|back GAP");
        ForgeSpec.Part child=parts.get(p[1]),parent=parts.get(p[2]);
        if(child==null||parent==null||child==parent)
          throw new IllegalArgumentException("Attachment must reference distinct existing parts");
        float gap=number(p[4]),x=child.x,y=child.y,z=child.z;
        switch(p[3]){
          case "top": x=parent.x+child.x;y=parent.y+(parent.h+child.h)*.5f+gap;z=parent.z+child.z;break;
          case "bottom": x=parent.x+child.x;y=parent.y-(parent.h+child.h)*.5f-gap;z=parent.z+child.z;break;
          case "left": x=parent.x-(parent.w+child.w)*.5f-gap;y=parent.y+child.y;z=parent.z+child.z;break;
          case "right": x=parent.x+(parent.w+child.w)*.5f+gap;y=parent.y+child.y;z=parent.z+child.z;break;
          case "front": x=parent.x+child.x;y=parent.y+child.y;z=parent.z+(parent.d+child.d)*.5f+gap;break;
          case "back": x=parent.x+child.x;y=parent.y+child.y;z=parent.z-(parent.d+child.d)*.5f-gap;break;
          default:throw new IllegalArgumentException("Unknown attachment face: "+p[3]);
        }
        if(Math.abs(x)>50||Math.abs(y)>50||Math.abs(z)>50)
          throw new IllegalArgumentException("Attachment exceeds build space");
        parts.put(child.name,new ForgeSpec.Part(child.name,child.type,x,y,z,child.w,child.h,child.d));
        continue;
      }
      throw new IllegalArgumentException("Unsupported FORGE/2 command: "+p[0]);
    }
    if(parts.isEmpty())throw new IllegalArgumentException("A model needs a geometric part");
    // The persisted technique is fully resolved. It may be replayed on devices
    // with the FORGE/1 geometry engine (including capsule and ring support).
    return new ForgeSpec.Blueprint(title,new ArrayList<>(parts.values()),
       "FORGE/2 relationships resolved to original named geometry, no stored meshes");
  }
  private static float scale(String s){
    return word(s,"small|tiny|miniature")?.7f:word(s,"huge|giant|large")?1.35f:1f;
  }
  public static ForgeSpec.Blueprint compile(String request){
    if(request==null||request.trim().isEmpty()||request.length()>5000)
      throw new IllegalArgumentException("Invalid FORGE/2 request");
    if(request.startsWith("FORGE/2\n"))return parse(request);
    String s=request.toLowerCase(Locale.ROOT);
    float m=scale(s);
    boolean longish=word(s,"tall|long|elongated");
    boolean wide=word(s,"wide|broad");
    StringBuilder plan=new StringBuilder("FORGE/2\n");
    if(word(s,"robot|android|automaton")){
      plan.append("model procedural_robot\n");
      plan.append(String.format(Locale.ROOT,"part torso box 0 %.3f 0 %.3f %.3f %.3f\n",
       1.15f*m, (wide?1.15f:.85f)*m, 1.1f*m,.52f*m));
      plan.append(String.format(Locale.ROOT,"part head capsule 0 0 0 %.3f %.3f %.3f\n",
       .6f*m,.64f*m,.54f*m));
      plan.append("attach head torso top 0.04\n");
      plan.append(String.format(Locale.ROOT,"part arm_left capsule %.3f 1.12 0 %.3f %.3f %.3f\n",
       -.72f*m,.23f*m,(longish?1.7f:1.08f)*m,.22f*m));
      plan.append("mirror arm_left arm_right x\n");
      plan.append(String.format(Locale.ROOT,"part leg_left capsule %.3f %.3f 0 %.3f %.3f %.3f\n",
       -.24f*m,.44f*m,.28f*m,.88f*m,.28f*m));
      plan.append("mirror leg_left leg_right x\n");
      if(word(s,"antenna|antennae")){
        plan.append(String.format(Locale.ROOT,"part antenna capsule 0 0 0 %.3f %.3f %.3f\n",
         .10f*m,.4f*m,.10f*m));
        plan.append("attach antenna head top 0.0\n");
      }
    }else if(word(s,"bridge")){
      plan.append("model procedural_bridge\n");
      plan.append(String.format(Locale.ROOT,"part deck box 0 %.3f 0 %.3f %.3f %.3f\n",
       .85f*m,(longish?5.6f:3.5f)*m,.18f*m,(wide?2.1f:1.3f)*m));
      plan.append(String.format(Locale.ROOT,"part support_left box %.3f %.3f 0 %.3f %.3f %.3f\n",
       -1.15f*m,.38f*m,.36f*m,.76f*m,.36f*m));
      plan.append("mirror support_left support_right x\n");
      plan.append(String.format(Locale.ROOT,"part railing_left box %.3f %.3f 0 %.3f %.3f %.3f\n",
       -.69f*m,1.25f*m,(longish?5.6f:3.5f)*m,.56f*m,.10f*m));
      plan.append("mirror railing_left railing_right x\n");
    }else if(word(s,"wheel|tire")){
      plan.append("model procedural_wheel\n");
      plan.append(String.format(Locale.ROOT,"part rim ring 0 %.3f 0 %.3f %.3f %.3f\n",
       .6f*m,(wide?1.5f:1.1f)*m,.16f*m,(wide?1.5f:1.1f)*m));
      plan.append(String.format(Locale.ROOT,"part hub cylinder 0 %.3f 0 %.3f %.3f %.3f\n",
       .6f*m,.25f*m,.12f*m,.25f*m));
    }else{
      throw new IllegalArgumentException("FORGE/2 automatic planning supports robots, bridges and wheels. Other objects need named part instructions, not copied assets.");
    }
    return parse(plan.toString());
  }
}
