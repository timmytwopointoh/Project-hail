package com.trioncompasitor.vqstudio;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
/** No Android or external asset fixtures. Compiles and exercises actual mesh geometry. */
public final class ForgeSpecSelfTest {
 public static void main(String[] args)throws Exception{
  String original="FORGE/1\nmodel clockwork_fox\n"+
    "part body ellipsoid 0 1 0 1.4 .7 .6\n"+
    "part ear_l taper -.45 1.65 0 .2 .5 .2\n"+
    "part ear_r taper .45 1.65 0 .2 .5 .2\n";
  ForgeSpec.Blueprint first=ForgeSpec.parse(original);
  if(first.parts.size()!=3)throw new AssertionError("Missing named parts");
  String source=new String(ForgeSpec.build(first,2,()->false),StandardCharsets.UTF_8);
  if(!source.contains("g body")||!source.contains("g ear_l")||!source.contains("f "))
    throw new AssertionError("No original grouped 3D triangles");
  if(!first.serialize().equals(ForgeSpec.parse(first.serialize()).serialize()))
    throw new AssertionError("FORGE/1 roundtrip was lossy");
  ForgeSpec.Blueprint widened=ForgeSpec.adapt(first,"Use previous construction technique, make it wider");
  if(widened.parts.get(0).w<=first.parts.get(0).w)
    throw new AssertionError("Technique memory did not affect geometry");
  if(Arrays.equals(ForgeSpec.build(widened,2,()->false),
                   ForgeSpec.build(first,2,()->false)))
    throw new AssertionError("Changed requested dimensions must produce new geometry");
  ForgeSpec.Blueprint natural=ForgeSpec.compile("Make a giant ancient tree with wide branches");
  if(natural.parts.size()<3||natural.parts.get(0).h<.5f)
    throw new AssertionError("Tree shape and proportions not interpreted");
  try{ForgeSpec.compile("Create a photorealistic dancing dragon");
   throw new AssertionError("Unknown concept was silently replaced");}
  catch(IllegalArgumentException expected){}
  try{ForgeSpec.parse("FORGE/1\nmodel bad\npart part1 box 0 0 0 -1 1 1\n");
   throw new AssertionError("Negative size accepted");}
  catch(IllegalArgumentException expected){}
  try{ForgeSpec.parse("FORGE/1\nmodel bad\npart part1 box 0 0 0 1 1 1\npart part1 box 1 0 0 1 1 1\n");
   throw new AssertionError("Duplicate part accepted");}
  catch(IllegalArgumentException expected){}
  try{ForgeSpec.build(first,2,()->true);throw new AssertionError("Stop ignored");}
  catch(IllegalStateException expected){}
  System.out.println("FORGE_SPEC_COMPILER_AND_REAL_GEOMETRY_PASS");
 }
}