#!/usr/bin/env python3
"""自托管主页资源生成器：抓取真实 GitHub 数据，渲染单张合并大图 dashboard.svg
（whoami 终端 + 技能雷达 + 战绩 + 最近动态 + 入学喜讯 + 状态栏）。
零第三方依赖。由 .github/workflows/profile-refresh.yml 定时调用，也可本地运行。"""
import os, json, urllib.request, datetime

# —— 手动维护：学术指标（来自 Google Scholar）——
PUBLICATIONS, CITATIONS, HINDEX = 11, 23, 4
# —— 手动维护：入学/履历喜讯 ——
INCOMING_WHEN = "2026.09"
INCOMING_TEXT = "南京大学 × 北京中关村学院 · 联合培养博士"

USER  = os.environ.get("GH_USER", "bupterlxp")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HDR   = {"Accept": "application/vnd.github+json", "User-Agent": "profile-bot"}
if TOKEN:
    HDR["Authorization"] = "token " + TOKEN

def api(path):
    req = urllib.request.Request("https://api.github.com" + path, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))

def bar(value, ref, cap=250):
    return max(25, min(cap, round(value / ref * cap)))

def season_skin():
    """按日期自动切换的节日皮肤；返回标题栏徽章文字（空串=无）。"""
    t = datetime.date.today()
    if t.year == 2026 and ((t.month == 6 and t.day >= 11) or (t.month == 7 and t.day <= 20)):
        d = (datetime.date(2026, 7, 20) - t).days
        tail = f" · FINAL T-{d}d" if d > 0 else " · FINAL TODAY!"
        return "⚽ WORLD CUP 2026" + tail
    if (t.month == 1 and t.day >= 20) or (t.month == 2 and t.day <= 20):
        return "🏮 新春快乐"
    if t.month == 10 and t.day <= 7:
        return "🇨🇳 国庆快乐"
    if (t.month == 12 and t.day >= 20) or (t.month == 1 and t.day <= 2):
        return "🎄 Happy New Year"
    return ""

