"""Remove leftover experiment operations and report the health of every setup.

Trial operations whose creation threw before their deleteMe() ran will sit in a
setup with no toolpath. Fusion's post processor refuses to run while any such
operation exists, and the error it gives ("Initialization fails") does not say
which operation is at fault - so sweep before posting.
"""
import adsk.core, adsk.cam

PREFIXES = ("__trial", "__probe", "__p_")

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    killed = []
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        for j in range(s.operations.count - 1, -1, -1):
            o = s.operations.item(j)
            if o.name.startswith(PREFIXES):
                killed.append(f"{s.name} / {o.name}")
                o.deleteMe()
    print(f"removed {len(killed)} leftover trial ops")
    for k in killed:
        print(f"    {k}")

    print("\nsetups:")
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        flags = [s.operations.item(j).name for j in range(s.operations.count)
                 if not s.operations.item(j).hasToolpath or s.operations.item(j).hasWarning]
        print(f"  {s.name[:44]:<46} {s.operations.count} ops"
              f"{'  PROBLEM: ' + ', '.join(flags) if flags else '  all clean'}")
