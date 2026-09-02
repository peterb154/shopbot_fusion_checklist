import adsk.core, adsk.fusion
TX, TY, R = 2438.4, 1219.2, 3.175
SW, SH = 2440.0, 1220.0     # standard sheet

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    root = des.rootComponent
    sheets, parts = [], []
    def add(nm, b):
        xs=[v.geometry.x*10 for v in b.vertices]; ys=[v.geometry.y*10 for v in b.vertices]
        zz=[v.geometry.z*10 for v in b.vertices]
        w,h=max(xs)-min(xs),max(ys)-min(ys)
        r=dict(n=nm,x0=min(xs),x1=max(xs),y0=min(ys),y1=max(ys),th=round(max(zz)-min(zz),1))
        (sheets if (w>2400 and h>1200) else parts).append(r)
    for occ in root.allOccurrences:
        for b in occ.bRepBodies:
            if b.isSolid: add(occ.name.split(':')[0], b)
    for b in root.bRepBodies:
        if b.isSolid: add(f"<root>/{b.name}", b)

    print(f"{'sheet':<24}{'th':>4}{'span X':>9}{'span Y':>9}   valid X offset      pick")
    for s in sorted(sheets, key=lambda r:(-r['y0'], r['x0'])):
        on=[p for p in parts if p['x0']<s['x1'] and p['x1']>s['x0']
            and p['y0']<s['y1'] and p['y1']>s['y0']]
        if not on: continue
        sx=max(p['x1'] for p in on)-min(p['x0'] for p in on)
        sy=max(p['y1'] for p in on)-min(p['y0'] for p in on)
        lo_x, hi_x = R, TX - sx - R
        lo_y, hi_y = R, TY - sy - R
        ok = hi_x >= lo_x and hi_y >= lo_y
        px = min(20.0, max(lo_x, hi_x*0.5)) if ok else None
        py = min(20.0, max(lo_y, hi_y*0.5)) if ok else None
        tag=f"{s['n'][:12]} X{s['x0']:.0f} Y{s['y0']:.0f}"
        rng = f"{lo_x:6.2f}..{hi_x:7.2f}" if ok else "  DOES NOT FIT"
        print(f"{tag:<24}{s['th']:4.0f}{sx:9.1f}{sy:9.1f}   {rng}   X {px if px is None else round(px,2):>7}"
              f"  Y {py if py is None else round(py,2):>7}")
        if ok and hi_x < 20:
            print(f"      note: X offset forced below 20mm - only {hi_x-lo_x:.1f}mm of latitude")
