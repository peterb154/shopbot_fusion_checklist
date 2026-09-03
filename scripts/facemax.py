import adsk.core, adsk.fusion, adsk.cam, math

def normal_faces_axis(f):
    g = f.geometry; ev = f.evaluator
    ok, prm = ev.getParameterAtPoint(f.pointOnFace)
    if not ok: return True
    ok2, n = ev.getNormalAtParameter(prm); ok3, pt = ev.getPointAtParameter(prm)
    if not (ok2 and ok3): return True
    ax, org = g.axis, g.origin
    vx, vy, vz = pt.x-org.x, pt.y-org.y, pt.z-org.z
    d = vx*ax.x + vy*ax.y + vz*ax.z
    rx, ry, rz = vx-d*ax.x, vy-d*ax.y, vz-d*ax.z
    return (rx*n.x + ry*n.y + rz*n.z) < 0

def slopes(f, n=3):
    t = f.geometry.objectType.split("::")[-1]
    if t == "Plane":
        a = math.degrees(math.acos(min(1.0, abs(f.geometry.normal.z)))); return [a, a]
    if t == "Cylinder":
        g = f.geometry
        if abs(abs(g.axis.z)-1.0) < 1e-6 or normal_faces_axis(f): return [90.0, 90.0]
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
    rows = []
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        names = {m.name for m in s.models}
        for occ in des.rootComponent.allOccurrences:
            if occ.name not in names: continue
            for b in occ.bRepBodies:
                if not b.isSolid: continue
                faces = []
                for f in b.faces:
                    sl = slopes(f)
                    if sl and max(sl) >= 5.0 and min(sl) <= 85.0:
                        fzs = [v.geometry.z*10 for v in f.vertices]
                        drop = (max(fzs)-min(fzs)) if fzs else 0.0
                        faces.append((f.area*100, drop))
                if not faces: continue
                rows.append((s.name.split(' - ')[0], occ.name.split(':')[0].strip(),
                             len(faces), max(a for a, _ in faces),
                             sum(a for a, _ in faces),
                             max(d for _, d in faces)))
    print(f"{'sheet':<9}{'part':<22}{'faces':>6}{'largest':>10}{'total':>10}{'maxZdrop':>10}")
    for sn, nm, n, mx, tot, drop in sorted(rows, key=lambda r: -r[3]):
        mark = "" if mx >= 500 else "   <- largest face under 500mm2"
        print(f"{sn:<9}{nm:<22}{n:>6}{mx:>10.1f}{tot:>10.1f}{drop:>10.2f}{mark}")
