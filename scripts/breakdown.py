import adsk.core, adsk.cam, collections

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    print("per-operation time:\n")
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        print(f"  {s.name}")
        for j in range(s.operations.count):
            o = s.operations.item(j)
            try: t = cam.getMachiningTime(o, 1.0, 0.0, 0.0).machiningTime/60
            except Exception: t = float('nan')
            print(f"      {o.name:26} {t:7.1f} min")
    print("\n\nsmall-hole diameters (the 1/8in bore ops):\n")
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        for j in range(s.operations.count):
            o = s.operations.item(j)
            if "small" not in o.name: continue
            p = o.parameters.itemByName("circularFaces")
            faces = p.value.value
            d = collections.Counter(round(f.geometry.radius*20, 2) for f in faces)
            zs = collections.Counter()
            for f in faces:
                bb = f.boundingBox
                zs[round((bb.maxPoint.z-bb.minPoint.z)*10, 1)] += 1
            print(f"  {s.name[:34]:<36} {len(faces):4} holes")
            for dia, n in sorted(d.items()):
                print(f"       dia {dia:6.2f}mm  x{n:4}   "
                      f"{'plunge-able with 1/8in' if abs(dia-3.175)<0.35 else ''}")
            print(f"       depths {dict(sorted(zs.items()))}")
