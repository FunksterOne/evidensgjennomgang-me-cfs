import openpyxl, math
wb = openpyxl.load_workbook('ActPac_data.xlsx', data_only=True)
ws = wb['ActPac data']
rows = list(ws.iter_rows(values_only=True))[2:]  # data rows (header at idx1)

def num(x):
    try: return float(x)
    except: return None

# metafor SMD (Hedges g, vtype LS) + REML random effects
def hedges(m1,s1,n1,m2,s2,n2):
    sp = math.sqrt(((n1-1)*s1*s1 + (n2-1)*s2*s2)/(n1+n2-2))
    d  = (m1-m2)/sp
    J  = 1 - 3/(4*(n1+n2-2)-1)
    g  = J*d
    v  = 1.0/n1 + 1.0/n2 + g*g/(2*(n1+n2))
    return g, v

def md(m1,s1,n1,m2,s2,n2):
    v = s1*s1/n1 + s2*s2/n2
    return (m1-m2), v

def reml_tau2(y,v):
    t2=0.0
    for _ in range(200):
        w=[1/(vi+t2) for vi in v]
        sw=sum(w); mu=sum(wi*yi for wi,yi in zip(w,y))/sw
        num_=sum(wi*wi*((yi-mu)**2 - vi) for wi,yi,vi in zip(w,y,v))
        den_=sum(wi*wi for wi in w)
        new=max(0.0,t2+ (num_/den_) ) if den_>0 else 0.0
        # damped fixed-point (Viechtbauer REML); simple iteration
        new=max(0.0, (sum(wi*wi*((yi-mu)**2 - vi) for wi,yi,vi in zip(w,y,v)) + t2*den_)/den_)
        if abs(new-t2)<1e-10: t2=new; break
        t2=new
    return t2

def pool(y,v):
    t2=reml_tau2(y,v)
    w=[1/(vi+t2) for vi in v]; sw=sum(w)
    mu=sum(wi*yi for wi,yi in zip(w,y))/sw
    se=math.sqrt(1/sw)
    # Q with FE weights
    wf=[1/vi for vi in v]; swf=sum(wf)
    muf=sum(wi*yi for wi,yi in zip(wf,y))/swf
    Q=sum(wi*(yi-muf)**2 for wi,yi in zip(wf,y))
    df=len(y)-1
    I2=max(0.0,(Q-df)/Q*100) if Q>0 else 0.0
    return mu,mu-1.96*se,mu+1.96*se,I2,len(y),t2

def block(flag_i, ma_i, ni,mi,si, nc,mc,sc, measure='SMD', label=''):
    groups={'Pacing':[],'Pacing up':[]}
    rowsused=[]
    for r in rows:
        if r[0] is None: continue
        if str(r[flag_i]).strip()=='Yes' and str(r[ma_i]).strip()=='Yes':
            vals=[num(r[ni]),num(r[mi]),num(r[si]),num(r[nc]),num(r[mc]),num(r[sc])]
            if any(v is None for v in vals): continue
            n1,m1,s1,n2,m2,s2=vals
            g,v=(hedges if measure=='SMD' else md)(m1,s1,int(n1),m2,s2,int(n2))
            grp=str(r[2]).strip()
            groups.setdefault(grp,[]).append((g,v))
            rowsused.append((r[0],r[1],grp,r[3],round(g,3)))
    print(f"\n=== {label} ({measure}) ===")
    allg=[g for grp in groups.values() for g,_ in grp]
    allv=[v for grp in groups.values() for _,v in grp]
    if allg:
        mu,lo,hi,I2,k,t2=pool(allg,allv)
        print(f"  OVERALL : est={mu:+.3f}  95%CI [{lo:+.3f},{hi:+.3f}]  I2={I2:.1f}%  k={k}")
    for grp in ['Pacing','Pacing up']:
        gg=groups.get(grp,[])
        if len(gg)>=1:
            y=[a for a,_ in gg]; vv=[b for _,b in gg]
            if len(gg)==1:
                mu=y[0]; se=math.sqrt(vv[0]); lo,hi,I2,k=mu-1.96*se,mu+1.96*se,0.0,1
            else:
                mu,lo,hi,I2,k,t2=pool(y,vv)
            tag='pacing (oppretthold)' if grp=='Pacing' else 'pacing up (gradert økning)'
            print(f"  {tag:28s}: est={mu:+.3f}  95%CI [{lo:+.3f},{hi:+.3f}]  I2={I2:.1f}%  k={k}")
    return rowsused

ru = block(20,21,23,24,25,26,27,28,'SMD','UTMATTELSE — etter intervensjon')
block(33,34,36,37,38,39,40,41,'MD','FYSISK FUNKSJON — etter (MD)')
block(59,60,62,63,64,65,66,67,'SMD','DEPRESJON — etter')
block(72,73,75,76,77,78,79,80,'SMD','ANGST — etter')
block(85,86,88,89,90,91,92,93,'SMD','UTMATTELSE — oppfølging')

print("\n\n=== Studie-til-subgruppe (utmattelse etter) + aldersgruppe ===")
for a,y,grp,age,g in ru:
    print(f"  {str(a):14s} {y}  [{grp:9s}]  {age}  g={g:+.3f}")
