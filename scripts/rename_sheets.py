import adsk.core, adsk.fusion

def ext(b):
    xs=[v.geometry.x*10 for v in b.vertices]; ys=[v.geometry.y*10 for v in b.vertices]
    zs=[v.geometry.z*10 for v in b.vertices]
    return min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)

def is_sheet(b):
    x0,x1,y0,y1,_,_ = ext(b)
    return (x1-x0) > 2400 and (y1-y0) > 1200

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    root = des.rootComponent
    ply = next((o for o in root.allOccurrences
                if o.component.name.upper().startswith("PLYWOOD")), None)
    if not ply:
        print("no PLYWOOD component"); return

    found = []
    for i in range(ply.component.bRepBodies.count):
        nat = ply.component.bRepBodies.item(i)
        prox = ply.bRepBodies.item(i)
        if is_sheet(prox): found.append([prox, nat, "PLYWOOD"])
    for b in root.bRepBodies:
        if is_sheet(b): found.append([b, b, "root"])

    for r in found:
        x0, x1, y0, y1, z0, z1 = ext(r[0])
        r += [x0, y0, round(z1 - z0, 1)]
    found.sort(key=lambda r: (-r[4], r[3]))

    print(f"{len(found)} sheets, numbered top-to-bottom then left-to-right:\n")
    plan = []
    for n, r in enumerate(found, 1):
        prox, nat, where, x0, y0, th = r
        new = f"Sheet {n} - {th:.0f}mm"
        plan.append((nat, new, where))
        print(f"   Sheet {n}   '{nat.name}' in {where:<8} at X{x0:6.0f} Y{y0:6.0f}"
              f"  {th:.0f}mm   ->  '{new}'")

    # two-phase rename so a name never collides with one still in use
    for i, (nat, _, _) in enumerate(plan):
        nat.name = f"__tmp_sheet_{i}"
    for nat, new, _ in plan:
        nat.name = new
    print("\nrenamed.")

    moved = 0
    for nat, new, where in plan:
        if where != "root": continue
        try:
            nat.moveToComponent(ply)
            moved += 1
            print(f"moved '{new}' from root into PLYWOOD")
        except Exception as e:
            print(f"could NOT move '{new}': {str(e).splitlines()[-1][:70]}")
    print(f"\nroot bodies remaining: {root.bRepBodies.count}"
          f"   PLYWOOD bodies: {ply.component.bRepBodies.count}")
    for b in ply.component.bRepBodies:
        print(f"   PLYWOOD / '{b.name}'")
