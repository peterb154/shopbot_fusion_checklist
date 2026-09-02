import json,sys,urllib.request

URL="http://127.0.0.1:27182/mcp"
SID=None

def rpc(method,params=None,notify=False):
    global SID
    body={"jsonrpc":"2.0","method":method}
    if params is not None: body["params"]=params
    if not notify: body["id"]=1
    h={"Content-Type":"application/json","Accept":"application/json, text/event-stream"}
    if SID: h["Mcp-Session-Id"]=SID
    req=urllib.request.Request(URL,data=json.dumps(body).encode(),headers=h,method="POST")
    with urllib.request.urlopen(req,timeout=120) as r:
        if not SID and r.headers.get("Mcp-Session-Id"): SID=r.headers["Mcp-Session-Id"]
        raw=r.read().decode()
    if notify or not raw.strip(): return None
    # handle SSE framing
    if raw.lstrip().startswith("event:") or raw.lstrip().startswith("data:"):
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw=line[5:].strip(); break
    return json.loads(raw)

def start():
    rpc("initialize",{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"qa","version":"1"}})
    rpc("notifications/initialized",{},notify=True)

def call(name,args=None):
    r=rpc("tools/call",{"name":name,"arguments":args or {}})
    if "error" in r: return "ERROR: "+json.dumps(r["error"])
    out=[]
    for c in r.get("result",{}).get("content",[]):
        out.append(c.get("text",json.dumps(c)))
    return "\n".join(out)

if __name__=="__main__":
    start()
    if sys.argv[1]=="list":
        r=rpc("tools/list",{})
        for t in r["result"]["tools"]:
            print(f"- {t['name']}: {(t.get('description') or '')[:150]}")
    else:
        print(call(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv)>2 else {}))
