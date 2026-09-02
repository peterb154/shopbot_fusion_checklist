import adsk.core, adsk.cam, collections

def run(_context: str):
    app = adsk.core.Application.get()
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    lm = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    local = lm.urlByLocation(adsk.cam.LibraryLocations.LocalLibraryLocation)
    info = {}
    for u in lm.childAssetURLs(local):
        if "MCC ShopBot" not in u.leafName: continue
        for t in lm.toolLibraryAtURL(u):
            p = {x.name: x for x in t.parameters}
            n = p['tool_number'].value.value
            info[n] = dict(
                desc=str(p['tool_description'].value.value),
                typ=str(p['tool_type'].value.value),
                dia=p['tool_diameter'].value.value*10,
                flute=p['tool_fluteLength'].value.value*10 if 'tool_fluteLength' in p else 0,
                nf=p['tool_numberOfFlutes'].value.value if 'tool_numberOfFlutes' in p else '?')
    print("MCC ShopBot library:\n")
    for n in sorted(info):
        d = info[n]
        print(f"  T{n}  {d['dia']:6.3f}mm  {d['typ']:<14} {d['nf']}fl  "
              f"flute {d['flute']:5.1f}mm")
        print(f"        {d['desc'][:76]}")

    print("\n\nwhere each tool is used:\n")
    use = collections.defaultdict(list)
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        for j in range(s.operations.count):
            o = s.operations.item(j)
            P = {x.name: x for x in o.parameters}
            tn = P['tool_number'].value.value
            try: t = cam.getMachiningTime(o,1.,0.,0.).machiningTime/60
            except Exception: t = 0.0
            use[tn].append((s.name.replace(" - ", " "), o.name, t))
    for n in sorted(use):
        tot = sum(x[2] for x in use[n])
        d = info.get(n, {})
        print(f"  T{n}  ({d.get('dia',0):.3f}mm {d.get('typ','?')})   "
              f"{len(use[n])} ops, {tot:.1f} min total")
        for sn, on, t in use[n]:
            print(f"        {sn:<16} {on:<28} {t:6.1f} min")
    unused = sorted(set(info) - set(use))
    print(f"\n  in library but unused: {['T%d' % n for n in unused]}")
