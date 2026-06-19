#!/usr/bin/env python3
"""自托管主页资源生成器：抓取真实 GitHub 数据，重渲染 stats.svg 与 activity.svg。
零第三方依赖。由 .github/workflows/profile-refresh.yml 定时调用，也可本地运行。
学术指标（无公开 API）作为常量手动维护：改这三个数字即可。"""
import os, json, urllib.request, datetime

# —— 手动维护的学术指标（来自 Google Scholar）——
PUBLICATIONS = 11
CITATIONS    = 23
HINDEX       = 4

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
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))

def main():
    user  = api(f"/users/{USER}")
    repos = api(f"/users/{USER}/repos?per_page=100&sort=pushed")
    owned = [r for r in repos if not r["fork"]]
    followers = user["followers"]
    public    = user["public_repos"]
    stars     = sum(r["stargazers_count"] for r in owned)
    since     = user["created_at"][:4]

    # 最新有动态的仓库（排除 profile 仓库本身）
    latest = next((r for r in owned if r["name"].lower() != USER.lower()), owned[0])
    os.makedirs("assets", exist_ok=True)
    write_stats(public, followers, stars, since)
    write_activity(latest)
    print("generated stats.svg & activity.svg")

def bar(value, ref):
    return max(30, min(380, round(value / ref * 380)))

def write_stats(public, followers, stars, since):
    bp, bc, br, bs = bar(PUBLICATIONS,15), bar(CITATIONS,30), bar(public,15), bar(max(stars,1),10)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 360" width="1000" height="360" fill="none">
  <defs>
    <linearGradient id="snn" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00f0ff"/><stop offset="0.5" stop-color="#a855f7"/><stop offset="1" stop-color="#ff00e5"/></linearGradient>
    <filter id="sg" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="ssg" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <pattern id="sgrid" width="34" height="34" patternUnits="userSpaceOnUse"><path d="M34 0 L0 0 0 34" fill="none" stroke="#10203a" stroke-width="1"/></pattern>
    <clipPath id="nw"><rect x="34" y="80" width="0" height="90"><animate attributeName="width" from="0" to="932" dur="1s" begin="0.3s" fill="freeze"/></rect></clipPath>
  </defs>
  <rect x="3" y="3" width="994" height="354" rx="16" fill="#07070d" stroke="url(#snn)" stroke-width="2"><animate attributeName="opacity" values="0.85;1;0.85" dur="3s" repeatCount="indefinite"/></rect>
  <rect x="3" y="3" width="994" height="354" rx="16" fill="url(#sgrid)" opacity="0.5"/>
  <text x="34" y="52" font-family="'Courier New',monospace" font-size="22" font-weight="bold" fill="#00f0ff" filter="url(#ssg)" letter-spacing="2">// RESEARCH × CODE — SYSTEM PROFILE</text>
  <text x="966" y="52" text-anchor="end" font-family="'Courier New',monospace" font-size="14" font-weight="bold" fill="#28c840">● ONLINE<animate attributeName="opacity" values="1;0.3;1" dur="1.6s" repeatCount="indefinite"/></text>
  <line x1="34" y1="68" x2="966" y2="68" stroke="#1b2b45" stroke-width="1"/>
  <g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="0.2s" fill="freeze"/>
    <text x="40" y="118" font-family="'Courier New',monospace" font-size="14" fill="#7fdfff" letter-spacing="2">PUBLICATIONS</text>
    <text x="40" y="158" font-family="'Courier New',monospace" font-size="40" font-weight="bold" fill="#00f0ff" filter="url(#sg)">{PUBLICATIONS}</text>
    <rect x="40" y="172" height="6" rx="3" fill="#16263f"/><rect x="40" y="172" height="6" rx="3" fill="url(#snn)"><animate attributeName="width" from="0" to="{bp}" dur="1.3s" begin="0.4s" fill="freeze"/></rect></g>
  <g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="0.5s" fill="freeze"/>
    <text x="40" y="218" font-family="'Courier New',monospace" font-size="14" fill="#7fdfff" letter-spacing="2">CITATIONS</text>
    <text x="40" y="258" font-family="'Courier New',monospace" font-size="40" font-weight="bold" fill="#a855f7" filter="url(#sg)">{CITATIONS}</text>
    <rect x="40" y="272" height="6" rx="3" fill="#16263f"/><rect x="40" y="272" height="6" rx="3" fill="url(#snn)"><animate attributeName="width" from="0" to="{bc}" dur="1.3s" begin="0.7s" fill="freeze"/></rect></g>
  <g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="0.8s" fill="freeze"/>
    <text x="40" y="318" font-family="'Courier New',monospace" font-size="14" fill="#7fdfff" letter-spacing="2">h-INDEX</text>
    <text x="40" y="346" font-family="'Courier New',monospace" font-size="30" font-weight="bold" fill="#ff00e5" filter="url(#sg)">{HINDEX}</text></g>
  <g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="0.35s" fill="freeze"/>
    <text x="540" y="118" font-family="'Courier New',monospace" font-size="14" fill="#7fdfff" letter-spacing="2">PUBLIC REPOS</text>
    <text x="540" y="158" font-family="'Courier New',monospace" font-size="40" font-weight="bold" fill="#00f0ff" filter="url(#sg)">{public}</text>
    <rect x="540" y="172" height="6" rx="3" fill="#16263f"/><rect x="540" y="172" height="6" rx="3" fill="url(#snn)"><animate attributeName="width" from="0" to="{br}" dur="1.3s" begin="0.55s" fill="freeze"/></rect></g>
  <g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="0.65s" fill="freeze"/>
    <text x="540" y="218" font-family="'Courier New',monospace" font-size="14" fill="#7fdfff" letter-spacing="2">TOTAL STARS</text>
    <text x="540" y="258" font-family="'Courier New',monospace" font-size="40" font-weight="bold" fill="#a855f7" filter="url(#sg)">{stars}</text>
    <rect x="540" y="272" height="6" rx="3" fill="#16263f"/><rect x="540" y="272" height="6" rx="3" fill="url(#snn)"><animate attributeName="width" from="0" to="{bs}" dur="1.3s" begin="0.85s" fill="freeze"/></rect></g>
  <g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="0.95s" fill="freeze"/>
    <text x="540" y="318" font-family="'Courier New',monospace" font-size="14" fill="#7fdfff" letter-spacing="2">FOLLOWERS · SINCE</text>
    <text x="540" y="346" font-family="'Courier New',monospace" font-size="30" font-weight="bold" fill="#ff00e5" filter="url(#sg)">{followers} · {since}</text></g>
