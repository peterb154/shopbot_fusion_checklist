import adsk.core, adsk.cam, time
TX, TY, R = 2438.4, 1219.2, 3.175

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        q = {x.name: x for x in s.parameters}
        sx = (q['surfaceXHigh'].value.value - q['surfaceXLow'].value.value)*10
        sy = (q['surfaceYHigh'].value.value - q['surfaceYLow'].value.value)*10
        hx, hy = TX - sx - R, TY - sy - R
        want_x = 20.0 if hx >= 40.0 else max(R, hx*0.5)
        want_y = 20.0 if hy >= 40.0 else max(R, hy*0.5)
        cur_x = q['job_stockFixedXOffset'].value.value*10
        cur_y = q['job_stockFixedYOffset'].value.value*10
        if abs(cur_x-want_x) < 0.01 and abs(cur_y-want_y) < 0.01:
            print(f"  {s.name[:42]:<44} offsets already {cur_x:.2f}/{cur_y:.2f}")
            continue
        q['job_stockFixedXOffset'].expression = f"{round(want_x,2)}mm"
        q['job_stockFixedYOffset'].expression = f"{round(want_y,2)}mm"
        fut = cam.generateToolpath(s)
        for _ in range(700):
            if fut.isGenerationCompleted: break
            time.sleep(1)
        q = {x.name: x for x in s.parameters}
        cx0 = q['surfaceXLow'].value.value*10 - R; cx1 = q['surfaceXHigh'].value.value*10 + R
        cy0 = q['surfaceYLow'].value.value*10 - R; cy1 = q['surfaceYHigh'].value.value*10 + R
        bad = sum(1 for j in range(s.operations.count)
                  if not s.operations.item(j).hasToolpath or s.operations.item(j).hasWarning)
        print(f"  {s.name[:42]:<44} {cur_x:.2f}/{cur_y:.2f} -> {want_x:.2f}/{want_y:.2f}"
              f"   margins X {cx0:.1f}/{TX-cx1:.1f}  Y {cy0:.1f}/{TY-cy1:.1f}"
              f"   problems {bad}")
