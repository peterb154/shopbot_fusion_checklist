import adsk.core, adsk.cam

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    tot = 0.0
    print(f"{'setup':<44}{'ops':>4}{'tools':>16}{'min':>8}")
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        try: t = cam.getMachiningTime(s, 1.0, 0.0, 0.0).machiningTime/60
        except Exception: t = 0.0
        tot += t
        seq = [ {x.name: x for x in s.operations.item(j).parameters}['tool_number'].value.value
                for j in range(s.operations.count) ]
        ch = sum(1 for a,b in zip(seq, seq[1:]) if a != b)
        print(f"  {s.name[:42]:<42}{s.operations.count:>4}  {str(seq):<14}{t:>8.1f}   "
              f"{ch} change{'s' if ch!=1 else ''}")
    print(f"\n  {'TOTAL (all sheets)':<42}{'':>4}{'':>16}{tot:>8.1f} min "
          f"= {tot/60:.2f} h")
    print("\n  per-operation, largest first:")
    rows = []
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        for j in range(s.operations.count):
            o = s.operations.item(j)
            try: t = cam.getMachiningTime(o, 1.0, 0.0, 0.0).machiningTime/60
            except Exception: t = 0.0
            rows.append((t, s.name.split(' - ')[0], o.name))
    for t, sn, on in sorted(rows, reverse=True)[:10]:
        print(f"      {t:6.1f} min   {sn:<10} {on}")
