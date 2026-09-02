import adsk.core, adsk.fusion, adsk.cam, collections, math

def slopes(f, n=3):
    """Angles from horizontal, sampled over the face. 0 = flat, 90 = vertical wall."""
    ev = f.evaluator
    rng = ev.parametricRange()
    if rng is None: return []
    out = []
    for i in range(n):
        for j in range(n):
            u = rng.minPoint.x + (rng.maxPoint.x - rng.minPoint.x) * (i + 0.5) / n
            v = rng.minPoint.y + (rng.maxPoint.y - rng.minPoint.y) * (j + 0.5) / n
            ok2, nv = ev.getNormalAtParameter(adsk.core.Point2D.create(u, v))
            if ok2: out.append(math.degrees(math.acos(min(1.0, abs(nv.z)))))
    return out

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    print("faces that are genuinely sloped (5-85 deg from horizontal):\n")
    total = 0
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        names = {m.name for m in s.models}
        rows = []
        for occ in des.rootComponent.allOccurrences:
            if occ.name not in names: continue
            for b in occ.bRepBodies:
                if not b.isSolid: continue
                sloped, area, angs = 0, 0.0, []
                vert = flat = 0
                for f in b.faces:
                    t = f.geometry.objectType.split("::")[-1]
                    if t == "Cylinder" and abs(abs(f.geometry.axis.z)-1.0) < 1e-6:
                        vert += 1; continue
                    sl = slopes(f)
                    if not sl: continue
                    lo, hi = min(sl), max(sl)
                    if hi < 1.0:   flat += 1; continue
                    if lo > 89.0:  vert += 1; continue
                    sloped += 1; area += f.area*100
                    angs.append((round(lo), round(hi), t))
                if sloped:
                    rows.append((occ.name.split(':')[0].strip(), sloped, area, angs))
                    total += sloped
        if rows:
            print(f"  {s.name}")
            for nm, n, ar, angs in sorted(rows, key=lambda r: -r[2]):
                kinds = collections.Counter(a[2] for a in angs)
                rngs = sorted({(a[0], a[1]) for a in angs})[:5]
                print(f"      {nm:<20} {n:3} faces  {ar:9.1f} mm2  {dict(kinds)}")
                print(f"          slope ranges (deg from horizontal): "
                      f"{', '.join(f'{a}-{b}' for a, b in rngs)}")
    print(f"\n  {total} genuinely sloped faces in the job")