def write_arxiv():
    """从 arXiv API 抓一篇最新 cs.CL 论文，渲染「今日精选」卡。失败则保留旧图/占位。"""
    import xml.etree.ElementTree as ET
    title, author, link = None, "—", "https://arxiv.org/list/cs.CL/recent"
    try:
        url = ("http://export.arxiv.org/api/query?search_query=cat:cs.CL"
               "&sortBy=submittedDate&sortOrder=descending&max_results=1")
        req = urllib.request.Request(url, headers={"User-Agent": "profile-bot"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode("utf-8")
        ns = {"a": "http://www.w3.org/2005/Atom"}
        e = ET.fromstring(data).find("a:entry", ns)
        title = " ".join(e.find("a:title", ns).text.split())
        authors = [a.find("a:name", ns).text for a in e.findall("a:author", ns)]
        author = authors[0] + (" et al." if len(authors) > 1 else "")
        link = e.find("a:id", ns).text.strip()
    except Exception as ex:
        print("arxiv fetch failed:", ex)
        if os.path.exists("assets/arxiv.svg"):
            return
        title = "arXiv cs.CL — see latest submissions"
    t1, t2 = esc(title[:62]), esc(title[62:120])
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 150" width="1000" height="150" fill="none" font-family="'Courier New',monospace">
  <defs>
    <linearGradient id="g1" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00f0ff"/><stop offset="0.5" stop-color="#a855f7"/><stop offset="1" stop-color="#ff00e5"/></linearGradient>
    <filter id="fs" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <pattern id="agrid" width="30" height="30" patternUnits="userSpaceOnUse"><path class="grd" d="M30 0 L0 0 0 30" fill="none" stroke="#0f1d33" stroke-width="1"/></pattern>
    <style>.bg{{fill:#07070d}}.grd{{stroke:#0f1d33}}.txt{{fill:#cfe3ff}}
      @media (prefers-color-scheme: light){{.bg{{fill:#f4f8fe}}.grd{{stroke:#dbe6f5}}.txt{{fill:#1f2d44}}}}</style>
  </defs>
  <rect class="bg" x="3" y="3" width="994" height="144" rx="14" fill="#07070d" stroke="url(#g1)" stroke-width="2"/>
  <rect x="3" y="3" width="994" height="144" rx="14" fill="url(#agrid)" opacity="0.5"/>
  <circle cx="34" cy="38" r="6" fill="#ff4fd8" filter="url(#fs)"><animate attributeName="opacity" values="1;0.3;1" dur="1.5s" repeatCount="indefinite"/></circle>
  <text x="52" y="43" font-size="16" font-weight="bold" fill="#00f0ff" letter-spacing="2">// arXiv PICK OF THE DAY · cs.CL</text>
  <text class="txt" x="34" y="80" font-size="17" font-weight="bold" fill="#cfe3ff">{t1}</text>
  <text class="txt" x="34" y="104" font-size="17" font-weight="bold" fill="#cfe3ff">{t2}</text>
  <text x="34" y="130" font-size="13" fill="#a855f7">{esc(author)}</text>
  <text x="966" y="130" text-anchor="end" font-size="12" fill="#7fdfff">{esc(link)}</text>
</svg>'''
    open("assets/arxiv.svg", "w", encoding="utf-8").write(svg)
    print("generated arxiv.svg")

def main():
    user  = api(f"/users/{USER}")
    repos = api(f"/users/{USER}/repos?per_page=100&sort=pushed")
    owned = [r for r in repos if not r["fork"]]
    followers = user["followers"]
    public    = user["public_repos"]
    stars     = sum(r["stargazers_count"] for r in owned)
    since     = user["created_at"][:4]
    latest    = next((r for r in owned if r["name"].lower() != USER.lower()), owned[0])
    name = esc(latest["name"]); desc = esc((latest.get("description") or "—")[:74])
    lang = esc(latest.get("language") or "—"); when = latest["pushed_at"][:10]
    bp, bc, br, bs = bar(PUBLICATIONS,15), bar(CITATIONS,30), bar(public,15), bar(max(stars,1),10)

    os.makedirs("assets", exist_ok=True)
    season = season_skin()
    season_el = (f'<text x="560" y="40" text-anchor="middle" font-size="14" font-weight="bold" fill="#28c840" filter="url(#fs)">{season}</text>') if season else ""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 900" width="1000" height="900" fill="none" font-family="'Courier New',monospace">
  <defs>
    <linearGradient id="g1" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00f0ff"/><stop offset="0.5" stop-color="#a855f7"/><stop offset="1" stop-color="#ff00e5"/></linearGradient>
    <linearGradient id="scan" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00f0ff" stop-opacity="0"/><stop offset="0.5" stop-color="#00f0ff" stop-opacity="0.4"/><stop offset="1" stop-color="#00f0ff" stop-opacity="0"/></linearGradient>
    <filter id="fg" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="fs" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <pattern id="grid" width="34" height="34" patternUnits="userSpaceOnUse"><path class="grd" d="M34 0 L0 0 0 34" fill="none" stroke="#0f1d33" stroke-width="1"/></pattern>
    <style>
      .bg{{fill:#07070d}}.grd{{stroke:#0f1d33}}.ln{{stroke:#1b2b45}}.lbl{{fill:#7fdfff}}.txt{{fill:#cfe3ff}}
      @media (prefers-color-scheme: light){{
        .bg{{fill:#f4f8fe}}.grd{{stroke:#dbe6f5}}.ln{{stroke:#b3c7e3}}.lbl{{fill:#2b4a73}}.txt{{fill:#1f2d44}}
      }}
    </style>
  </defs>

  <!-- frame -->
  <rect class="bg" x="3" y="3" width="994" height="894" rx="18" fill="#07070d" stroke="url(#g1)" stroke-width="2"><animate attributeName="opacity" values="0.9;1;0.9" dur="3s" repeatCount="indefinite"/></rect>
  <rect x="3" y="3" width="994" height="894" rx="18" fill="url(#grid)" opacity="0.5"/>
  <rect x="-300" y="0" width="300" height="900" fill="url(#scan)" opacity="0.10"><animate attributeName="x" values="-300;1000" dur="7s" repeatCount="indefinite"/></rect>

  <!-- title bar -->
  <text x="30" y="40" font-size="22" font-weight="bold" fill="#00f0ff" filter="url(#fs)" letter-spacing="2">// XINPING LEI — CONTROL DECK</text>
  <text x="970" y="40" text-anchor="end" font-size="14" font-weight="bold" fill="#28c840">● ONLINE<animate attributeName="opacity" values="1;0.3;1" dur="1.6s" repeatCount="indefinite"/></text>
  {season_el}
  <line x1="20" y1="56" x2="980" y2="56" class="ln" stroke="#1b2b45"/>
  <line x1="552" y1="56" x2="552" y2="420" class="ln" stroke="#1b2b45"/>

  <!-- ===== WHOAMI ===== -->
  <text x="30" y="88" font-size="15" font-weight="bold" fill="#7fdfff" letter-spacing="2">// WHOAMI</text>
  <g font-size="15" filter="url(#fs)">
    <text x="30" y="120" fill="#28c840">$ whoami<animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="0.2s" fill="freeze"/></text>
    <text x="30" y="146" class="txt" fill="#cfe3ff">→ <tspan fill="#00f0ff" font-weight="bold">Xinping Lei</tspan> · LLM/Agent Researcher @ BUPT<animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="0.6s" fill="freeze"/></text>
    <text x="30" y="180" fill="#28c840">$ cat research_focus.txt<animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="1s" fill="freeze"/></text>
    <text x="30" y="206" fill="#a855f7">→ Multi-Agent · Agentic Orchestration<animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="1.4s" fill="freeze"/></text>
    <text x="30" y="230" fill="#a855f7">→ Agentic Coding &amp; Evaluation<animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="1.7s" fill="freeze"/></text>
    <text x="30" y="254" fill="#a855f7">→ LLM Reasoning · Alignment · Ideation<animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="2s" fill="freeze"/></text>
    <text x="30" y="296" fill="#28c840">$ ./mission --now<animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="2.4s" fill="freeze"/></text>
    <text x="30" y="322" fill="#ff4fd8" font-weight="bold">→ build agents that actually work.<tspan fill="#00f0ff">█<animate attributeName="opacity" values="1;0;1" dur="1s" begin="2.9s" repeatCount="indefinite"/></tspan><animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="2.8s" fill="freeze"/></text>
  </g>
  <text x="30" y="372" font-size="13" fill="#5a6b8c">$ uptime → researching since {since} · 北京邮电大学</text>

  <!-- ===== SKILL RADAR (embedded, scaled) ===== -->
  <g transform="translate(566,60) scale(0.88)">
    <text x="220" y="30" text-anchor="middle" font-size="16" font-weight="bold" fill="#00f0ff" filter="url(#fs)" letter-spacing="3">// SKILL RADAR</text>
    <g class="ln" stroke="#1b2b45" stroke-width="1" fill="none">
      <polygon points="220,65 336.9,132.5 336.9,267.5 220,335 103.1,267.5 103.1,132.5"/>
      <polygon points="220,110.9 297.2,155.4 297.2,244.6 220,289.1 142.8,244.6 142.8,155.4"/>
      <polygon points="220,155.45 258.6,177.7 258.6,222.3 220,244.55 181.4,222.3 181.4,177.7"/>
    </g>
    <g stroke="#12243d" stroke-width="1">
      <line x1="220" y1="200" x2="220" y2="65"/><line x1="220" y1="200" x2="336.9" y2="132.5"/><line x1="220" y1="200" x2="336.9" y2="267.5"/>
      <line x1="220" y1="200" x2="220" y2="335"/><line x1="220" y1="200" x2="103.1" y2="267.5"/><line x1="220" y1="200" x2="103.1" y2="132.5"/>
    </g>
    <polygon points="220,71.75 327.5,137.9 319.4,257.4 220,308 114.8,260.75 128.8,147.35" fill="url(#g1)" fill-opacity="0" stroke="url(#g1)" stroke-width="2.5" filter="url(#fg)" stroke-dasharray="1200" stroke-dashoffset="1200">
      <animate attributeName="stroke-dashoffset" from="1200" to="0" dur="1.6s" begin="0.4s" fill="freeze"/>
      <animate attributeName="fill-opacity" from="0" to="0.32" dur="1s" begin="1.8s" fill="freeze"/>
    </polygon>
    <g fill="#00f0ff" filter="url(#fs)">
      <circle cx="220" cy="71.75" r="3.5"><animate attributeName="opacity" values="0.4;1;0.4" dur="2s" repeatCount="indefinite"/></circle>
      <circle cx="327.5" cy="137.9" r="3.5" fill="#a855f7"><animate attributeName="opacity" values="0.4;1;0.4" dur="2s" begin="0.3s" repeatCount="indefinite"/></circle>
      <circle cx="319.4" cy="257.4" r="3.5" fill="#ff00e5"><animate attributeName="opacity" values="0.4;1;0.4" dur="2s" begin="0.6s" repeatCount="indefinite"/></circle>
      <circle cx="220" cy="308" r="3.5"><animate attributeName="opacity" values="0.4;1;0.4" dur="2s" begin="0.9s" repeatCount="indefinite"/></circle>
      <circle cx="114.8" cy="260.75" r="3.5" fill="#a855f7"><animate attributeName="opacity" values="0.4;1;0.4" dur="2s" begin="1.2s" repeatCount="indefinite"/></circle>
      <circle cx="128.8" cy="147.35" r="3.5" fill="#ff00e5"><animate attributeName="opacity" values="0.4;1;0.4" dur="2s" begin="1.5s" repeatCount="indefinite"/></circle>
    </g>
    <g font-size="14" font-weight="bold" class="txt" fill="#cfe3ff">
      <text x="220" y="55" text-anchor="middle">LLM</text>
      <text x="348" y="132">Agent</text>
      <text x="348" y="272">Agentic Coding</text>
      <text x="220" y="358" text-anchor="middle">Reasoning</text>
      <text x="92" y="272" text-anchor="end">Ideation</text>
      <text x="92" y="132" text-anchor="end">Systems</text>
    </g>
  </g>

  <!-- ===== STATS ===== -->
  <line x1="20" y1="420" x2="980" y2="420" class="ln" stroke="#1b2b45"/>
  <text x="30" y="452" font-size="18" font-weight="bold" fill="#00f0ff" filter="url(#fs)" letter-spacing="2">// RESEARCH × CODE — STATS</text>
  <g font-weight="bold">
    <text x="40" y="492" class="lbl" font-size="13" fill="#7fdfff" letter-spacing="1">PUBLICATIONS</text>
    <text x="40" y="528" font-size="34" fill="#00f0ff" filter="url(#fg)">{PUBLICATIONS}</text>
    <rect x="40" y="540" height="6" rx="3" fill="#16263f"/><rect x="40" y="540" height="6" rx="3" fill="url(#g1)"><animate attributeName="width" from="0" to="{bp}" dur="1.3s" begin="0.4s" fill="freeze"/></rect>
    <text x="350" y="492" class="lbl" font-size="13" fill="#7fdfff" letter-spacing="1">CITATIONS</text>
    <text x="350" y="528" font-size="34" fill="#a855f7" filter="url(#fg)">{CITATIONS}</text>
    <rect x="350" y="540" height="6" rx="3" fill="#16263f"/><rect x="350" y="540" height="6" rx="3" fill="url(#g1)"><animate attributeName="width" from="0" to="{bc}" dur="1.3s" begin="0.6s" fill="freeze"/></rect>
    <text x="660" y="492" class="lbl" font-size="13" fill="#7fdfff" letter-spacing="1">h-INDEX</text>
    <text x="660" y="528" font-size="34" fill="#ff00e5" filter="url(#fg)">{HINDEX}</text>
    <text x="40" y="576" class="lbl" font-size="13" fill="#7fdfff" letter-spacing="1">PUBLIC REPOS</text>
    <text x="40" y="612" font-size="34" fill="#00f0ff" filter="url(#fg)">{public}</text>
    <rect x="40" y="624" height="6" rx="3" fill="#16263f"/><rect x="40" y="624" height="6" rx="3" fill="url(#g1)"><animate attributeName="width" from="0" to="{br}" dur="1.3s" begin="0.8s" fill="freeze"/></rect>
    <text x="350" y="576" class="lbl" font-size="13" fill="#7fdfff" letter-spacing="1">TOTAL STARS</text>
    <text x="350" y="612" font-size="34" fill="#a855f7" filter="url(#fg)">{stars}</text>
    <rect x="350" y="624" height="6" rx="3" fill="#16263f"/><rect x="350" y="624" height="6" rx="3" fill="url(#g1)"><animate attributeName="width" from="0" to="{bs}" dur="1.3s" begin="1s" fill="freeze"/></rect>
    <text x="660" y="576" class="lbl" font-size="13" fill="#7fdfff" letter-spacing="1">FOLLOWERS · SINCE</text>
    <text x="660" y="612" font-size="34" fill="#ff00e5" filter="url(#fg)">{followers} · {since}</text>
  </g>

  <!-- ===== LATEST SIGNAL ===== -->
  <line x1="20" y1="652" x2="980" y2="652" class="ln" stroke="#1b2b45"/>
  <circle cx="34" cy="684" r="6" fill="#28c840" filter="url(#fs)"><animate attributeName="opacity" values="1;0.3;1" dur="1.5s" repeatCount="indefinite"/></circle>
  <text x="52" y="689" font-size="15" font-weight="bold" fill="#00f0ff" letter-spacing="2">// LATEST SIGNAL · 最近动态</text>
  <text x="34" y="726" font-size="26" font-weight="bold" fill="url(#g1)" filter="url(#fg)">{name}</text>
  <text x="34" y="752" font-size="14" class="txt" fill="#cfe3ff">{desc}</text>
  <text x="966" y="722" text-anchor="end" font-size="14" font-weight="bold" fill="#a855f7">◈ {lang}</text>
  <text x="966" y="748" text-anchor="end" font-size="13" fill="#ff4fd8">⟳ {when}</text>

  <!-- ===== INCOMING (入学喜讯) ===== -->
  <line x1="20" y1="772" x2="980" y2="772" class="ln" stroke="#1b2b45"/>
  <rect x="22" y="782" width="956" height="58" rx="10" fill="#a855f7" fill-opacity="0.08" stroke="url(#g1)" stroke-width="1.4"><animate attributeName="opacity" values="0.6;1;0.6" dur="2.4s" repeatCount="indefinite"/></rect>
  <text x="42" y="808" font-size="14" font-weight="bold" fill="#28c840">▶ INCOMING · {INCOMING_WHEN}</text>
  <text x="42" y="830" font-size="17" font-weight="bold" fill="url(#g1)" filter="url(#fs)">🎓 {INCOMING_TEXT}</text>
  <text class="lbl" x="966" y="820" text-anchor="end" font-size="13" font-weight="bold" fill="#7fdfff">Joint PhD Program · NJU × ZGC Academy</text>

  <!-- ===== STATUS BAR ===== -->
  <line x1="20" y1="852" x2="980" y2="852" class="ln" stroke="#1b2b45"/>
  <circle cx="34" cy="878" r="6" fill="#28c840" filter="url(#fs)"><animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/></circle>
  <text x="50" y="883" font-size="14" font-weight="bold" fill="#28c840">STATUS: RESEARCHING</text>
  <g>
    <rect x="300" y="870" width="15" height="15" rx="2" fill="#00f0ff" filter="url(#fs)"><animate attributeName="opacity" from="0.15" to="1" dur="0.4s" begin="0.2s" fill="freeze"/></rect>
    <rect x="321" y="870" width="15" height="15" rx="2" fill="#00f0ff" filter="url(#fs)"><animate attributeName="opacity" from="0.15" to="1" dur="0.4s" begin="0.5s" fill="freeze"/></rect>
    <rect x="342" y="870" width="15" height="15" rx="2" fill="#a855f7" filter="url(#fs)"><animate attributeName="opacity" from="0.15" to="1" dur="0.4s" begin="0.8s" fill="freeze"/></rect>
    <rect x="363" y="870" width="15" height="15" rx="2" fill="#ff00e5" filter="url(#fs)"><animate attributeName="opacity" from="0.15" to="1" dur="0.4s" begin="1.1s" fill="freeze"/></rect>
    <rect x="384" y="870" width="15" height="15" rx="2" fill="#2a3550"><animate attributeName="opacity" values="0.3;0.6;0.3" dur="1.5s" repeatCount="indefinite"/></rect>
  </g>
  <text x="966" y="883" text-anchor="end" font-size="14" font-weight="bold" fill="#ff4fd8" filter="url(#fs)">LOCATION: BEIJING ⇄ NANJING</text>
</svg>'''
    open("assets/dashboard.svg", "w", encoding="utf-8").write(svg)
    print("generated dashboard.svg")
    write_arxiv()

if __name__ == "__main__":
    main()
