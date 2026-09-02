import adsk.core, adsk.fusion, adsk.cam, collections

def true_normal(f):
    """Outward normal of the FACE, not the underlying surface - they differ when
    the face parameterisation is reversed."""
    ev = f.evaluator
    ok, prm = ev.getParameterAtPoint(f.pointOnFace)
    if not ok: return None
    ok2, n = ev.getNormalAtParameter(prm)
    return n if ok2 else None

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    print("pocket floors by facing direction (UP = machinable from the top):\n")
    trouble = []
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        names = {m.name for m in s.models}
        rows = []
        for occ in des.rootComponent.allOccurrences:
            if occ.name not in names: continue
            for b in occ.bRepBodies:
                if not b.isSolid: continue
                zs = [v.geometry.z*10 for v in b.vertices]
                zt, zb = max(zs), min(zs)
                up = dn = 0
                depths = []
                for f in b.faces:
                    if f.geometry.objectType != adsk.core.Plane.classType(): continue
                    n = true_normal(f)
                    if n is None or abs(abs(n.z)-1.0) > 1e-4: continue
                    fzs = [v.geometry.z*10 for v in f.vertices]
                    if not fzs: continue
                    fz = sum(fzs)/len(fzs)
                    if not (zb + 0.1 < fz < zt - 0.1): continue
                    if n.z > 0: up += 1;  depths.append(("up", round(zt-fz, 2)))
                    else:       dn += 1;  depths.append(("dn", round(fz-zb, 2)))
                if up or dn:
                    rows.append((occ.name.split(':')[0].strip(), up, dn, depths))
        if not rows: continue
        print(f"  {s.name}")
        for nm, up, dn, depths in rows:
            flag = ""
            if dn and not up: flag = "   <-- ALL FLOORS FACE DOWN - part is upside down"
            elif dn and up:   flag = "   <-- has floors BOTH ways, check intent"
            print(f"      {nm:<22} up {up:2}  down {dn:2}{flag}")
            if dn:
                d = [f"{k}{v}" for k, v in depths]
                print(f"          depths: {', '.join(d[:8])}")
                trouble.append((s.name, nm, up, dn))
    print()
    if trouble:
        print(f"*** {len(trouble)} part(s) with downward-facing pockets:")
        for sn, nm, up, dn in trouble:
            print(f"      {sn:<18} {nm:<22} {dn} down-facing, {up} up-facing")
    else:
        print("no downward-facing pocket floors anywhere - all pockets open upward")
