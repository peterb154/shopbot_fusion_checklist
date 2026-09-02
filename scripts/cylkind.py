import adsk.core, adsk.fusion, adsk.cam, collections

def normal_faces_axis(f):
    """True if the face normal points TOWARD the cylinder axis -> it is a hole.
    False -> material is inside the cylinder -> convex rounded edge."""
    g = f.geometry; ev = f.evaluator
    ok, prm = ev.getParameterAtPoint(f.pointOnFace)
    if not ok: return None
    ok2, n = ev.getNormalAtParameter(prm)
    ok3, pt = ev.getPointAtParameter(prm)
    if not (ok2 and ok3): return None
    ax, org = g.axis, g.origin
    vx, vy, vz = pt.x-org.x, pt.y-org.y, pt.z-org.z
    d = vx*ax.x + vy*ax.y + vz*ax.z
    rx, ry, rz = vx-d*ax.x, vy-d*ax.y, vz-d*ax.z
    return (rx*n.x + ry*n.y + rz*n.z) < 0

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    want = {"SIDE PNL RT","RIB LT 7","RIB LT 8","ECS VENT PLATE 1","ECS VENT PLATE 2",
            "LONGERON RT MID","INST PNL UPR"}
    print("non-vertical cylinders on parts I excluded or questioned:\n")
    for occ in des.rootComponent.allOccurrences:
        n = occ.name.split(':')[0].strip()
        if n not in want: continue
        for b in occ.bRepBodies:
            if not b.isSolid: continue
            holes, rounds = [], []
            for f in b.faces:
                g = f.geometry
                if g.objectType != adsk.core.Cylinder.classType(): continue
                if abs(abs(g.axis.z)-1.0) < 1e-6: continue
                t = normal_faces_axis(f)
                (holes if t else rounds).append((g.radius*20, f.area*100))
            if not (holes or rounds): continue
            print(f"  {n}")
            if rounds:
                print(f"      ROUNDED EDGES (machinable): {len(rounds)} faces, "
                      f"{sum(a for _, a in rounds):9.1f} mm2   "
                      f"radii {sorted({round(r/2,2) for r, _ in rounds})}")
            if holes:
                print(f"      angled HOLES (not 3-axis):  {len(holes)} faces, "
                      f"{sum(a for _, a in holes):9.1f} mm2   "
                      f"dia {sorted({round(r,2) for r, _ in holes})}")
