#!/usr/bin/env python3
"""archive_wechat.py - Web/WeChat article archiver."""
import os, sys, re, json, base64, urllib.request, html as html_mod, urllib.parse
from datetime import datetime; from pathlib import Path

WP_USER = os.environ.get("WP_USER","Edwardai"); WP_PASS = os.environ.get("WP_APP_PASSWORD","")
WP_URL = os.environ.get("WP_SITE_URL","https://www.token2x.com"); WP_API = f"{WP_URL}/wp-json/wp/v2"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MSG = {"dl":"Fetching","ok":"OK","imgs":"Images","up":"Uploading","pub":"Published","done":"Complete","local":"Local","src":"Original link","foot":"Archived by Codex"}

def fetch(url, ref=None):
    h = {"User-Agent":UA}
    if ref: h["Referer"]=ref
    return urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=30).read()

def dec(data):
    for e in ["utf-8","gbk","gb2312"]:
        try: return data.decode(e)
        except: continue
    return data.decode("utf-8",errors="replace")

def safe(s,m=60): return re.sub(r'[\\/:*?"<>|]',"_",s)[:m]
def ext(url,ct=""):
    for k,v in [("wx_fmt=jpeg","jpg"),("wx_fmt=png","png"),("wx_fmt=gif","gif")]:
        if k in url or k in ct: return v
    _,e = os.path.splitext(urllib.parse.urlparse(url).path); return e.lstrip(".") or "jpg"

def title(h):
    t = re.search(r'og:title" content="([^"]+)"',h)
    if t: return t.group(1)
    for m in re.finditer(r"<h1[^>]*>([^<]+)</h1>",h):
        if len(m.group(1).strip())>8: return m.group(1).strip()
    t = re.search(r"<title>([^<]+)</title>",h)
    if t:
        s = t.group(1).strip()
        for sep in [" - "," | "]:
            if sep in s: return s.split(sep)[0]
        return s
    return "Untitled"

def body(h,u):
    wx = "mp.weixin.qq.com" in u
    if wx:
        m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script',h,re.DOTALL)
        if m: return m.group(1),True
    for t in ["article"]:
        m = re.search(rf"<{t}[^>]*>([\s\S]*?)</{t}>",h,re.I)
        if m and len(m.group(1))>500: return m.group(1),wx
    for c in ["article-content","entry-content","post-content","content","article","main-content","right-c-content-con"]:
        m = re.search(rf'class="[^"]*{c}[^"]*"[^>]*>([\s\S]*?)</(?:div|section)>',h,re.I)
        if m and len(m.group(1))>500: return m.group(1),wx
    m = re.search(r"<body[^>]*>([\s\S]*)</body>",h,re.I)
    return (m.group(1),wx) if m else (h,wx)

def clean(b,wx):
    for t in ["script","style","noscript","iframe"]:
        b = re.sub(rf"<{t}[^>]*>[\s\S]*?</{t}>","",b,flags=re.I)
    if wx:
        b = re.sub(r'<img[^>]*data-src="([^"]+)"[^>]*>',lambda m: f'<img src="{m.group(1)}" alt=""/>',b)
        b = re.sub(r'\s+type="block"',"",b); b = re.sub(r'\s+data-[^=]+="[^"]*"',"",b)
        for c in ["#ffffff","#f0f4fa","#fff"]:
            b = b.replace(f"color: {c}","").replace(f"color:{c}","")
    else:
        for t in ["nav","header","footer","aside"]:
            b = re.sub(rf"<{t}[^>]*>[\s\S]*?</{t}>","",b,flags=re.I)
        for k in ["nav","menu","sidebar","footer","header","bread","crumb"]:
            b = re.sub(rf'<div[^>]*class="[^"]*{k}[^"]*"[^>]*>[\s\S]*?</div>',"",b,flags=re.I)
        b = re.sub(r"<!--.*?-->","",b,flags=re.DOTALL)
        # Strip lazy load: replace src with data-src, remove lazy attributes
        b = re.sub(r'<img([^>]*)src="[^"]*"([^>]*)data-src="([^"]+)"([^>]*)>',r'<img\1src="\3"\2\4>',b)
        b = re.sub(r'\s+data-lazy-type="[^"]*"',"",b)
        b = re.sub(r'\s+class="lazy[^"]*"',' class="wp-image"',b)
        b = re.sub(r'\s+data-src="[^"]*"',"",b)
        b = re.sub(r'<noscript>[\s\S]*?</noscript>',"",b,flags=re.I)
    b = re.sub(r"<span[^>]*>\s*</span>","",b); b = re.sub(r"<p>\s*</p>","",b)
    return b.strip()

def absurl(h,p):
    def f(m):
        a = m.group(1)
        if a.startswith("http") or a.startswith("data:"): return m.group(0)
        u = urllib.parse.urljoin(p,a)
        r = m.group(0).replace(f'src="{a}"',f'src="{u}"').replace(f'href="{a}"',f'href="{u}"')
        return r
    h = re.sub(r'src="([^"]+)"',f,h); h = re.sub(r'href="([^"]+)"',f,h); return h

def imgs(b):
    u = re.findall(r'src="(https?://[^"]+)"',b) + re.findall(r'data-src="(https?://[^"]+)"',b)
    return list(dict.fromkeys(u))

def dlimgs(u,d,r=None):
    (Path(d)/"images").mkdir(parents=True,exist_ok=True); res=[]
    for i,url in enumerate(u):
        fn = f"img_{i+1:02d}.{ext(url)}"; p = Path(d)/"images"/fn
        try: p.write_bytes(fetch(url,r)); res.append((url,fn,str(p)))
        except: pass
    return res

