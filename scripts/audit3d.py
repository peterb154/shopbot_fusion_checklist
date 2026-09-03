import adsk.core, adsk.fusion, adsk.cam, math, collections

BALL_R = 3.175
SLOPE_MIN, SLOPE_MAX = 5.0, 85.0
MIN_FACE_DROP = 0.5
MIN_3D_FACE, MIN_3D_COUNT, MIN_3D_GROUP = 500.0, 8, 800.0

def tn(f):
    ev=f.evaluator; ok,prm=ev.getParameterAtPoint(f.pointOnFace)
    if not ok: return None
    ok2,n=ev.getNormalAtParameter(prm)
    return n if ok2 else None

def faces_axis(f):
    g=f.geometry; ev=f.evaluator
    ok,prm=ev.getParameterAtPoint(f.pointOnFace)
    if not ok: return True
    ok2,n=ev.getNormalAtParameter(prm); ok3,pt=ev.getPointAtParameter(prm)
    if not(ok2 and ok3): return True
    ax,org=g.axis,g.origin
    vx,vy,vz=pt.x-org.x,pt.y-org.y,pt.z-org.z
    d=vx*ax.x+vy*ax.y+vz*ax.z
    rx,ry,rz=vx-d*ax.x,vy-d*ax.y,vz-d*ax.z
    return (rx*n.x+ry*n.y+rz*n.z)<0

def samples(f,n=3):
    t=f.geometry.objectType.split("::")[-1]
    if t=="Plane":
        nv=tn(f)
        return [] if nv is None else [(math.degrees(math.acos(min(1.0,abs(nv.z)))),nv.z)]
    if t=="Cylinder":
        g=f.geometry
        if abs(abs(g.axis.z)-1.0)<1e-6: return [(90.0,0.0)]
        if faces_axis(f): return None            # angled hole
    ev=f.evaluator; rng=ev.parametricRange()
    if rng is None: return []
    out=[]
    for i in range(n):
        for j in range(n):
            u=rng.minPoint.x+(rng.maxPoint.x-rng.minPoint.x)*(i+0.5)/n
            v=rng.minPoint.y+(rng.maxPoint.y-rng.minPoint.y)*(j+0.5)/n
            ok,nv=ev.getNormalAtParameter(adsk.core.Point2D.create(u,v))
            if ok: out.append((math.degrees(math.acos(min(1.0,abs(nv.z)))),nv.z))
    return out

def classify(f):
    sm=samples(f)
    if sm is None: return "angled hole", f.area*100
    if not sm: return None, 0.0
    sl=[a for a,_ in sm]
    if max(sl)<SLOPE_MIN: return None, 0.0            # flat
    if min(sl)>SLOPE_MAX: return None, 0.0            # wall
    a=f.area*100
    zs=[v.geometry.z*10 for v in f.vertices]
    if not zs or (max(zs)-min(zs))<MIN_FACE_DROP: return "no vertical extent", a
    mz=sum(z for _,z in sm)/len(sm)
    if mz<0: return "FACES DOWN", a
    return "machinable", a

def run(_context: str):
    app=adsk.core.Application.get()
    des=adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    cam=adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    print(f"{'sheet':<8}{'part':<22}{'machinable':>11}{'facesDOWN':>11}"
          f"{'angledHole':>11}{'noZ':>7}  verdict")
    for i in range(cam.setups.count):
        s=cam.setups.item(i); names={m.name for m in s.models}
        rows=[]
        for occ in des.rootComponent.allOccurrences:
            if occ.name not in names: continue
            for b in occ.bRepBodies:
                if not b.isSolid: continue
                agg=collections.Counter(); mach=[]
                tight=0
                for f in b.faces:
                    k,a=classify(f)
                    if k is None: continue
                    agg[k]+=a
                    if k=="machinable":
                        mach.append(a)
                        g=f.geometry
                        if g.objectType==adsk.core.Cylinder.classType() and g.radius*10<BALL_R:
                            tight+=1
                if not agg: continue
                ok = bool(mach) and (max(mach)>=MIN_3D_FACE or
                                     (len(mach)>=MIN_3D_COUNT and sum(mach)>=MIN_3D_GROUP))
                if ok: verdict="IN 3D pass"
                elif agg["FACES DOWN"]>100: verdict="*** UPSIDE DOWN - flip it"
                elif mach: verdict="skipped: too small"
                else: verdict="skipped: nothing machinable"
                if tight: verdict += f" (+{tight} radii < ball)"
                rows.append((occ.name.split(':')[0].strip(), sum(mach),
                             agg["FACES DOWN"], agg["angled hole"],
                             agg["no vertical extent"], verdict))
        for nm,m,d,h,z,v in sorted(rows,key=lambda r:-(r[1]+r[2])):
            print(f"{s.name.split(' - ')[0]:<8}{nm:<22}{m:11.1f}{d:11.1f}{h:11.1f}{z:7.1f}  {v}")
