import adsk.core, adsk.fusion, adsk.cam, collections, math

def slopes(f, n=3):
    t = f.geometry.objectType.split("::")[-1]
    if t == "Plane":
        a = math.degrees(math.acos(min(1.0, abs(f.geometry.normal.z)))); return [a, a]
    if t == "Cylinder" and abs(abs(f.geometry.axis.z)-1.0) < 1e-6: return [90.0, 90.0]
    ev = f.evaluator; rng = ev.parametricRange()
    if rng is None: return []
    out = []
    for i in range(n):
        for j in range(n):
            u = rng.minPoint.x + (rng.maxPoint.x-rng.minPoint.x)*(i+0.5)/n
            v = rng.minPoint.y + (rng.maxPoint.y-rng.minPoint.y)*(j+0.5)/n
            ok, nv = ev.getNormalAtParameter(adsk.core.Point2D.create(u, v))
            if ok: out.append(math.degrees(math.acos(min(1.0, abs(nv.z)))))
    return out

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    T9R, T3R = 3.175, 1.587
    print(f"concave radii on sloped faces  (T9 ball R={T9R}mm, T3 ball R={T3R}mm)\n")
    for si in range(cam.setups.count):
        s = cam.setups.item(si)
        names = {m.name for m in s.models}
        rows = []
        for occ in des.rootComponent.allOccurrences:
            if occ.name not in names: continue
            for b in occ.bRepBodies:
                if not b.isSolid: continue
                sl_faces = [f for f in b.faces
                            if (lambda x: x and max(x) >= 5.0 and min(x) <= 85.0)(slopes(f))]
                if not sl_faces: continue
                radii = []
                for f in sl_faces:
                    g = f.geometry; t = g.objectType.split("::")[-1]
                    if t == "Sphere":   radii.append(("sphere", g.radius*10))
                    elif t == "Cylinder": radii.append(("cyl", g.radius*10))
                    elif t == "Cone":
                        try: radii.append(("cone", min(g.radius, g.radius)*10))
                        except Exception: pass
                    for L in f.loops:
                        for e in L.edges:
                            eg = e.geometry; et = eg.objectType.split("::")[-1]
                            if et in ("Arc3D", "Circle3D"):
                                radii.append(("edge", eg.radius*10))
                if not radii: continue
                tight9 = [r for _, r in radii if r < T9R - 1e-6]
                tight3 = [r for _, r in radii if r < T3R - 1e-6]
                rows.append((occ.name.split(':')[0].strip(), min(r for _, r in radii),
                             len(tight9), len(tight3), len(radii)))
        if rows:
            print(f"  {s.name}")
            for nm, mn, t9, t3, tot in sorted(rows, key=lambda r: r[1]):
                flag = ""
                if t9: flag = f"  <-- {t9} radii the 1/4in ball cannot enter"
                print(f"      {nm:<20} min radius {mn:6.2f}mm  of {tot:4} features"
                      f"   too tight for T9: {t9:3}  for T3: {t3:3}{flag}")
