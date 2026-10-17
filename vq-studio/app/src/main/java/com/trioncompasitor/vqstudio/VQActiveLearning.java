package com.trioncompasitor.vqstudio;

import java.util.*;
/**
 * Targeted clarification -> a real FORGE/1 blueprint.
 * Never claims an unknown noun was recognized from its name.
 * The user's main-part description is a NEW construction rule, not an asset.
 */
public final class VQActiveLearning {
  private VQActiveLearning(){}
  public static final class NeedsDetails extends IllegalArgumentException{
    public final String question;
    NeedsDetails(String question){super("Additional construction knowledge required");this.question=question;}
  }
  public static String question(String prompt){
    String s=prompt.toLowerCase(Locale.ROOT);
    String kind=s.matches("(?s).*\\b(animal|creature|dragon|person|character|human)\\b.*")
      ?"body, head, limbs and distinctive features"
      :s.matches("(?s).*\\b(armor|clothing|helmet|suit)\\b.*")
      ?"main panels, joints and decorative pieces"
      :"the main structural parts and how they connect";
    return "I can build original geometry for this. To learn "+kind+
      ", describe 2-8 parts as NAME SHAPE WIDTH HEIGHT DEPTH PLACEMENT in meters, "+
      "separated by semicolons. Shapes: box, ellipsoid, cylinder, taper, capsule or ring. "+
      "Placement: top, left, right, front, back, bottom, or center. "+
      "Example: base box 2 1 1 center; dome ellipsoid 1.3 .7 1.3 top. "+
      "Which parts should I construct?";
  }
  public static ForgeSpec.Blueprint compile(String prompt,String details,
                                             VQPersonalizer personal){
    if(prompt==null||prompt.trim().isEmpty()||prompt.length()>5000)
      throw new IllegalArgumentException("Describe the object in up to 5000 characters");
    if(personal==null)throw new IllegalArgumentException("Missing local style state");
    if(details!=null&&!details.trim().isEmpty())
      return personal.shape(fromParts(prompt,details),prompt);
    try{return personal.shape(ForgeSpec.compile(prompt),prompt);}
    catch(IllegalArgumentException unknown) {
      if(prompt.startsWith("FORGE/1")||prompt.startsWith("FORGE/2"))throw unknown;
      throw new NeedsDetails(question(prompt));
    }
  }
  public static ForgeSpec.Blueprint fromParts(String prompt,String answer){
    if(answer==null||answer.length()>2200)throw new IllegalArgumentException("Too much detail");
    String[] rows=answer.trim().split(";",-1);
    if(rows.length<1||rows.length>12)throw new IllegalArgumentException("Give 1-12 separated parts");
    String name=prompt.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+","_");
    if(name.isEmpty()||!Character.isLetter(name.charAt(0)))name="new_object";
    if(name.length()>39)name=name.substring(0,39);
    StringBuilder b=new StringBuilder("FORGE/1\nmodel ").append(name).append('\n');
    double x=0,y=0,z=0; double lastW=0,lastH=0,lastD=0;
    Set<String> used=new HashSet<>();
    for(int i=0;i<rows.length;i++){
      String[] f=rows[i].trim().toLowerCase(Locale.ROOT).split("\\s+");
      if(f.length!=5&&f.length!=6)
        throw new IllegalArgumentException("Part "+(i+1)+": use NAME SHAPE WIDTH HEIGHT DEPTH [PLACE]");
      if(!f[0].matches("[a-z][a-z0-9_]{0,31}")||!used.add(f[0]))
        throw new IllegalArgumentException("Use unique, simple part names");
      if(!Arrays.asList("box","ellipsoid","cylinder","taper","capsule","ring","ring_z").contains(f[1]))
        throw new IllegalArgumentException("Part "+f[0]+": choose a supported shape");
      double w=length(f[2]),h=length(f[3]),d=length(f[4]);
      if(i==0){x=0;y=h/2;z=0;}
      else{
        String place=f.length==6?f[5]:"top";
        switch(place){
          case "center":break;
          case "top":y+=(lastH+h)*.48;break;
          case "bottom":y-=(lastH+h)*.48;break;
          case "left":x-=(lastW+w)*.48;break;
          case "right":x+=(lastW+w)*.48;break;
          case "front":z+=(lastD+d)*.48;break;
          case "back":z-=(lastD+d)*.48;break;
          default:throw new IllegalArgumentException("Use top, bottom, left, right, front, back or center");
        }
      }
      if(Math.max(Math.abs(x),Math.max(Math.abs(y),Math.abs(z)))>25)
        throw new IllegalArgumentException("Requested assembly exceeds safe dimensions");
      b.append(String.format(Locale.ROOT,"part %s %s %.4f %.4f %.4f %.4f %.4f %.4f\n",
        f[0],f[1],x,y,z,w,h,d));
      lastW=w;lastH=h;lastD=d;
    }
    return ForgeSpec.parse(b.toString());
  }
  private static double length(String v){
    final double n;
    try{n=Double.parseDouble(v);}catch(NumberFormatException ex){
      throw new IllegalArgumentException("Use dimensions in meters",ex);
    }
    if(!Double.isFinite(n)||n<.02||n>10)throw new IllegalArgumentException("Size must be 0.02-10 meters");
    return n;
  }
}
