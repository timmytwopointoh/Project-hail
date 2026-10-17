package com.trioncompasitor.vqstudio;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public final class ForgeLang2SelfTest {
 private static void check(boolean pass,String message){if(!pass)throw new AssertionError(message);}
 public static void main(String[] ignored)throws Exception{
  String instructions="FORGE/2\nmodel watchman\n"+
    "part trunk box 0 1 0 1 .8 .5\n"+
    "part head capsule 0 0 0 .6 .7 .6\n"+
    "attach head trunk top .1\n"+
    "part arm_l capsule -.8 1 0 .2 .9 .2\n"+
    "mirror arm_l arm_r x\n"+
    "part halo ring 0 2 0 1 .13 1\n";
  ForgeSpec.Blueprint a=ForgeLang2.parse(instructions);
  check(a.parts.size()==5,"Named parts, attachments and symmetry expected");
  check(a.parts.get(1).y>1.8f,"Head was not placed on top of trunk");
  check(a.parts.get(3).x>0,"Mirror must generate reflected coordinates");
  byte[] detailed=ForgeSpec.build(a,2,()->false);
  String obj=new String(detailed,StandardCharsets.UTF_8);
  check(obj.contains("g halo"),"Torus must be new geometric vertices");
  check(obj.contains("g head"),"Capsule group missing");
  check(obj.split("\nf ").length>100,"Expected actual triangulated 3D construction");
  check(!Arrays.equals(detailed,ForgeSpec.build(a,1,()->false)),"Revisions must change topology");
  check(ForgeSpec.parse(a.serialize()).parts.size()==5,"Persisted instructions should replay");
  for(String request:new String[]{"a large tall robot with antenna","a wide bridge","a small wheel"}){
   ForgeSpec.Blueprint b=ForgeSpec.compile(request);
   check(!b.parts.isEmpty(),"No geometry built for "+request);
   check(ForgeSpec.build(b,2,()->false).length>300,"Empty mesh for "+request);
  }
  ForgeSpec.Blueprint bridge=ForgeSpec.compile("build a wide bridge");
  ForgeSpec.Part railL=null,railR=null,deck=null;
  for(ForgeSpec.Part part:bridge.parts){
    if(part.name.equals("railing_left"))railL=part;
    if(part.name.equals("railing_right"))railR=part;
    if(part.name.equals("deck"))deck=part;
  }
  check(railL!=null&&railR!=null&&deck!=null,"Bridge assembly pieces missing");
  check(railL.z<0&&railR.z>0,"Rails must occupy opposite deck edges");
  check(Math.abs(railL.x)<.001&&Math.abs(railR.x)<.001,"Rails must align with bridge length");
  check(railL.y-railL.h*.5f >= deck.y+deck.h*.5f-.04f,"Rails must rest above deck");
  ForgeSpec.Blueprint wheel=ForgeSpec.compile("build a small wheel");
  check(wheel.parts.get(0).type.equals("ring_z"),"Wheel rim must be upright");
  String wheelObj=new String(ForgeSpec.build(wheel,2,()->false),StandardCharsets.UTF_8);
  float ymin=100,ymax=-100;
  for(String line:wheelObj.split("\n")){
    if(line.startsWith("v ")){
      String[] v=line.split(" ");
      float y=Float.parseFloat(v[2]);
      ymin=Math.min(ymin,y);ymax=Math.max(ymax,y);
    }
  }
  check(ymax-ymin>.45f,"Wheel should have a tall vertical round silhouette");
  try{ForgeLang2.parse("FORGE/2\npart a box 0 0 0 1 1 1\nattach a absent top .1\n");
   throw new AssertionError("Invalid parent accepted");
  }catch(IllegalArgumentException expected){}
  try{ForgeLang2.parse("FORGE/2\npart a box 0 0 0 1 1 1\npart b box 0 0 0 1 1 1\nattach b a sideways .1\n");
   throw new AssertionError("Unknown relation accepted");
  }catch(IllegalArgumentException expected){}
  try{ForgeLang2.parse("FORGE/2\npart a box 0 0 0 1 1 1\npart b box 0 0 0 1 1 1\nattach b a top -2\n");
   throw new AssertionError("Negative gap accepted");
  }catch(IllegalArgumentException expected){}
  System.out.println("FORGE_2_ORIGINAL_RELATIONSHIP_GEOMETRY_PASS");
 }
}