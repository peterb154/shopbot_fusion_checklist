import adsk.core, adsk.fusion, collections
TX, TY, R = 2438.4, 1219.2, 3.175
SW, SH = 2440.0, 1220.0

def ext(b):
    xs=[v.geometry.x*10 for v in b.vertices]; ys=[v.geometry.y*10 for v in b.vertices]
    zs=[v.geometry.z*10 for v in b.vertices]
    return min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    root = des.rootComponent
    sheets, parts = [], []
    def add(nm, b, occ):
        x0,x1,y0,y1,z0,z1 = ext(b)
        r = dict(n=nm, occ=occ, x0=x0,x1=x1,y0=y0,y1=y1, th=round(z1-z0,1),
                 w=x1-x0, h=y1-y0, body=b)
        (sheets if (r['w']>2400 and r['h']>1200) else parts).append(r)
    for occ in root.allOccurrences:
        for b in occ.bRepBodies:
            if b.isSolid: add(occ.name.split(':')[0], b, occ)
    for b in root.bRepBodies:
        if b.isSolid: add(f"<root>/{b.name}", b, None)

    sheets.sort(key=lambda s: (-s['y0'], s['x0']))
    print(f"{len(sheets)} sheets, {len(parts)} parts\n")
    placed = set()
    for i, s in enumerate(sheets, 1):
        on = [p for p in parts if p['x0']<s['x1'] and p['x1']>s['x0']
              and p['y0']<s['y1'] and p['y1']>s['y0']]
        for p in on: placed.add(id(p))
        if not on:
            print(f"  Sheet {i} {s['n'][:22]:<24} EMPTY"); continue
        lo,hi = min(p['x0'] for p in on), max(p['x1'] for p in on)
        ylo,yhi = min(p['y0'] for p in on), max(p['y1'] for p in on)
        sx, sy = hi-lo, yhi-ylo
        hx, hy = TX - sx - R, TY - sy - R
        th = collections.Counter(p['th'] for p in on).most_common()
        ok = hx >= R and hy >= R
        lat = min(hx-R, hy-R)
        area = sum(p['w']*p['h'] for p in on)
        print(f"  Sheet {i}  {s['n'][:20]:<22} {len(on):3} parts  {th[0][0]:.0f}mm"
              f"{'  MIXED '+str(dict(th)) if len(th)>1 else ''}")
        print(f"      span {sx:7.1f} x {sy:6.1f}   offset range X [{R:.2f}, {hx:.2f}]"
              f"  Y [{R:.2f}, {hy:.2f}]   latitude {lat:6.2f}mm"
              f"   {'OK' if lat>=10 else '*** TOO TIGHT ***' if ok else '*** DOES NOT FIT ***'}")
        if sx > SW or sy > SH:
            print(f"      *** exceeds {SW}x{SH} sheet ***")
        # overlaps
        bad = []
        for a in range(len(on)):
            for b_ in range(a+1, len(on)):
                p, q = on[a], on[b_]
                ox = min(p['x1'],q['x1'])-max(p['x0'],q['x0'])
                oy = min(p['y1'],q['y1'])-max(p['y0'],q['y0'])
                if ox > 0.5 and oy > 0.5: bad.append((p['n'], q['n'], ox, oy))
        if bad:
            print(f"      {len(bad)} bounding-box overlaps (may be legitimate interlocking):")
            for n1,n2,ox,oy in bad[:4]:
                print(f"         {n1[:26]:<28} vs {n2[:26]:<28} {ox:6.1f} x {oy:5.1f}")
    orphan = [p for p in parts if id(p) not in placed]
    if orphan:
        print(f"\n  {len(orphan)} parts on NO sheet:")
        for p in orphan:
            print(f"      {p['n'][:34]:<36} {p['w']:7.1f} x {p['h']:6.1f} x {p['th']:.0f}mm"
                  f"   at X{p['x0']:.0f} Y{p['y0']:.0f}")
