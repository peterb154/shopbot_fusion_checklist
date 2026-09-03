import adsk.core, adsk.fusion, adsk.cam
TX, TY, R = 2438.4, 1219.2, 3.175

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    print("travel from TRUE vertices (Fusion's surfaceX/Y use inflated bounding boxes):\n")
    print(f"{'setup':<16}{'spanX':>9}{'spanY':>9}{'cutterX':>19}{'cutterY':>19}  verdict")
    allok = True
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        q = {x.name: x for x in s.parameters}
        ox = q['job_stockFixedXOffset'].value.value*10
        oy = q['job_stockFixedYOffset'].value.value*10
        names = {m.name for m in s.models}
        xs, ys = [], []
        for occ in des.rootComponent.allOccurrences:
            if occ.name not in names: continue
            for b in occ.bRepBodies:
                if not b.isSolid: continue
                xs += [v.geometry.x*10 for v in b.vertices]
                ys += [v.geometry.y*10 for v in b.vertices]
        if not xs: continue
        sx, sy = max(xs)-min(xs), max(ys)-min(ys)
        cx0, cx1 = ox - R, ox + sx + R
        cy0, cy1 = oy - R, oy + sy + R
        ok = cx0 >= 0 and cx1 <= TX and cy0 >= 0 and cy1 <= TY
        allok = allok and ok
        # what Fusion thinks, for comparison
        fx1 = q['surfaceXHigh'].value.value*10 + R
        fy1 = q['surfaceYHigh'].value.value*10 + R
        print(f"{s.name:<16}{sx:9.1f}{sy:9.1f}"
              f"{cx0:9.2f}..{cx1:8.2f}{cy0:9.2f}..{cy1:8.2f}  "
              f"{'OK' if ok else '*** OVER ***'}"
              f"   (Fusion bbox says X{fx1:.0f} Y{fy1:.0f})")
    print(f"\n  slack to travel limits:")
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        q = {x.name: x for x in s.parameters}
        ox = q['job_stockFixedXOffset'].value.value*10; oy = q['job_stockFixedYOffset'].value.value*10
        names = {m.name for m in s.models}
        xs, ys = [], []
        for occ in des.rootComponent.allOccurrences:
            if occ.name not in names: continue
            for b in occ.bRepBodies:
                if b.isSolid:
                    xs += [v.geometry.x*10 for v in b.vertices]
                    ys += [v.geometry.y*10 for v in b.vertices]
        if not xs: continue
        sx, sy = max(xs)-min(xs), max(ys)-min(ys)
        print(f"     {s.name:<16} X {ox-R:6.2f} left / {TX-(ox+sx+R):7.2f} right   "
              f"Y {oy-R:6.2f} front / {TY-(oy+sy+R):7.2f} back")
    print(f"\n  {'ALL SHEETS WITHIN TRAVEL' if allok else '*** AT LEAST ONE OVER TRAVEL ***'}")
