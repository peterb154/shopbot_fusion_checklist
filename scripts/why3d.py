import adsk.core, adsk.fusion, adsk.cam, math

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
    s = next(cam.setups.item(i) for i in range(cam.setups.count) if cam.setups.item(i).name == "Sheet 1 - 12mm")
    names = {m.name for m in s.models}
    print("Sheet 1 - every face that put a part into the 3D pass:\n")
    for occ in des.rootComponent.allOccurrences:
        if occ.name not in names: continue
        for b in occ.bRepBodies:
            if not b.isSolid: continue
            hits = []
            for f in b.faces:
                sl = slopes(f)
                if not sl or max(sl) < 5.0 or min(sl) > 85.0: continue
                g = f.geometry; t = g.objectType.split("::")[-1]
                extra = ""
                if t == "Cylinder":
                    ax = g.axis
                    extra = (f"  axis=({ax.x:+.2f},{ax.y:+.2f},{ax.z:+.2f}) "
                             f"r={g.radius*10:.2f}mm  <-- ANGLED HOLE, not a bevel")
                hits.append((t, round(min(sl)), round(max(sl)), f.area*100, extra))
            if hits:
                tot = sum(h[3] for h in hits)
                print(f"  {occ.name.split(':')[0].strip():<20} {len(hits)} faces, {tot:8.1f} mm2")
                for t, lo, hi, a, extra in sorted(hits, key=lambda h: -h[3]):
                    print(f"      {t:<14} {lo:3}-{hi:3} deg  {a:8.1f} mm2{extra}")
