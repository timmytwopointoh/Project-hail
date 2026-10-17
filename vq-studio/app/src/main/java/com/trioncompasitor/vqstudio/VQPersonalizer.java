package com.trioncompasitor.vqstudio;

import java.util.*;

/**
 * Tiny, device-owned 5->4->2 trainable neural preference mapper.
 * Learns ONLY from explicit owner corrections; it is not an object-recognition
 * network or a fine-tune of Trion's separate Qwen language model.
 * All parameters remain in private, offline app preferences.
 */
public final class VQPersonalizer {
  private final double[][] hidden=new double[4][5];
  private final double[][] output=new double[2][5];
  public VQPersonalizer(long privateSeed){
    Random r=new Random(privateSeed);
    for(double[] row:hidden)for(int i=0;i<row.length;i++)row[i]=(r.nextDouble()-.5)*.55;
    for(double[] row:output)for(int i=0;i<row.length;i++)row[i]=(r.nextDouble()-.5)*.45;
  }
  private VQPersonalizer(){ }
  private static double[] features(String prompt){
    String s=prompt.toLowerCase(Locale.ROOT);
    return new double[]{1,
      test(s,"tree|leaf|flower|plant|mushroom|animal|fox|dog|body|organic")?1:0,
      test(s,"robot|machine|wheel|bridge|engine|metal|vehicle|gear")?1:0,
      test(s,"tall|high|long|tower|slender")?1:0,
      test(s,"wide|broad|thick|heavy")?1:0};
  }
  private static boolean test(String s,String words){
    return java.util.regex.Pattern.compile("\\b("+words+")\\b").matcher(s).find();
  }
  private static double dot(double[] a,double[] b){
    double sum=0;for(int i=0;i<a.length;i++)sum+=a[i]*b[i];return sum;
  }
  private double[] hidden(double[] x){
    double[] h=new double[5];h[0]=1;
    for(int i=0;i<4;i++)h[i+1]=Math.tanh(dot(hidden[i],x));
    return h;
  }
  public double[] prediction(String prompt){
    double[] h=hidden(features(prompt));
    return new double[]{Math.tanh(dot(output[0],h)),Math.tanh(dot(output[1],h))};
  }
  /** Geometry personalization stays +/-15%, and never edits explicit FORGE plans. */
  public ForgeSpec.Blueprint shape(ForgeSpec.Blueprint base,String prompt){
    if(prompt.startsWith("FORGE/1\n")||prompt.startsWith("FORGE/2\n"))return base;
    double[] y=prediction(prompt);
    float width=(float)(1+.15*y[0]),height=(float)(1+.15*y[1]);
    ArrayList<ForgeSpec.Part> parts=new ArrayList<>();
    for(ForgeSpec.Part p:base.parts)
      parts.add(new ForgeSpec.Part(p.name,p.type,p.x*width,p.y*height,p.z*width,
        p.w*width,p.h*height,p.d*width));
    return new ForgeSpec.Blueprint(base.title,parts,
      base.explanation+"; tiny local owner-specific geometry style; approval pending");
  }
  /** Lightweight SGD, bounded and repeatable. Correction is an explicit user action. */
  public void learn(String prompt,String feedback){
    String s=feedback.toLowerCase(Locale.ROOT).trim();
    final int axis;final double target;
    switch(s){
      case "wider": case "broader":axis=0;target=.9;break;
      case "slimmer": case "narrower":axis=0;target=-.9;break;
      case "taller": case "longer":axis=1;target=.9;break;
      case "shorter":axis=1;target=-.9;break;
      default:throw new IllegalArgumentException("Choose wider, slimmer, taller, or shorter");
    }
    double[] x=features(prompt);
    for(int epoch=0;epoch<48;epoch++){
      double[] h=hidden(x);
      double y=Math.tanh(dot(output[axis],h));
      double grad=(target-y)*(1-y*y);
      double[] previous=output[axis].clone();
      for(int j=0;j<5;j++)output[axis][j]=clamp(output[axis][j]+.035*grad*h[j]);
      for(int j=0;j<4;j++){
        double derivative=grad*previous[j+1]*(1-h[j+1]*h[j+1]);
        for(int k=0;k<5;k++)hidden[j][k]=clamp(hidden[j][k]+.035*derivative*x[k]);
      }
    }
  }
  private static double clamp(double d){return Math.max(-2,Math.min(2,d));}
  public String save(){
    StringBuilder b=new StringBuilder("VQSTYLE/1");
    for(double[] row:hidden)for(double v:row)b.append(' ').append(Double.toString(v));
    for(double[] row:output)for(double v:row)b.append(' ').append(Double.toString(v));
    return b.toString();
  }
  public static VQPersonalizer load(String source){
    if(source==null||source.length()>1500)throw new IllegalArgumentException("Invalid private style profile");
    String[] fields=source.split(" ");
    if(fields.length!=31||!fields[0].equals("VQSTYLE/1"))
      throw new IllegalArgumentException("Unsupported style profile");
    VQPersonalizer net=new VQPersonalizer();
    int index=1;
    try {
      for(double[] row:net.hidden)for(int i=0;i<row.length;i++){
        double d=Double.parseDouble(fields[index++]);
        if(!Double.isFinite(d)||Math.abs(d)>2)throw new IllegalArgumentException("Bad weights");
        row[i]=d;
      }
      for(double[] row:net.output)for(int i=0;i<row.length;i++){
        double d=Double.parseDouble(fields[index++]);
        if(!Double.isFinite(d)||Math.abs(d)>2)throw new IllegalArgumentException("Bad weights");
        row[i]=d;
      }
    }catch(NumberFormatException error){throw new IllegalArgumentException("Corrupted weights",error);}
    return net;
  }
}
