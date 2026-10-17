package com.trioncompasitor.vqstudio;
import java.util.Arrays;

public final class VQLearningSelfTest {
  private static void check(boolean ok,String problem){if(!ok)throw new AssertionError(problem);}
  public static void main(String[] args) {
    String request="Create a floating observatory with a glass roof";
    VQPersonalizer first=new VQPersonalizer(1045L),other=new VQPersonalizer(91824L);
    try{VQActiveLearning.compile(request,"",first);throw new AssertionError("Missing question");}
    catch(VQActiveLearning.NeedsDetails expected){
      check(expected.question.contains("Which parts"),"Specific clarification not asked");
    }
    String description="base box 2 1 1 center; dome ellipsoid 1.3 .7 1.3 top";
    ForgeSpec.Blueprint candidate=VQActiveLearning.compile(request,description,first);
    check(candidate.parts.size()==2,"Parts not constructed");
    byte[] obj=ForgeSpec.build(candidate,2,()->false);
    check(obj.length>1000,"Actual triangles not constructed");
    check(Arrays.equals(obj,ForgeSpec.build(VQActiveLearning.compile(request,description,first),2,()->false)),
       "Same private profile does not reproduce geometry");
    ForgeSpec.Blueprint second=VQActiveLearning.compile(request,description,other);
    check(!Arrays.equals(obj,ForgeSpec.build(second,2,()->false)),
       "Different installations must be allowed distinctive local styles");
    double before=first.prediction(request)[0];
    first.learn(request,"wider");
    check(first.prediction(request)[0]>before,"Correction did not update neural preference");
    check(VQPersonalizer.load(first.save()).save().equals(first.save()),"Style weights did not roundtrip");
    double old=first.prediction(request)[0];
    try{first.learn(request,"make it magic");throw new AssertionError("Unbounded feedback accepted");}
    catch(IllegalArgumentException expected){}
    check(old==first.prediction(request)[0],"Invalid feedback mutated profile");
    try{VQActiveLearning.fromParts(request,"base box NaN 1 2 center");
      throw new AssertionError("NaN geometry accepted");}
    catch(IllegalArgumentException expected){}
    try{VQActiveLearning.fromParts(request,"body cylinder 2 1 1 center; head ellipsoid 1 1 1 top; head box 1 1 1 top");
      throw new AssertionError("Duplicate part accepted");}
    catch(IllegalArgumentException expected){}
    System.out.println("VQ_ON_DEVICE_QUESTIONS_AND_TRAINABLE_STYLE_PASS mesh_bytes="+obj.length+
      " owner_feedback=trained privacy=local_only");
  }
}
