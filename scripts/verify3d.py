import adsk.core, adsk.fusion, adsk.cam, os, json
OUT = "/private/tmp/claude-501/-Users-brianpeterson-Projects-personal-shopbot-fusion-checklist/664e57f4-3c71-4f00-aa85-081a27aa5e42/scratchpad/post"

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    os.makedirs(OUT, exist_ok=True)
    cps = None
    for root, _, files in os.walk(cam.genericPostFolder):
        for f in files:
            if f.lower() == "shopbot.cps": cps = os.path.join(root, f)
    meta = {}
    for want in ("Sheet 1 - 12mm", "Sheet 4 - 18mm"):
        s = next(cam.setups.item(i) for i in range(cam.setups.count) if cam.setups.item(i).name == want)
        o = next((s.operations.item(j) for j in range(s.operations.count)
                  if "Bevels" in s.operations.item(j).name), None)
        if not o: continue
        q = {x.name: x for x in s.parameters}
        ox = q['job_stockFixedXOffset'].value.value*10; oy = q['job_stockFixedYOffset'].value.value*10
        pts = []
        for occ in des.rootComponent.allOccurrences:
            if occ.name not in {m.name for m in s.models}: continue
            for b in occ.bRepBodies:
                if b.isSolid:
                    xs=[v.geometry.x*10 for v in b.vertices]; ys=[v.geometry.y*10 for v in b.vertices]
                    pts.append((occ.name.split(':')[0].strip(), min(xs),max(xs),min(ys),max(ys)))
        mnx = min(p[1] for p in pts); mny = min(p[3] for p in pts)
        tag = want.split(' - ')[0].replace(' ','')
        meta[tag] = {n: [a-mnx+ox, b-mnx+ox, c-mny+oy, d-mny+oy] for n,a,b,c,d in pts}
        f = f"bev{tag}"
        try:
            pi = adsk.cam.PostProcessInput.create(f, cps, OUT, adsk.cam.PostOutputUnitOptions.MillimetersOutput)
            pi.isOpenInEditor = False
            print(f"{want}: posted {cam.postProcess(o, pi)} -> {f}.sbp")
        except Exception as e:
            print(f"{want}: post failed {str(e).splitlines()[-1][:50]}")
    open(os.path.join(OUT, "regions.json"), "w").write(json.dumps(meta))
    print("wrote regions.json")
