import adsk.core, adsk.cam
TX, TY, R = 2438.4, 1219.2, 3.175

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    print(f"{cam.setups.count} setups\n")
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        q = {x.name: x for x in s.parameters}
        ox = q['job_stockFixedXOffset'].value.value*10
        oy = q['job_stockFixedYOffset'].value.value*10
        th = abs(q['stockZLow'].value.value*10)
        cx0 = q['surfaceXLow'].value.value*10-R; cx1 = q['surfaceXHigh'].value.value*10+R
        cy0 = q['surfaceYLow'].value.value*10-R; cy1 = q['surfaceYHigh'].value.value*10+R
        ok = cx0>=0 and cx1<=TX and cy0>=0 and cy1<=TY
        bad = sum(1 for j in range(s.operations.count)
                  if not s.operations.item(j).hasToolpath or s.operations.item(j).hasWarning)
        print(f"{s.name}")
        print(f"   prog {q['job_programName'].value.value}  {len(s.models)} parts  {th:.0f}mm  "
              f"offsets X{ox:.2f} Y{oy:.2f}  {s.operations.count} ops  "
              f"{'travel OK' if ok else 'OVER TRAVEL'}  problems {bad}")
        for j in range(s.operations.count):
            o = s.operations.item(j)
            p = {x.name: x for x in o.parameters}
            w = o.warning.strip().replace("\n"," ")[:45] if o.hasWarning else ""
            print(f"      {o.name:26} #{p['tool_number'].value.value} "
                  f"path {str(o.hasToolpath):5} {w}")
