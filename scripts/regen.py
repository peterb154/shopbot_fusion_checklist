import adsk.core, adsk.cam, time

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    bad = []
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        for j in range(s.operations.count):
            o = s.operations.item(j)
            if not o.hasToolpath: bad.append((s, o))
    print(f"{len(bad)} ops without a toolpath: {[o.name for _, o in bad]}")
    for s, o in bad:
        n = o.parameters.itemByName("holeFaces")
        cnt = len(n.value.value) if n and n.value.value else 0
        print(f"   {o.name}: holeFaces={cnt}")
        fut = cam.generateToolpath(o)
        for _ in range(600):
            if fut.isGenerationCompleted: break
            time.sleep(1)
        print(f"   -> path {o.hasToolpath}  warn {o.hasWarning} "
              f"{o.warning.strip().replace(chr(10),' ')[:60] if o.hasWarning else ''}")