</svg>'''
    open("assets/stats.svg", "w", encoding="utf-8").write(svg)

def write_activity(repo):
    name = esc(repo["name"])
    desc = esc((repo.get("description") or "—")[:78])
    lang = esc(repo.get("language") or "—")
    when = repo["pushed_at"][:10]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 150" width="1000" height="150" fill="none">
  <defs>
    <linearGradient id="ann" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00f0ff"/><stop offset="0.5" stop-color="#a855f7"/><stop offset="1" stop-color="#ff00e5"/></linearGradient>
    <filter id="ag" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <pattern id="agrid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0 L0 0 0 30" fill="none" stroke="#10203a" stroke-width="1"/></pattern>
  </defs>
  <rect x="3" y="3" width="994" height="144" rx="14" fill="#07070d" stroke="url(#ann)" stroke-width="2"/>
  <rect x="3" y="3" width="994" height="144" rx="14" fill="url(#agrid)" opacity="0.5"/>
  <circle cx="34" cy="38" r="6" fill="#28c840" filter="url(#ag)"><animate attributeName="opacity" values="1;0.3;1" dur="1.5s" repeatCount="indefinite"/></circle>
  <text x="52" y="43" font-family="'Courier New',monospace" font-size="16" font-weight="bold" fill="#00f0ff" letter-spacing="2">// LATEST SIGNAL · 最近动态</text>
  <text x="34" y="88" font-family="'Courier New',monospace" font-size="30" font-weight="bold" fill="url(#ann)" filter="url(#ag)">{name}</text>
  <text x="34" y="118" font-family="'Courier New',monospace" font-size="15" fill="#cfe3ff">{desc}</text>
  <text x="966" y="88" text-anchor="end" font-family="'Courier New',monospace" font-size="14" font-weight="bold" fill="#a855f7">◈ {lang}</text>
  <text x="966" y="118" text-anchor="end" font-family="'Courier New',monospace" font-size="13" fill="#ff4fd8">⟳ {when}</text>
</svg>'''
    open("assets/activity.svg", "w", encoding="utf-8").write(svg)

if __name__ == "__main__":
    main()
