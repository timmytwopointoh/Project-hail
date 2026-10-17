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