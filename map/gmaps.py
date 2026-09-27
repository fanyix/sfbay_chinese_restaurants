import urllib.request, urllib.parse, re, json, sys, time
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
def get(u):
    r=urllib.request.Request(u,headers={'User-Agent':UA,'Accept-Language':'en-US,en;q=0.9'})
    return urllib.request.urlopen(r,timeout=25).read().decode('utf-8','replace')
def lookup(q):
    page=get('https://www.google.com/maps/search/?api=1&query='+urllib.parse.quote_plus(q))
    m=re.search(r'search\?tbm=map[^"]*',page)
    if not m: return None,'no-endpoint'
    u=m.group(0).replace('&amp;','&').replace('\\u0026','&')
    txt=get('https://www.google.com/'+u)
    return txt,None
def pb_template(cache, q='Chinese restaurant in Daly City, CA'):
    """Paginated Maps search URL (path after google.com/) for query q, cached to a file. Callers swap the query text."""
    import os
    if os.path.exists(cache): return open(cache).read()
    page=get('https://www.google.com/maps/search/?api=1&query='+urllib.parse.quote_plus(q))
    m=re.search(r'search\?tbm=map[^"]*',page)
    if not m: raise SystemExit('Google Maps search endpoint not found; page format changed')
    u=m.group(0).replace('&amp;','&').replace('\\u0026','&')
    open(cache,'w').write(u)
    return u
def walk(o,f,path=()):
    f(o,path)
    if isinstance(o,list):
        for i,x in enumerate(o): walk(x,f,path+(i,))
if __name__=='__main__':
    txt,_=lookup(sys.argv[1])
    data=json.loads(txt[4:] if txt.startswith(")]}'") else txt)
    open('/tmp/last.json','w').write(json.dumps(data))
    hits=[]
    walk(data,lambda o,p: hits.append((p,o)) if o in ('CLOSED','OPERATIONAL','CLOSED_TEMPORARILY','CLOSED_PERMANENTLY') else None)
    print(hits[:5])
    # print strings near
    s=json.dumps(data)
    for m in re.finditer(r'"(CLOSED|OPERATIONAL|CLOSED_\w+)"',s): print(s[max(0,m.start()-200):m.end()+80]); print('---')
