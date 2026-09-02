import adsk.core, adsk.cam

def snap(s):
    d = {}
    for p in s.parameters:
        try: d[p.name] = str(p.expression)
        except Exception:
            try: d[p.name] = str(p.value.value)
            except Exception: d[p.name] = "<n/a>"
    return d

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    g = lambda n: next(cam.setups.item(i) for i in range(cam.setups.count) if cam.setups.item(i).name == n)
    a, b = snap(g("Sheet 6 - 18mm")), snap(g("Sheet 1 - 12mm"))
    keys = sorted(set(a) | set(b))
    print(f"{'parameter':<40}{'Sheet 6 (drills OK)':<30}{'Sheet 1 (refuses)'}")
    n = 0
    for k in keys:
        va, vb = a.get(k, "<missing>"), b.get(k, "<missing>")
        if va == vb: continue
        n += 1
        print(f"  {k:<38}{va[:28]:<30}{vb[:28]}")
    print(f"\n{n} differing parameters")
