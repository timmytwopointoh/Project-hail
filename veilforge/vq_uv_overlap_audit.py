"""Fail-closed UV-space overlap audit for M30/M31 material baking.

Unlike texel raster checks, detects coincident-geometry stacking and
positive-area intersections smaller than a single output pixel.
Does not prove mip gutter, texel density, or artistic quality.
"""
import math


def _uv_triangles_overlap(a,b):
    """SAT: edge/corner contact is allowed; positive-area overlap is not."""
    for tri in (a,b):
        for i in range(3):
            p,q=tri[i],tri[(i+1)%3]
            axis=(p[1]-q[1],q[0]-p[0])
            length=math.hypot(*axis)
            if length<1e-14:
                raise ValueError("Degenerate UV triangle")
            axis=(axis[0]/length,axis[1]/length)
            x=[u[0]*axis[0]+u[1]*axis[1] for u in a]
            y=[u[0]*axis[0]+u[1]*axis[1] for u in b]
            if min(max(x),max(y))-max(min(x),min(y))<=1e-12:
                return False
    return True


def validate_unique_uv_atlas(rows):
    """Audit all candidate UV triangle pairs using a bounded spatial grid."""
    side=min(256,max(8,math.ceil(math.sqrt(len(rows)))))
    cells={};seen=set();visits=0
    for i,(_,uv,_,_) in enumerate(rows):
        x0=max(0,min(side-1,int(min(p[0] for p in uv)*side)))
        x1=max(0,min(side-1,int(max(p[0] for p in uv)*side)))
        y0=max(0,min(side-1,int(min(p[1] for p in uv)*side)))
        y1=max(0,min(side-1,int(max(p[1] for p in uv)*side)))
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                visits+=1
                if visits>2000000:
                    raise ValueError("UV audit cell budget exceeded; uniqueness unproven")
                bucket=cells.setdefault((x,y),[])
                for j in bucket:
                    pair=(j,i)
                    if pair in seen:continue
                    seen.add(pair)
                    if len(seen)>2000000:
                        raise ValueError("UV audit pair budget exceeded; uniqueness unproven")
                    if _uv_triangles_overlap(uv,rows[j][1]):
                        raise ValueError(f"Overlapping UV islands on triangles {j} and {i}")
                bucket.append(i)
    return {"triangles_checked":len(rows),"candidate_pairs_checked":len(seen),
            "cell_visits":visits,"positive_area_uv_overlap_rejected":True}
