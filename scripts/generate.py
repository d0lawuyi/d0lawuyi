#!/usr/bin/env python3
"""Generate Tetris / Mission Control themed SVG panels for a GitHub profile README.

Usage:
  python generate.py --config profile.json --out assets/          # live data (needs GH_TOKEN)
  python generate.py --config profile.json --out assets/ --demo   # fake data, for previews

Outputs: hero.svg, stats.svg, mission.svg
Live mode needs a token with read:user scope in GH_TOKEN (or GITHUB_TOKEN).
"""
import argparse, datetime as dt, html, json, os, random, urllib.request

# ---------- theme ----------
T = {
    "bg": "#0b0f1a", "panel": "#111827", "grid": "#1f2937", "dim": "#4b5563",
    "text": "#e5e7eb", "muted": "#9ca3af", "accent": "#ff8a1f",
    # classic tetromino colours, low -> high activity
    "levels": ["#1a2233", "#00c2ff", "#2f6bff", "#22d36b", "#ffd400", "#ff3d5a"],
    "pieces": ["#00f0f0", "#f0f000", "#a000f0", "#00f000", "#f00000", "#0000f0", "#f0a000"],
    "font": "'JetBrains Mono','Fira Code',Consolas,monospace",
}
TETROMINOES = {  # cell offsets
    "I": [(0, 0), (1, 0), (2, 0), (3, 0)], "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "T": [(0, 0), (1, 0), (2, 0), (1, 1)], "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
    "Z": [(0, 0), (1, 0), (1, 1), (2, 1)], "J": [(0, 0), (0, 1), (1, 1), (2, 1)],
    "L": [(2, 0), (0, 1), (1, 1), (2, 1)],
}
esc = html.escape


def frame(w, h, title, body, subtitle=""):
    """Bracketed HUD frame used by every panel."""
    c = T["accent"]
    corners = "".join(
        f'<path d="M{x} {y+dy*10}V{y}H{x+dx*10}" stroke="{c}" stroke-width="2" fill="none"/>'
        for x, y, dx, dy in [(6, 6, 1, 1), (w - 6, 6, -1, 1), (6, h - 6, 1, -1), (w - 6, h - 6, -1, -1)]
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<style>
 text{{font-family:{T["font"]};fill:{T["text"]}}}
 .muted{{fill:{T["muted"]}}} .acc{{fill:{T["accent"]}}} .dim{{fill:{T["dim"]}}}
 @keyframes drop{{0%{{transform:translateY(-260px);opacity:0}}60%{{opacity:1}}100%{{transform:translateY(0)}}}}
 @keyframes fall{{0%{{transform:translateY(-120px)}}100%{{transform:translateY({h+40}px)}}}}
 @keyframes streak{{0%{{transform:translateX(0);opacity:0}}20%{{opacity:.9}}100%{{transform:translateX(-260px);opacity:0}}}}
 @keyframes boost{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(6px,-3px)}}}}
 @keyframes blink{{50%{{opacity:0}}}} @keyframes flame{{0%,100%{{transform:scaleX(1)}}50%{{transform:scaleX(1.6)}}}}
 .drop{{animation:drop .9s cubic-bezier(.3,1.4,.6,1) both}}
 .cursor{{animation:blink 1s steps(1) infinite}}
