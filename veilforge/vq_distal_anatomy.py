#!/usr/bin/env python3
"""VQ A3: original, geometry-based distal anatomy studies.

No imported 3D scans, photography or third-party mesh topology. Dimensions are
non-clinical stylized design ratios, not empirically validated human anatomy.
Bodies are SDF unions; these features join the main watertight skin, rather
than being independent tubes glued to the surface.
"""
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class DistalRecipe:
    fingers: int = 4
    thumbs: int = 1
    toes: int = 5
    finger_lengths: tuple = (.88, 1., .94, .70)  # index, middle, ring, little
    toe_lengths: tuple = (1., .94, .86, .77, .68)  # hallux -> fifth

RECIPE = DistalRecipe()


def add_face(add, ell, h, head_radius, center_y, face_width, jaw_strength):
    """Add authored craniofacial volumes and landmarks with bilateral pairing."""
    r=head_radius; cy=center_y
    # Muzzle of the human face: brow, malar cheek, chin, nasolabial fat,
    # cartilage-like nose wings and lip cushions. Does not reproduce a scan.
    for s in (-1, 1):
        add(ell((s*r*.22, cy+r*.135, -r*.295),
                (r*.16, r*.057, r*.107)), .010*h)  # supraorbital brow
        add(ell((s*r*.255, cy-r*.155, -r*.205),
                (r*.110*face_width, r*.105, r*.072)), .012*h)  # malar eminence
        add(ell((s*r*.275*jaw_strength,cy-r*.315,-r*.085),
                (r*.085,r*.077,r*.086)),.014*h)  # mandibular angle
        add(ell((s*r*.087,cy-r*.185,-r*.405),
                (r*.049,r*.042,r*.044)),.006*h)  # ala of nose
        add(ell((s*r*.39, cy-r*.01,-r*.025),
                (r*.065,r*.110,r*.065)),.005*h)  # pinna / ear root
    add(ell((0,cy-r*.357,-r*.251),
            (r*.170*jaw_strength,r*.098,r*.117)), .012*h)  # mentum
    add(ell((0,cy-r*.205,-r*.412),
            (r*.066,r*.080,r*.064)), .006*h)  # nasal tip
    add(ell((0,cy-r*.292,-r*.418),
            (r*.056,r*.024,r*.042)), .004*h)  # philtrum ridges
    add(ell((0,cy-r*.312,-r*.413),
            (r*.141,r*.024,r*.028)), .004*h)  # upper lip
    add(ell((0,cy-r*.350,-r*.408),
            (r*.135,r*.030,r*.033)), .004*h)  # lower lip


def hand_landmarks(wrist, sign, height):
    """Return five distinct fingertip target centers for a neutral T-pose."""
    wx,wy,wz=wrist;h=height
    # Palm continues from wrist toward the x-axis. Mild finger cascade
    # and a non-coplanar opposable thumb; the second digit is longest.
    palm=(wx+sign*.031*h, wy-.007*h, wz)
    fingers=[]
    for j,m in enumerate(RECIPE.finger_lengths):
        yoff=(1.5-j)*.0155*h
        base=(palm[0]+sign*.029*h,palm[1]+yoff,palm[2]-.001*h)
        length=.048*h*m
        tip=(base[0]+sign*length,base[1]+yoff*.20,base[2]-.007*h)
        fingers.append((base,tip))
    thumb_base=(palm[0]+sign*.009*h,palm[1]-.027*h,palm[2]-.011*h)
    thumb_tip=(palm[0]+sign*.059*h,palm[1]-.060*h,palm[2]-.020*h)
    return palm,fingers,(thumb_base,thumb_tip)


def add_hand(add, ell, capsule, wrist, sign, height):
    """One palm, four unequal three-segment fingers and an opposed thumb."""
    h=height;palm, fingers, thumb=hand_landmarks(wrist,sign,h)
    add(ell(palm,(.039*h,.039*h,.022*h)),.014*h)
    for j,(base,tip) in enumerate(fingers):
        s0=.0; y0=base[1]; z0=base[2]
        joint1=(base[0]+(tip[0]-base[0])*.48, y0+(tip[1]-y0)*.48, z0-.002*h)
        joint2=(base[0]+(tip[0]-base[0])*.78, y0+(tip[1]-y0)*.78, z0-.004*h)
        width=(.0081 if j!=3 else .0070)*h
        add(capsule(base,joint1,width,width*.83),.003*h)
        add(capsule(joint1,joint2,width*.83,width*.71),.002*h)
        add(capsule(joint2,tip,width*.71,width*.53),.0015*h)
        add(ell(joint1,(width*.92,width*.92,width*.75)),.001*h)
    tb,tt=thumb
    cmc=(tb[0]+sign*.018*h,tb[1]-.016*h,tb[2]-.013*h)
    add(capsule(tb,cmc,.0112*h,.0092*h),.003*h)
    add(capsule(cmc,tt,.0092*h,.0058*h),.002*h)
    return {'palm':palm,'finger_tips':[p[1] for p in fingers],'thumb_tip':tt}


def foot_landmarks(ankle,sign,height):
    """Heel, metatarsal heads and unequal toe tips in Z-forward orientation."""
    h=height;ax,ay,az=ankle
    # Index 0 sits medially, so the inner hallux is on the positive-X side
    # of the character's right foot; mirror across x=0 for the left.
    ball=(ax,.039*h,-.091*h)
    toe=[]
    for j,m in enumerate(RECIPE.toe_lengths):
        lateral=(2-j)*.020*h*sign
        base=(ax+lateral,.026*h,-.108*h)
        tip=(ax+lateral+sign*.004*h,.023*h,-(.130+.024*m)*h)
        toe.append((base,tip))
    return ball,toe


def add_foot(add,ell,capsule,ankle,sign,height):
    """Build connected heel, medial arch, metatarsal fan and five toes."""
    h=height;ax,ay,az=ankle
    add(ell((ax,.044*h,.014*h),(.030*h,.038*h,.038*h)),.012*h) # heel
    add(ell((ax,.062*h,-.047*h),(.038*h,.036*h,.069*h)),.012*h) # instep
    ball,toes=foot_landmarks(ankle,sign,h)
    add(ell(ball,(.047*h,.024*h,.036*h)),.018*h) # forefoot across five metatarsals
    for j,(start,tip) in enumerate(toes):
        width=(.013 if j==0 else .0092-(j-1)*.00085)*h
        # Positive sole-clearance without cylinders being detached.
        add(capsule(start,tip,width,width*.67),.003*h)
        add(ell((start[0],start[1]+.006*h,start[2]),
                (width*.95,width*.8,width*1.4)),.002*h)
    return {'ball':ball,'toe_tips':[p[1] for p in toes]}