import pyreadr, math
d = pyreadr.read_r('environment_CFS.RData')['data'].reset_index(drop=True)

# R 1-indexed row selections from R-script_CFS.R
post_R   = [1,4,6,8,12,13,15,16,17,19,21,23,25,28,31]
FU12_R   = [2,5,7,10,14,18,20,22,27,29]
FUinf_R  = [3,11,30]
def Rsel(df, ridx): return df.iloc[[i-1 for i in ridx]].reset_index(drop=True)
data_post = Rsel(d, post_R)
data_FU12 = Rsel(d, FU12_R)
data_FUinf= Rsel(d, FUinf_R)

# within-data_post positional selections (1-indexed) per script
sel = {
 'som' : [1,2,3,4,5,7,8,11,12,14,15],
 'phs' : [1,2,3,4,5,7,9,11,12,14,15],
}
def hedges(m1,s1,n1,m2,s2,n2):
    sp=math.sqrt(((n1-1)*s1*s1+(n2-1)*s2*s2)/(n1+n2-2))
    d_=(m1-m2)/sp
    J=1-3/(4*(n1+n2-2)-1)
    g=J*d_
    v=1.0/n1+1.0/n2+g*g/(2*(n1+n2))
    return g,v
def reml(y,v):
    t2=0.0
    for _ in range(500):
        w=[1/(vi+t2) for vi in v]; sw=sum(w)
        mu=sum(wi*yi for wi,yi in zip(w,y))/sw
        den=sum(wi*wi for wi in w)
        new=max(0.0,(sum(wi*wi*((yi-mu)**2-vi) for wi,yi,vi in zip(w,y,v))+t2*den)/den)
        if abs(new-t2)<1e-12: t2=new;break
        t2=new
    w=[1/(vi+t2) for vi in v]; sw=sum(w)
    mu=sum(wi*yi for wi,yi in zip(w,y))/sw
    se=math.sqrt(1/sw)
    wf=[1/vi for vi in v]; swf=sum(wf); muf=sum(wi*yi for wi,yi in zip(wf,y))/swf
    Q=sum(wi*(yi-muf)**2 for wi,yi in zip(wf,y)); df=len(y)-1
    I2=max(0.0,(Q-df)/Q*100) if Q>0 else 0.0
    return mu,mu-1.96*se,mu+1.96*se,I2,len(y),t2

def ma(df, oc, rows1, label):
    sub=df.iloc[[i-1 for i in rows1]].reset_index(drop=True)
    y=[];v=[]
    for _,r in sub.iterrows():
        try:
            ne=float(r[f'Ne_analysis_{oc}']); nc=float(r[f'Nc_analysis_{oc}'])
            me=float(r[f'Me_{oc}_post']); sde=float(r[f'SDe_{oc}_post'])
            mc=float(r[f'Mc_{oc}_post']); sdc=float(r[f'SDc_{oc}_post'])
        except: continue
        if any(math.isnan(x) for x in [ne,nc,me,sde,mc,sdc]): continue
        g,vv=hedges(me,sde,int(ne),mc,sdc,int(nc)); y.append(g);v.append(vv)
    if not y: print(label,'-- no data'); return
    mu,lo,hi,I2,k,t2=reml(y,v)
    print(f"{label:42s} g={mu:+.3f}  CI[{lo:+.3f},{hi:+.3f}]  I2={I2:.1f}%  k={k}")

print("=== POST-TREATMENT (data_post, positional subsets per R) ===")
ma(data_post,'som',sel['som'],'Fatigue post')
ma(data_post,'phs',sel['phs'],'PHS post')
# depression/anxiety post: script selects which rows? find non-NA
for oc in ['depr','anx']:
    sub=data_post.copy()
    rows=[i+1 for i in range(len(sub)) if not (str(sub.iloc[i].get(f'Me_{oc}_post','nan'))=='nan' or (isinstance(sub.iloc[i].get(f'Me_{oc}_post'),float) and math.isnan(sub.iloc[i].get(f'Me_{oc}_post'))))]
    ma(data_post,oc,rows,f'{oc} post (non-NA k)')

print("\n=== LONG-TERM FOLLOW-UP (data_FU12) ===")
for oc in ['som','phs','depr','anx']:
    sub=data_FU12.copy()
    rows=[i+1 for i in range(len(sub)) if not (isinstance(sub.iloc[i].get(f'Me_{oc}_post'),float) and math.isnan(sub.iloc[i].get(f'Me_{oc}_post')))]
    ma(data_FU12,oc,rows,f'{oc} long-term FU')

print("\n=== FOLLOW-UP TIMING (the months/weeks question) ===")
for c in d.columns:
    cl=c.lower()
    if cl in ('follow-up','post_assess...5','post_assess...137') or 'assess' in cl and oc=='':
        pass
cols_show=['author','year','follow-up','post_assess...5','post_assess...137']
cols_show=[c for c in cols_show if c in d.columns]
print('FU12 rows timing:')
print(data_FU12[cols_show].to_string())
print('\nFUinf rows timing:')
print(data_FUinf[cols_show].to_string())

print("\n=== DIAGNOSEKRITERIER (Maas egen ekstraksjon) ===")
for c in ['diagnosis_criteria','diagnosis_which','diagnosis_how']:
    if c in d.columns:
        print(c,':', list(d[c].dropna().unique()))
print("\nPost-treatment studies diagnosis_criteria:")
print(data_post[['author','diagnosis_criteria']].to_string())

print("\n=== KONTROLLGRUPPE-SUBGRUPPE (komparator-inflasjon) ===")
print("control-koder i data_post:", list(data_post['control'].unique()))
# fatigue post by control type
sub=data_post.iloc[[i-1 for i in sel['som']]].reset_index(drop=True)
groups={}
for _,r in sub.iterrows():
    try:
        ne=float(r['Ne_analysis_som']);nc=float(r['Nc_analysis_som'])
        me=float(r['Me_som_post']);sde=float(r['SDe_som_post'])
        mc=float(r['Mc_som_post']);sdc=float(r['SDc_som_post'])
        ctrl=str(r['control'])
    except: continue
    if any(math.isnan(x) for x in [ne,nc,me,sde,mc,sdc]): continue
    g,vv=hedges(me,sde,int(ne),mc,sdc,int(nc))
    groups.setdefault(ctrl,[]).append((g,vv,r['author']))
for ctrl,items in groups.items():
    y=[a for a,_,_ in items];v=[b for _,b,_ in items]
    if len(y)>=2:
        mu,lo,hi,I2,k,t2=reml(y,v)
        print(f"  control='{ctrl}': g={mu:+.3f} CI[{lo:+.3f},{hi:+.3f}] I2={I2:.1f}% k={k}")
    else:
        print(f"  control='{ctrl}': k={len(y)} (for lite) studies={[x[2] for x in items]}")
print("  studier per kontrolltype:")
for ctrl,items in groups.items():
    print(f"   {ctrl}: {[x[2] for x in items]}")