</style>
<rect width="{w}" height="{h}" rx="6" fill="{T["bg"]}"/>
<rect x="6" y="6" width="{w-12}" height="{h-12}" fill="none" stroke="{T["grid"]}"/>
{corners}
<text x="22" y="30" font-size="13" font-weight="700" class="acc">{esc(title)}</text>
<text x="22" y="44" font-size="9" class="dim">{esc(subtitle)}</text>
{body}
</svg>'''


def block(x, y, s, color, extra=""):
    """One Tetris cell with bevel highlight."""
    return (f'<g {extra}><rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{color}"/>'
            f'<rect x="{x}" y="{y}" width="{s}" height="{max(2,s//5)}" fill="#fff" opacity=".35"/>'
            f'<rect x="{x}" y="{y+s-max(2,s//5)}" width="{s}" height="{max(2,s//5)}" fill="#000" opacity=".3"/></g>')


def falling_pieces(w, h, n=7, s=10, seed=3):
    rnd, out = random.Random(seed), []
    for i in range(n):
        name = rnd.choice(list(TETROMINOES)); col = T["pieces"][i % 7]
        x0 = rnd.randint(0, w // s - 5) * s; dur = rnd.uniform(7, 13); delay = -rnd.uniform(0, dur)
        cells = "".join(block(x0 + dx * s, dy * s, s - 1, col) for dx, dy in TETROMINOES[name])
        out.append(f'<g opacity=".18" style="animation:fall {dur:.1f}s linear {delay:.1f}s infinite">{cells}</g>')
    return "".join(out)


# ---------- panels ----------
def hero(cfg):
    w, h = 900, 230
    lines = [("acc", f"{cfg['handle']}@github:~$ whoami"), ("", cfg["name"]),
             ("muted", cfg.get("role", ""))]
    for k, v in cfg.get("sections", {}).items():
        lines.append(("acc", k.upper())); lines.append(("", " · ".join(v)))
    body = falling_pieces(w, h)
    for i, (cls, t) in enumerate(lines[:11]):
        body += f'<text x="40" y="{72+i*15}" font-size="{16 if i==1 else 11}" class="{cls}" font-weight="{700 if i<2 else 400}">{esc(t)}</text>'
    body += f'<rect x="40" y="{72+min(len(lines),11)*15-10}" width="8" height="12" fill="{T["accent"]}" class="cursor"/>'
    # mini stacked well on the right
    for r in range(6):
        for c in range(8):
            if r > 1 or (c + r) % 3:
                body += block(w - 150 + c * 13, 80 + r * 13, 12, T["pieces"][(r * 3 + c) % 7])
    return frame(w, h, "// PILOT PROFILE", body, "boot sequence ok · all systems nominal")


def stats(cfg, d):
    w, h = 900, 300
    tiles = [("TODAY", d["today"]), ("THIS WEEK", d["week"]), ("LAST 30D", d["d30"]),
             ("LAST YEAR", d["year"]), ("STREAK", f'{d["streak"]}d'), ("BEST DAY", d["best"])]
    body = ""
    for i, (lab, val) in enumerate(tiles):
        x = 22 + i * 145
        body += (f'<rect x="{x}" y="58" width="3" height="30" fill="{T["accent"]}"/>'
                 f'<text x="{x+10}" y="76" font-size="18" font-weight="700">{val}</text>'
                 f'<text x="{x+10}" y="88" font-size="8" class="muted">{lab}</text>')
    weeks = d["weeks"][-53:]
    s, gx, gy = 15, 22 + (53 - len(weeks)) * 16, 110
    body += f'<rect x="18" y="{gy-4}" width="{w-36}" height="{7*16+8}" fill="{T["panel"]}" stroke="{T["accent"]}" stroke-opacity=".5"/>'
    mx = max([c for wk in weeks for c in wk] + [1])
    for wi, wk in enumerate(weeks):
        for di, cnt in enumerate(wk):
            lvl = 0 if cnt == 0 else min(5, 1 + int(4 * cnt / mx))
            x, y = gx + wi * 16, gy + di * 16
            if lvl == 0:
                body += f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{T["levels"][0]}"/>'
            else:
                body += block(x, y, s, T["levels"][lvl], f'class="drop" style="animation-delay:{wi*0.04+di*0.02:.2f}s"')
    body += f'<text x="{w-22}" y="{gy+7*16+20}" font-size="8" class="muted" text-anchor="end">LANDSCAPE TETRIS · {sum(map(sum,weeks))} CONTRIBUTIONS · 53 WEEKS</text>'
    return frame(w, h, "// FLIGHT LOG", body, "contribution telemetry · auto-updated")


def rocket(x, y):
    """Rocket assembled from Tetris cells, with flame + speed streaks."""
    s, c = 9, T["pieces"]
    cells = [(3, 1, "#e5e7eb"), (2, 0, "#e5e7eb"), (2, 1, "#e5e7eb"), (2, 2, "#e5e7eb"),
             (1, 1, "#e5e7eb"), (0, 1, "#e5e7eb"), (4, 1, c[0]), (1, 0, c[4]), (1, 2, c[4]),
             (0, 0, c[4]), (0, 2, c[4])]
    body = "".join(block(x + dx * s, y + dy * s, s - 1, col) for dx, dy, col in cells)
    flame = (f'<g style="transform-origin:{x}px {y+13}px;animation:flame .15s infinite">'
             f'<path d="M{x} {y+7}L{x-26} {y+13}L{x} {y+20}Z" fill="{T["accent"]}"/>'
             f'<path d="M{x} {y+10}L{x-13} {y+13}L{x} {y+17}Z" fill="#ffd400"/></g>')
    streaks = "".join(
        f'<rect x="{x-30}" y="{y+dy}" width="{ln}" height="2" rx="1" fill="#00c2ff" '
        f'style="animation:streak {0.5+i*0.13:.2f}s linear {i*0.11:.2f}s infinite"/>'
        for i, (dy, ln) in enumerate([(-6, 60), (2, 90), (13, 120), (24, 80), (32, 50)]))
    return f'<g style="animation:boost .6s ease-in-out infinite">{streaks}{flame}{body}</g>'


def mission(cfg, d):
    w, h = 900, 330
    kpis = [("COMMITS", d["commits"]), ("ACTIVE REPOS", d["repos"]),
            ("ISSUES", d["issues"]), ("PULL REQUESTS", d["prs"])]
    body = ""
    for i, (lab, val) in enumerate(kpis):
        x = 22 + i * 120
        body += (f'<rect x="{x}" y="58" width="3" height="30" fill="{T["accent"]}"/>'
                 f'<text x="{x+10}" y="76" font-size="18" font-weight="700">{val}</text>'
                 f'<text x="{x+10}" y="88" font-size="8" class="muted">{lab}</text>')
    # trajectory: higher monthly activity = steeper climb
    months = d["months"][-4:]; mx = max([m["commits"] for m in months] + [1])
    tot = sum(m["commits"] for m in months) or 1
    pts, x, y = [], 40, 225
    for m in months:  # climb budget of 100px split by each month's share, plus a base lift
        x += 180; y -= 4 + 84 * m["commits"] / tot; pts.append((x, y))
    path = "M40 225 " + " ".join(f"L{px:.0f} {py:.0f}" for px, py in pts)
    body += f'<path d="{path}" stroke="{T["accent"]}" stroke-width="2" stroke-dasharray="6 6" fill="none"/>'
    for px, py in pts:
        body += f'<rect x="{px-3:.0f}" y="{py-3:.0f}" width="7" height="7" fill="{T["accent"]}"/>'
    body += rocket(pts[-1][0] + 20, pts[-1][1] - 28)
    # stars
    rnd = random.Random(7)
    body += "".join(f'<rect x="{rnd.randint(30,870)}" y="{rnd.randint(55,200)}" width="2" height="2" fill="#fff" opacity="{rnd.uniform(.2,.7):.2f}"/>' for _ in range(40))
    # monthly log cards
    for i, m in enumerate(months):
        cx, last = 22 + i * 216, i == len(months) - 1
        stroke = T["accent"] if last else T["grid"]
        body += (f'<rect x="{cx}" y="245" width="206" height="66" fill="{T["panel"]}" stroke="{stroke}"/>'
                 f'<text x="{cx+10}" y="262" font-size="10" font-weight="700" class="{"acc" if last else ""}">▸ {esc(m["label"])}</text>'
                 f'<text x="{cx+10}" y="278" font-size="9" class="muted">{m["commits"]} commits · {m["repos"]} repos</text>'
                 f'<text x="{cx+10}" y="292" font-size="9" class="muted">{m["prs"]} PRs · {m["issues"]} issues</text>')
        if m.get("top"):
            body += f'<text x="{cx+10}" y="305" font-size="8" class="dim">top: {esc(m["top"][:26])}</text>'
    return frame(w, h, "// MISSION CONTROL", body, "contribution activity · last 4 months · speed run mode")


# ---------- data ----------
def gql(query, token, variables):
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    out = json.load(urllib.request.urlopen(req))
    if "errors" in out: raise SystemExit(f"GitHub API error: {out['errors']}")
    return out["data"]["user"]["contributionsCollection"]


Q = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){
 totalCommitContributions totalIssueContributions totalPullRequestContributions
 commitContributionsByRepository(maxRepositories:20){repository{name} contributions{totalCount}}
 contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""


def summarize(weeks_days, months):
    days = [d for wk in weeks_days for d in wk]
    counts = [c for _, c in days]; today = dt.date.today()
    by = {dd: c for dd, c in days}
    streak, cur = 0, today if by.get(today.isoformat(), 0) else today - dt.timedelta(days=1)
    while by.get(cur.isoformat(), 0) > 0: streak += 1; cur -= dt.timedelta(days=1)
    return {"weeks": [[c for _, c in wk] for wk in weeks_days], "today": by.get(today.isoformat(), 0),
            "week": sum(counts[-7:]), "d30": sum(counts[-30:]), "year": sum(counts),
            "streak": streak, "best": max(counts + [0]), "months": months,
            "commits": sum(m["commits"] for m in months), "repos": len({r for m in months for r in m["repo_names"]}),
            "issues": sum(m["issues"] for m in months), "prs": sum(m["prs"] for m in months)}


def live(login, token):
    now = dt.datetime.now(dt.timezone.utc)
    year = gql(Q, token, {"login": login, "from": (now - dt.timedelta(days=364)).isoformat(), "to": now.isoformat()})
    weeks = [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in year["contributionCalendar"]["weeks"]]
    months = []
    for k in range(3, -1, -1):
        y, m = now.year, now.month - k
        while m <= 0: m += 12; y -= 1
        start = dt.datetime(y, m, 1, tzinfo=dt.timezone.utc)
        end = min(now, dt.datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=dt.timezone.utc))
        c = gql(Q, token, {"login": login, "from": start.isoformat(), "to": end.isoformat()})
        repos = sorted(c["commitContributionsByRepository"], key=lambda r: -r["contributions"]["totalCount"])
        months.append({"label": start.strftime("%B %Y").upper(), "commits": c["totalCommitContributions"],
                       "issues": c["totalIssueContributions"], "prs": c["totalPullRequestContributions"],
                       "repos": len(repos), "repo_names": [r["repository"]["name"] for r in repos],
                       "top": repos[0]["repository"]["name"] if repos else ""})
    return summarize(weeks, months)


def demo():
    rnd, today = random.Random(42), dt.date.today()
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)
    weeks = [[((start + dt.timedelta(days=w * 7 + d)).isoformat(),
               rnd.choice([0, 0, 0, 1, 2, 3, 5, 8]) if w > 20 else rnd.choice([0, 0, 0, 0, 1]))
              for d in range(7) if start + dt.timedelta(days=w * 7 + d) <= today] for w in range(53)]
    months = []
    for k in range(3, -1, -1):
        mdate = (today.replace(day=1) - dt.timedelta(days=k * 30)).replace(day=1)
        months.append({"label": mdate.strftime("%B %Y").upper(), "commits": rnd.randint(10, 60),
                       "issues": rnd.randint(0, 4), "prs": rnd.randint(0, 3), "repos": rnd.randint(1, 4),
                       "repo_names": [f"repo{k}{j}" for j in range(2)], "top": "Potfolio"})
    return summarize([w for w in weeks if w], months)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--out", default="assets")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    data = demo() if a.demo or not token else live(cfg["handle"], token)
    os.makedirs(a.out, exist_ok=True)
    for name, svg in [("hero", hero(cfg)), ("stats", stats(cfg, data)), ("mission", mission(cfg, data))]:
        open(os.path.join(a.out, f"{name}.svg"), "w").write(svg)
    print(f"wrote hero.svg, stats.svg, mission.svg to {a.out} ({'demo' if a.demo or not token else 'live'} data)")
