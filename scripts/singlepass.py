import adsk.core, adsk.cam, time

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        q = {x.name: x for x in s.parameters}
        th = abs(q['stockZLow'].value.value*10)
        want = round(th + 1.0, 2)
        hit = []
        for j in range(s.operations.count):
            o = s.operations.item(j)
            P = {x.name: x for x in o.parameters}
            if "Pocket" in o.name or 'maximumStepdown' not in P: continue
            cur = P['maximumStepdown'].value.value*10
            if abs(cur - want) < 0.01: continue
            P['maximumStepdown'].expression = f"{want}mm"
            hit.append(f"{o.name} {cur:.1f}->{want:.1f}")
        if not hit:
            print(f"  {s.name[:42]:<44} no change"); continue
        before = cam.getMachiningTime(s,1.,0.,0.).machiningTime/60
        fut = cam.generateToolpath(s)
        for _ in range(900):
            if fut.isGenerationCompleted: break
            time.sleep(1)
        after = cam.getMachiningTime(s,1.,0.,0.).machiningTime/60
        bad = sum(1 for j in range(s.operations.count)
                  if not s.operations.item(j).hasToolpath or s.operations.item(j).hasWarning)
        print(f"  {s.name[:42]:<44} {before:6.1f} -> {after:6.1f} min  "
              f"({len(hit)} ops, {th:.0f}mm stock)  problems {bad}")
