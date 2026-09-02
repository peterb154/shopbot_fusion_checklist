import adsk.core, adsk.fusion
TX, R, WANT = 2438.4, 3.175, 20.0     # want 20mm of placement latitude

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    root = des.rootComponent
    sheets, parts = [], []
    def add(nm, b):
        xs=[v.geometry.x*10 for v in b.vertices]; ys=[v.geometry.y*10 for v in b.vertices]
        zz=[v.geometry.z*10 for v in b.vertices]
        w,h=max(xs)-min(xs),max(ys)-min(ys)
        r=dict(n=nm,x0=min(xs),x1=max(xs),y0=min(ys),y1=max(ys),w=w,h=h,
               th=round(max(zz)-min(zz),1))
        (sheets if (w>2400 and h>1200) else parts).append(r)
    for occ in root.allOccurrences:
        for b in occ.bRepBodies:
            if b.isSolid: add(occ.name.split(':')[0], b)
    for b in root.bRepBodies:
        if b.isSolid: add(f"<root>/{b.name}", b)

    for s in sheets:
        on=[p for p in parts if p['x0']<s['x1'] and p['x1']>s['x0']
            and p['y0']<s['y1'] and p['y1']>s['y0']]
        if not on: continue
        lo = min(p['x0'] for p in on); hi = max(p['x1'] for p in on)
        need = (hi-lo) + 2*R + WANT
        if need <= TX: continue
        shrink = need - TX
        blocker = max(on, key=lambda p:p['x1'])
        print(f"\n=== {s['n']} X{s['x0']:.0f} Y{s['y0']:.0f} ({blocker['th']:.0f}mm)"
              f"   must shrink X span by {shrink:.1f}mm for {WANT:.0f}mm latitude")
        print(f"    blocker: {blocker['n']}  {blocker['w']:.1f} x {blocker['h']:.1f}"
              f"   x {blocker['x1']-lo:.1f} at right edge")
        # what sits to its left within its Y band?
        band = [p for p in on if p is not blocker
                and p['y0'] < blocker['y1'] and p['y1'] > blocker['y0']
                and p['x1'] <= blocker['x0'] + 1]
        if band:
            nb = max(band, key=lambda p:p['x1'])
            gap = blocker['x0'] - nb['x1']
            print(f"    nearest neighbour in its Y band: {nb['n']}  ends x {nb['x1']-lo:.1f}"
                  f"   gap {gap:.1f}mm")
            print(f"    -> slide it LEFT {shrink:.1f}mm: "
                  f"{'FITS in the gap' if gap >= shrink else f'gap too small by {shrink-gap:.1f}mm'}")
        else:
            print(f"    nothing to its left in Y {blocker['y0']-min(p['y0'] for p in on):.0f}"
                  f"..{blocker['y1']-min(p['y0'] for p in on):.0f} - free to slide left")
        # second opinion: who becomes the blocker after it moves
        rest = sorted((p for p in on if p is not blocker), key=lambda p:-p['x1'])[0]
        print(f"    next-rightmost is {rest['n']} at x {rest['x1']-lo:.1f}"
              f"  -> span would be {rest['x1']-lo:.1f}, latitude {TX-(rest['x1']-lo)-2*R:.1f}mm")
