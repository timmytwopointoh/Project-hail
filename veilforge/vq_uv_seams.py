"""Read-only UV seam audit for source-derived VQ OBJ meshes."""
from collections import defaultdict
from engine import read_obj

def seam_counts(path):
    verts,uv,_,faces=read_obj(path)
    edges=defaultdict(list)
    for face in faces:
        if any(ref[1] is None for ref in face):
            raise ValueError("Missing source UV coordinates")
        for j in range(3):
            a,b=face[j],face[(j+1)%3]
            xyz=tuple(sorted((tuple(round(x,6) for x in verts[a[0]][:3]),
                              tuple(round(x,6) for x in verts[b[0]][:3]))))
            uv_pair=tuple(sorted((tuple(round(x,8) for x in uv[a[1]][:2]),
                                  tuple(round(x,8) for x in uv[b[1]][:2]))))
            edges[xyz].append(uv_pair)
    seam=shared=0
    for pairs in edges.values():
        if len(pairs)>2:raise ValueError("Nonmanifold UV edge")
        if len(pairs)==2:
            if pairs[0]==pairs[1]:shared+=1
            else:seam+=1
    return {"seam_edges":seam,"continuous_edges":shared}