def arch(title,b,m,o,s,wx):
    if wx:
        b = re.sub(r'<img[^>]*data-src="([^"]+)"[^>]*>',lambda x: f'<img src="images/{m.get(x.group(1),"")}" alt=""/>' if x.group(1) in m else x.group(0),b)
    else:
        b = re.sub(r'src="(https?://[^"]+)"',lambda x: f'<img src="images/{m.get(x.group(1),"")}" alt=""/>' if x.group(1) in m else x.group(0),b)
    htm = f"""<!DOCTYPE html><html><head><meta charset=UTF-8><title>{html_mod.escape(title)}</title>
<style>body{{max-width:720px;margin:0 auto;padding:20px;font-family:-apple-system,PingFang SC,system-ui,sans-serif;font-size:15px;line-height:1.7;color:#333}}
h1{{font-size:20px;text-align:center}}h2{{font-size:16px}}img{{max-width:100%;height:auto;display:block;margin:12px auto}}
.meta{{text-align:center;color:#888;font-size:13px}}</style></head><body>
<h1>{html_mod.escape(title)}</h1><div class=meta>{MSG["src"]} <a href={html_mod.escape(s)}>{html_mod.escape(s)}</a></div><hr>
{b}<hr>
<blockquote><p style=color:#888;font-size:13px;margin:0>{MSG["foot"]} | <a href={html_mod.escape(s)}>{MSG["src"]}</a></p></blockquote></body></html>"""
    (Path(o)/"index.html").write_text(htm,encoding="utf-8"); return str(Path(o)/"index.html")

def wp(title,b,imgs,u,wx):
    if not WP_PASS: return None
    ah = "Basic "+base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
    hd = {"Authorization":ah,"User-Agent":"WA-Archiver"}
    um = {}; first_media = None
    if imgs:
        for old,fn,p in imgs:
            try:
                with open(p,"rb") as f: d=f.read()
                bn = "----"+os.urandom(8).hex()
                pl = b"--"+bn.encode()+b'\r\nContent-Disposition: form-data; name="file"; filename="'+fn.encode()+b'"\r\nContent-Type: image/jpeg\r\n\r\n'+d+b"\r\n--"+bn.encode()+b"--\r\n"
                media = json.loads(urllib.request.urlopen(urllib.request.Request(WP_API+"/media",data=pl,headers={**hd,"Content-Type":"multipart/form-data; boundary="+bn},method="POST"),timeout=60).read().decode())
                wu = media.get("source_url") or media["guid"]["rendered"]; um[old]=wu
                if first_media is None: first_media = media["id"]
            except: pass
    c = b
    for o,n in um.items(): c=c.replace(f'"{o}"',f'"{n}"')
    c = re.sub(r'<img ', '<img data-no-lazy=1 ', c)
    wpc = f'<blockquote><p>{MSG["src"]}: <a href="{u}">{u}</a></p></blockquote>\n<div style="font-size:14px;line-height:1.7">\n{c}\n</div>\n<hr>\n<blockquote><p style="color:#888;font-size:13px;margin:0">{MSG["foot"]} | <a href="{u}">{MSG["src"]}</a></p></blockquote>'
    slug = safe(title).lower()[:50].replace("_","-")
    post_data = {"title":title,"content":wpc,"status":"draft","categories":[10],"slug":slug}
    if first_media: post_data["featured_media"] = first_media
    m3 = re.search(r"<p>([^<]{30,200})</p>", c)
    if m3: post_data["excerpt"] = re.sub(r"<[^>]+>", "", m3.group(1)).strip()
    post = json.loads(urllib.request.urlopen(urllib.request.Request(WP_API+"/posts",data=json.dumps(post_data).encode(),headers={**hd,"Content-Type":"application/json"},method="POST"),timeout=30).read().decode())
    urllib.request.urlopen(urllib.request.Request(WP_API+f"/posts/{post['id']}",data=json.dumps({"content":wpc,"status":"publish"}).encode(),headers={**hd,"Content-Type":"application/json"},method="POST"),timeout=30).read()
    return post["link"]

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("--html-file", help="Pre-fetched HTML file path (skip network fetch)")
    ap.add_argument("--wp", action="store_true")
    ap.add_argument("--output", "-o")
    a = ap.parse_args()
    if a.html_file:
        print(f"Reading HTML from: {a.html_file}")
        raw = open(a.html_file, "rb").read()
        htm = dec(raw)
    else:
        print(f"{MSG['dl']}: {a.url}")
        raw = fetch(a.url)
        htm = dec(raw)
    wx = "mp.weixin.qq.com" in a.url
    t = title(htm).replace("\ufffd","").replace("\xa0"," ").strip(); print(f"  {t[:80]}")
    b,_ = body(htm,a.url); b = clean(b,wx).replace("\ufffd","").replace("\xa0"," ")
    if not wx: b = absurl(b,a.url)
    im = imgs(b); print(f"  {MSG['imgs']}: {len(im)}")
    o = a.output or f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe(t)}"; Path(o).mkdir(parents=True,exist_ok=True)
    inf = dlimgs(im,o,a.url if wx else None)
    arch(t,b,{x[0]:x[1] for x in inf},o,a.url,wx)
    print(f"  {MSG['local']}: {os.path.abspath(o)}/index.html")
    if a.wp:
        l = wp(t,b,inf,a.url,wx)
        if l: print(f"  {MSG['pub']}: {l}")
    print(f"\n{MSG['done']}. {len(inf)}/{len(im)} {MSG['imgs']}")

if __name__=="__main__": main()
