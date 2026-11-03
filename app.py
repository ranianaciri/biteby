"""
BITEBY - Good food, right on your way.

A phone-format prototype of a route-based campus food finder for SMU students.
Core idea ("Break Math"): break length - walk to the stop - order/queue - walk to class - buffer
= time left to eat. A stop "fits your break" only if that sum works out.
Chope (the mascot) lands on the stop that fits.

PROTOTYPE NOTICE: the campus map is schematic and the outlets are sample data.
All times are estimates with a buffer, never a guarantee. Chope marks a stop; it never
holds a seat or places an order. No location or personal data is collected or stored.
"""
import html as _html
import math
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from chope_assets import CHOPE

# ---------------------------------------------------------------------------
# One-time theme file: Streamlit only reads its theme from .streamlit/config.toml at start-up.
# This keeps BiteBy cream and navy even if the phone or Mac is in dark mode.
# When hosting online, also commit this same file at .streamlit/config.toml in the repo.
# ---------------------------------------------------------------------------
_THEME = """[theme]
base = "light"
primaryColor = "#1F3A8A"
backgroundColor = "#FBF4E2"
secondaryBackgroundColor = "#F3EBD3"
textColor = "#1B2A63"
"""
_CFG = Path.cwd() / ".streamlit" / "config.toml"
if not _CFG.exists():
    try:
        _CFG.parent.mkdir(exist_ok=True)
        _CFG.write_text(_THEME)
    except OSError:
        pass

st.set_page_config(page_title="BiteBy", page_icon="🍜", layout="centered",
                   initial_sidebar_state="collapsed")

# ============================================================================
# PALETTE (from the brand slides)
# ============================================================================
NAVY, CREAM, CREAM2 = "#1F3A8A", "#F5E6C4", "#FBF4E2"
GREEN, BROWN, GOLD, SKY = "#5B7B47", "#4A433D", "#C9A227", "#8FA0CC"

# ============================================================================
# SAMPLE DATA  (schematic campus + fictional outlets: replace with real data later)
# Coordinates are in metres on an invented plan, NOT real map positions.
# ============================================================================
LOCS = {
    "School of Business": (70, 270),
    "School of Accountancy": (170, 90),
    "School of Computing & Info Systems": (290, 70),
    "School of Economics & Social Sciences": (330, 310),
    "Yong Pung How School of Law": (480, 335),
    "SMU Connexion": (410, 215),
    "Li Ka Shing Library": (530, 110),
}
SHORT = {
    "School of Business": "SOB",
    "School of Accountancy": "SOA",
    "School of Computing & Info Systems": "SCIS",
    "School of Economics & Social Sciences": "SOE/SOSS",
    "Yong Pung How School of Law": "Law",
    "SMU Connexion": "Connexion",
    "Li Ka Shing Library": "Library",
}

KIND = {  # emoji, tile colour, pin colour
    "coffee": ("☕", "#EBD7B0", "#E8C98A"),
    "meal": ("🍜", "#F4C9BB", "#F0A898"),
    "healthy": ("🥗", "#CFE3C6", "#A9CF9B"),
    "tea": ("🧋", "#F2D9C0", "#EDC29B"),
    "snack": ("🥐", "#F6E3A8", "#EFD27A"),
}

STOPS = [
    dict(id=1, name="The Daily Grind", tags="Coffee • Light Bites", kind="coffee", price=5.5, order=4, pos=(140, 248), veg=True, halal=False),
    dict(id=2, name="Grain & Greens", tags="Healthy • Bowls", kind="healthy", price=9.5, order=7, pos=(235, 205), veg=True, halal=True),
    dict(id=3, name="The Sandwich Club", tags="Sandwiches • Salads", kind="meal", price=7.0, order=5, pos=(335, 255), veg=True, halal=False),
    dict(id=4, name="Brew & Bites", tags="Bubble Tea • Snacks", kind="tea", price=6.0, order=5, pos=(300, 135), veg=True, halal=False),
    dict(id=5, name="Noodle Nook", tags="Noodles • Hot Meals", kind="meal", price=6.5, order=8, pos=(400, 125), veg=False, halal=False),
    dict(id=6, name="Kopi Corner", tags="Kopi • Kaya Toast", kind="coffee", price=4.0, order=4, pos=(180, 305), veg=True, halal=False),
    dict(id=7, name="Rice Bowl Express", tags="Rice • Hot Meals", kind="meal", price=5.5, order=6, pos=(455, 225), veg=False, halal=True),
    dict(id=8, name="Green Sprout", tags="Salads • Wraps", kind="healthy", price=8.5, order=4, pos=(360, 180), veg=True, halal=True),
    dict(id=9, name="Roti & Co", tags="Prata • Snacks", kind="snack", price=4.5, order=5, pos=(485, 150), veg=True, halal=True),
    dict(id=10, name="Sip Social", tags="Bubble Tea", kind="tea", price=5.0, order=4, pos=(265, 335), veg=True, halal=True),
    dict(id=11, name="The Bao Stop", tags="Bao • Dim Sum", kind="meal", price=5.0, order=4, pos=(495, 60), veg=False, halal=False),
    dict(id=12, name="Bake Lab", tags="Bakery • Coffee", kind="snack", price=5.0, order=3, pos=(125, 140), veg=True, halal=False),
]
BY_ID = {s["id"]: s for s in STOPS}

# ============================================================================
# CSS  (phone format, brand look)
# ============================================================================
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Montserrat:wght@400;500;600;700;800&display=swap');
:root {{ --navy:{NAVY}; --cream:{CREAM}; --cream2:{CREAM2}; --green:{GREEN}; --brown:{BROWN}; --gold:{GOLD}; --sky:{SKY}; --ink:#1B2A63; }}
.stApp {{ background: var(--cream2); font-family: 'Montserrat', sans-serif; color: var(--ink); }}
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], footer, #MainMenu {{ display:none !important; }}
[data-testid="stMainBlockContainer"], .block-container {{ max-width: 430px !important; padding: 1rem 1rem 6.5rem 1rem !important; }}
[data-testid="stWidgetLabel"] p {{ font-weight:700; color:var(--navy); font-size:.85rem; }}
div[data-testid="stElementContainer"]:has(> div[data-testid="stButton"]) {{ width:100% !important; }}
div[data-testid="stButton"] {{ width:100% !important; }}
button[data-testid^="stBaseButton"] {{ border-radius:999px !important; border:1.5px solid var(--navy) !important; background:#fff !important; color:var(--navy) !important; font-weight:700 !important; min-height:2.3rem !important; padding:.15rem .6rem !important; width:100%; }}
button[data-testid^="stBaseButton"] p {{ font-size:.85rem !important; font-weight:700 !important; color:inherit !important; }}
button[data-testid="stBaseButton-primary"] {{ background:var(--navy) !important; color:var(--cream2) !important; }}
button[data-testid^="stBaseButton"]:hover {{ background:var(--cream) !important; }}
button[data-testid="stBaseButton-primary"]:hover {{ background:#16296b !important; }}
div[data-testid="stHorizontalBlock"] {{ flex-wrap:nowrap !important; gap:.5rem !important; }}
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{ min-width:0 !important; flex:1 1 0 !important; width:auto !important; }}
.st-key-torow [data-testid="stColumn"]:nth-child(1) {{ flex:5 1 0 !important; }}
.st-key-torow [data-testid="stColumn"]:nth-child(2) {{ flex:1 1 0 !important; }}
.st-key-moderow [data-testid="stColumn"]:nth-child(1) {{ flex:2 1 0 !important; }}
.st-key-moderow [data-testid="stColumn"]:nth-child(2) {{ flex:3 1 0 !important; }}
.st-key-planner {{ background:#fff; border-radius:18px; padding:.9rem .9rem .4rem; box-shadow:0 2px 10px rgba(31,58,138,.08); }}
.st-key-nav {{ position:fixed; bottom:0; left:50%; transform:translateX(-50%); width:min(100%,430px); background:#fff; border-top:1px solid #E6DAB8; z-index:1000; padding:.3rem .5rem calc(.3rem + env(safe-area-inset-bottom)); }}
.st-key-nav [data-testid="stElementContainer"], .st-key-nav [data-testid="stRadio"], .st-key-nav [data-testid="stRadioGroup"] {{ width:100% !important; }}
.st-key-nav div[role="radiogroup"] {{ display:flex !important; flex-direction:row !important; justify-content:space-between; width:100%; gap:0 !important; }}
.st-key-nav div[role="radiogroup"] > div {{ flex:1 1 0; min-width:0; }}
.st-key-nav label[data-testid="stRadioOption"] {{ width:100%; justify-content:center; margin:0 !important; padding:.4rem 0; border-radius:12px; cursor:pointer; }}
.st-key-nav label[data-testid="stRadioOption"] > div {{ justify-content:center; width:100%; }}
.st-key-nav label[data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]) {{ display:none !important; }}
.st-key-nav label[data-testid="stRadioOption"] p {{ font-size:.74rem !important; font-weight:700 !important; color:#8A8F9C !important; text-align:center; white-space:nowrap; }}
.st-key-nav label[data-selected="true"] {{ background:var(--cream); }}
.st-key-nav label[data-selected="true"] p {{ color:var(--navy) !important; }}
.bb-head {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:.7rem; }}
.bb-logo {{ font-family:'Anton',Impact,sans-serif; font-size:2.7rem; color:var(--navy); line-height:1; letter-spacing:.5px; }}
.bb-tag {{ font-weight:700; color:var(--navy); font-size:.8rem; }}
.bb-avatar {{ width:70px; height:70px; object-fit:contain; }}
.bb-h2 {{ font-family:'Anton',Impact,sans-serif; font-size:1.9rem; color:var(--navy); margin:.9rem 0 .1rem; line-height:1.1; letter-spacing:.3px; }}
.bb-sub {{ color:#4b5a8f; font-weight:600; font-size:.85rem; margin-bottom:.5rem; }}
.bb-card {{ position:relative; display:flex; gap:.7rem; background:#fff; border-radius:16px; padding:.7rem; margin:.9rem 0 .35rem; box-shadow:0 2px 8px rgba(31,58,138,.07); }}
.bb-card.best {{ border:2px solid var(--navy); }}
.bb-thumb {{ flex:0 0 62px; height:62px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:2rem; }}
.bb-info {{ min-width:0; }}
.bb-nm {{ font-weight:800; font-size:1rem; color:#14204f; }}
.bb-tags {{ font-size:.78rem; color:#6b7390; font-weight:600; }}
.pill {{ display:inline-block; font-size:.72rem; font-weight:700; padding:.15rem .5rem; border-radius:999px; background:#EEF0F6; color:#33405f; margin:.2rem .25rem 0 0; }}
.pill.det {{ background:#DCEBD9; color:#2F5B2B; }}
.tag {{ display:inline-block; margin-top:.35rem; font-size:.72rem; font-weight:800; padding:.2rem .65rem; border-radius:999px; }}
.tag.fit {{ background:var(--navy); color:var(--cream2); }}
.tag.tak {{ background:#F3E3A6; color:#6B5710; }}
.tag.no  {{ background:#F1D4CF; color:#8a2f22; }}
.plop {{ position:absolute; right:8px; top:-34px; width:56px; transform-origin:50% 100%; animation:plop .75s cubic-bezier(.3,1.5,.5,1) both; }}
@keyframes plop {{ 0% {{ transform:translateY(-40px) scale(1,1); opacity:0; }} 55% {{ transform:translateY(0) scale(1.18,.8); opacity:1; }} 78% {{ transform:translateY(-6px) scale(.94,1.06); }} 100% {{ transform:translateY(0) scale(1,1); opacity:1; }} }}
.bb-bar {{ display:flex; height:34px; border-radius:10px; overflow:hidden; background:#ece3c9; }}
.bb-seg {{ display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800; font-size:.75rem; min-width:0; overflow:hidden; }}
.bb-legend {{ display:flex; flex-wrap:wrap; gap:.25rem .85rem; font-size:.74rem; font-weight:700; color:var(--brown); margin-top:.45rem; }}
.bb-dot {{ width:9px; height:9px; border-radius:50%; display:inline-block; margin-right:.3rem; }}
.bb-panel {{ background:#fff; border-radius:16px; padding:.9rem; margin:.6rem 0; box-shadow:0 2px 8px rgba(31,58,138,.07); }}
.bb-banner {{ display:flex; align-items:center; gap:.7rem; background:var(--cream); color:var(--navy); border:2px solid var(--navy); border-radius:16px; padding:.7rem .9rem; margin:.6rem 0; font-weight:600; }}
.bb-banner img {{ width:64px; animation:plop .75s cubic-bezier(.3,1.5,.5,1) both; }}
.bb-banner small {{ color:#4b5a8f; font-weight:600; }}
.bb-note {{ font-size:.74rem; color:#6b7390; font-weight:600; margin-top:.5rem; }}
.bb-steps {{ margin:.2rem 0 0 0; padding-left:1.1rem; font-weight:600; font-size:.88rem; line-height:1.55; }}
.bb-map {{ width:100%; height:auto; border-radius:18px; display:block; }}
.bb-empty {{ text-align:center; padding:1.2rem .5rem; color:#4b5a8f; font-weight:700; }}
.bb-empty img {{ width:110px; }}
</style>
"""


def esc(s):
    return _html.escape(str(s))


def H(s):
    """Render raw HTML. Whitespace is collapsed so Markdown never mangles it."""
    st.markdown(" ".join(s.split()), unsafe_allow_html=True)


# ============================================================================
# BREAK MATH
# ============================================================================
def walk_min(p, q):
    d = math.hypot(p[0] - q[0], p[1] - q[1])
    return 0 if d == 0 else max(1, math.ceil(d * 1.25 / 80))  # ~80 m/min, winding paths


def rush_mult(t):
    """Lunch rush: queues are ~60% longer between 11:30 and 14:00."""
    m = t.hour * 60 + t.minute
    return 1.6 if 11 * 60 + 30 <= m < 14 * 60 else 1.0


def evaluate(stop, A, B, break_min, buffer, mode, start):
    pa, pb = LOCS[A], LOCS[B]
    w1, w2, direct = walk_min(pa, stop["pos"]), walk_min(stop["pos"], pb), walk_min(pa, pb)
    mult = rush_mult(start)
    order = max(1, math.ceil(stop["order"] * mult))
    need = w1 + order + w2 + buffer
    eat = break_min - need
    min_eat = 10 if mode == "Dine in" else 0
    status = "fits" if eat >= min_eat else ("takeaway" if eat >= 0 else "no")
    return dict(stop=stop, w1=w1, w2=w2, direct=direct, order=order, need=need, eat=eat,
                detour=max(0, w1 + w2 - direct), status=status, mult=mult)


STATUS_RANK = {"fits": 0, "takeaway": 1, "no": 2}


def sort_key(e):
    return (STATUS_RANK[e["status"]], e["detour"], e["order"], e["stop"]["price"])


# ============================================================================
# HTML BUILDERS
# ============================================================================
def status_tag(e):
    if e["status"] == "fits":
        return '<span class="tag fit">Fits your break</span>'
    if e["status"] == "takeaway":
        return '<span class="tag tak">Takeaway only</span>'
    return f'<span class="tag no">Over by {-e["eat"]} min</span>'


def card_html(e, best=False):
    s = e["stop"]
    emoji, tile, _ = KIND[s["kind"]]
    plop = f'<img class="plop" src="{CHOPE["pin"]}" alt="Chope">' if best else ""
    return (
        f'<div class="bb-card{" best" if best else ""}">{plop}'
        f'<div class="bb-thumb" style="background:{tile}">{emoji}</div>'
        f'<div class="bb-info"><div class="bb-nm">{esc(s["name"])}</div>'
        f'<div class="bb-tags">{esc(s["tags"])}</div>'
        f'<div><span class="pill">🚶 {e["w1"]} min</span>'
        f'<span class="pill det">{e["detour"]} min detour</span>'
        f'<span class="pill">S${s["price"]:.2f}</span></div>'
        f'{status_tag(e)}</div></div>'
    )


def break_bar(e, break_min, buffer, mode):
    eat_label = "Eat" if mode == "Dine in" else "Spare"
    segs = [("Walk", e["w1"], NAVY), ("Order", e["order"], GOLD), ("Walk", e["w2"], SKY),
            ("Buffer", buffer, "#A79F94"), (eat_label, max(e["eat"], 0), GREEN)]
    total = max(break_min, e["need"])
    bar = "".join(
        f'<div class="bb-seg" style="width:{m / total * 100:.2f}%;background:{c}">{m if m >= 2 else ""}</div>'
        for _, m, c in segs if m > 0
    )
    legend = "".join(f'<span><i class="bb-dot" style="background:{c}"></i>{n} {m}</span>' for n, m, c in segs)
    over = ""
    if e["eat"] < 0:
        over = f'<div class="bb-note" style="color:#8a2f22">Over your break by {-e["eat"]} min.</div>'
    return f'<div class="bb-bar">{bar}</div><div class="bb-legend">{legend}</div>{over}'


def map_svg(A, B, evs, selected=None, best_id=None):
    W, Ht = 600, 380
    pa, pb = LOCS[A], LOCS[B]
    p = [f'<svg class="bb-map" viewBox="0 0 {W} {Ht}" xmlns="http://www.w3.org/2000/svg">',
         f'<rect width="{W}" height="{Ht}" rx="22" fill="#EFE6CC"/>']
    for x in range(40, W, 110):
        p.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{Ht}" stroke="#E4D9B9" stroke-width="9"/>')
    for y in range(40, Ht, 100):
        p.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#E4D9B9" stroke-width="9"/>')
    for name, (x, y) in LOCS.items():
        if name in (A, B):
            continue
        p.append(f'<rect x="{x - 9}" y="{y - 9}" width="18" height="18" rx="5" fill="#D9CFB2"/>')
        p.append(f'<text x="{x}" y="{y + 26}" font-size="13" font-weight="700" fill="#8C8266" text-anchor="middle">{esc(SHORT[name])}</text>')
    if selected:
        sp = selected["stop"]["pos"]
        p.append(f'<polyline points="{pa[0]},{pa[1]} {sp[0]},{sp[1]} {pb[0]},{pb[1]}" fill="none" stroke="{NAVY}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="2 11"/>')
    else:
        p.append(f'<line x1="{pa[0]}" y1="{pa[1]}" x2="{pb[0]}" y2="{pb[1]}" stroke="{NAVY}" stroke-width="5" stroke-linecap="round" stroke-dasharray="2 11"/>')
    shown = [selected] if selected else [e for e in evs if e["status"] != "no"][:8]
    for e in shown:
        s = e["stop"]
        emoji, _, pin = KIND[s["kind"]]
        x, y = s["pos"]
        p.append(f'<circle cx="{x}" cy="{y}" r="17" fill="{pin}" stroke="#fff" stroke-width="3"/>')
        p.append(f'<text x="{x}" y="{y + 6}" font-size="17" text-anchor="middle">{emoji}</text>')
        if best_id == s["id"] and not selected:
            p.append(f'<image href="{CHOPE["pin"]}" x="{x - 24}" y="{y - 66}" width="48" height="56"/>')
    p.append(f'<circle cx="{pa[0]}" cy="{pa[1]}" r="11" fill="{NAVY}" stroke="#fff" stroke-width="4"/>')
    p.append(f'<text x="{pa[0]}" y="{pa[1] + 32}" font-size="14" font-weight="800" fill="{NAVY}" text-anchor="middle">{esc(SHORT[A])}</text>')
    p.append(f'<circle cx="{pb[0]}" cy="{pb[1]}" r="13" fill="{GREEN}" stroke="#fff" stroke-width="4"/>')
    p.append(f'<circle cx="{pb[0]}" cy="{pb[1]}" r="4" fill="#fff"/>')
    p.append(f'<text x="{pb[0]}" y="{pb[1] + 34}" font-size="14" font-weight="800" fill="{GREEN}" text-anchor="middle">{esc(SHORT[B])}</text>')
    p.append("</svg>")
    return '<div class="bb-mapwrap">' + "".join(p) + "</div>"


def show_iframe(markup, height):
    """st.iframe on current Streamlit, components.html on older versions."""
    if hasattr(st, "iframe"):
        st.iframe(markup.strip(), height=height)
    else:
        components.html(markup, height=height)


def timer_html(minutes):
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Montserrat:wght@700;800&display=swap');
body {{ margin:0; font-family:'Montserrat',sans-serif; }}
.box {{ background:{NAVY}; color:{CREAM2}; border-radius:18px; padding:14px 16px; text-align:center; }}
.lbl {{ font-weight:800; font-size:12px; letter-spacing:2px; opacity:.85; }}
#t {{ font-family:'Anton',Impact,sans-serif; font-size:60px; line-height:1.05; letter-spacing:2px; }}
button {{ font-family:inherit; font-weight:800; font-size:14px; border:none; border-radius:999px; padding:9px 22px; margin:6px 4px 0; cursor:pointer; background:{CREAM}; color:{NAVY}; }}
</style>
<div class="box"><div class="lbl">BREAK</div><div id="t">{minutes:02d}:00</div>
<button id="go">Start my break</button><button id="rs">Reset</button></div>
<script>
let total={minutes}*60, left=total, timer=null;
const t=document.getElementById('t');
function draw(){{ const m=Math.floor(left/60), s=left%60; t.textContent=String(m).padStart(2,'0')+':'+String(s).padStart(2,'0'); }}
document.getElementById('go').onclick=()=>{{ if(timer) return; timer=setInterval(()=>{{ if(left>0){{left--;draw();}} else {{clearInterval(timer);timer=null;}} }},1000); }};
document.getElementById('rs').onclick=()=>{{ clearInterval(timer);timer=null;left=total;draw(); }};
</script>
"""


# ============================================================================
# STATE + CALLBACKS
# ============================================================================
def now_sg():
    """Current time in Singapore (hosted servers run on UTC)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Singapore"))
    except Exception:
        return datetime.now()


def round5(dt):
    return (dt.replace(second=0, microsecond=0) - timedelta(minutes=dt.minute % 5)).time()


def init_state():
    ss = st.session_state
    ss.setdefault("page", "🏠 Home")
    ss.setdefault("from_loc", "School of Business")
    ss.setdefault("to_loc", "Li Ka Shing Library")
    ss.setdefault("break_min", 28)
    ss.setdefault("buffer", 5)
    ss.setdefault("budget", 12.0)
    ss.setdefault("mode", "Dine in")
    ss.setdefault("prefs", [])
    ss.setdefault("saved", [])
    ss.setdefault("chope", [])
    ss.setdefault("stop_id", None)
    ss.setdefault("start_time", round5(now_sg()))
    # Widgets on the Home page disappear when you switch tabs; re-assigning keeps their values.
    for k in ("from_loc", "to_loc", "break_min", "buffer", "budget", "mode", "prefs", "start_time"):
        ss[k] = ss[k]


def swap_locs():
    ss = st.session_state
    ss["from_loc"], ss["to_loc"] = ss["to_loc"], ss["from_loc"]


def open_stop(sid):
    st.session_state["stop_id"] = sid
    st.session_state["page"] = "🏠 Home"


def close_stop():
    st.session_state["stop_id"] = None


def toggle_save(sid):
    saved = st.session_state["saved"]
    if sid in saved:
        saved.remove(sid)
    else:
        saved.append(sid)


def chope_it(sid):
    if sid not in st.session_state["chope"]:
        st.session_state["chope"].append(sid)


def reset_app():
    for k in list(st.session_state.keys()):
        if k != "page":
            del st.session_state[k]
    st.session_state["page"] = "👤 Profile"


def params():
    ss = st.session_state
    start = ss["start_time"]
    return (ss["from_loc"], ss["to_loc"], int(ss["break_min"]), int(ss["buffer"]),
            ss.get("mode") or "Dine in", start)


def filtered_stops():
    ss = st.session_state
    prefs = ss.get("prefs") or []
    out = []
    for s in STOPS:
        if s["price"] > ss["budget"]:
            continue
        if "Vegetarian" in prefs and not s["veg"]:
            continue
        if "Halal-friendly" in prefs and not s["halal"]:
            continue
        out.append(s)
    return out


def header():
    H(f'<div class="bb-head"><div><div class="bb-logo">BiteBy</div>'
      f'<div class="bb-tag">Good food, right on your way.</div></div>'
      f'<img class="bb-avatar" src="{CHOPE["front"]}" alt="Chope"></div>')


def stop_actions(e, key):
    """Save + view buttons under a card."""
    sid = e["stop"]["id"]
    saved = sid in st.session_state["saved"]
    c1, c2 = st.columns(2)
    c1.button("♥ Saved" if saved else "♡ Save", key=f"sv_{key}_{sid}", on_click=toggle_save, args=(sid,))
    c2.button("Chope it ›", key=f"op_{key}_{sid}", on_click=open_stop, args=(sid,), type="primary")


# ============================================================================
# PAGES
# ============================================================================
def page_home():
    ss = st.session_state
    header()
    if ss["stop_id"]:
        return page_detail(ss["stop_id"])

    locs = list(LOCS.keys())
    with st.container(key="planner"):
        st.selectbox("📍 From", locs, key="from_loc")
        with st.container(key="torow"):
            c1, c2 = st.columns(2, vertical_alignment="bottom")
            c1.selectbox("🏁 To", locs, key="to_loc")
            c2.button("⇅", key="swap", on_click=swap_locs, help="Swap from and to")
        st.slider("⏱️ How long is your break?", 10, 60, key="break_min", format="%d min")
        with st.container(key="moderow"):
            c1, c2 = st.columns(2)
            c1.time_input("🕐 Break starts", key="start_time", step=300)
            c2.segmented_control("🍴 I'm having it", ["Dine in", "Takeaway"], key="mode")
        with st.expander("Filters: budget, preferences, buffer"):
            st.slider("Max budget per meal", 3.0, 15.0, step=0.5, key="budget", format="S$%.1f")
            st.pills("Preferences", ["Vegetarian", "Halal-friendly"], selection_mode="multi", key="prefs")
            st.slider("Safety buffer (minutes)", 0, 10, key="buffer")

    A, B, brk, buf, mode, start = params()
    if A == B:
        H('<div class="bb-empty"><img src="%s"><br>Pick two different places for your route.</div>' % CHOPE["shocked"])
        return
    direct = walk_min(LOCS[A], LOCS[B])
    evs = sorted((evaluate(s, A, B, brk, buf, mode, start) for s in filtered_stops()), key=sort_key)
    fits = [e for e in evs if e["status"] == "fits"]
    tak = [e for e in evs if e["status"] == "takeaway"]
    no = [e for e in evs if e["status"] == "no"]
    best = fits[0] if fits else None

    H(map_svg(A, B, evs, best_id=best["stop"]["id"] if best else None))
    rush = ' • 🕛 Lunch rush: queues ~60% longer' if rush_mult(start) > 1 else ""
    n = len(fits)
    H(f'<div class="bb-h2">On your way</div><div class="bb-sub">{n} great option{"" if n == 1 else "s"} • {brk} min break • {direct} min walk{rush}</div>')

    if brk < direct + buf:
        H(f'<div class="bb-empty"><img src="{CHOPE["shocked"]}"><br>That break is shorter than the walk itself. Try a longer break.</div>')
        return
    if not evs:
        H(f'<div class="bb-empty"><img src="{CHOPE["sad"]}"><br>No stops match your filters. Try a higher budget.</div>')
        return
    if not fits:
        H(f'<div class="bb-empty"><img src="{CHOPE["sad"]}"><br>No stop fits this break as dine-in. Check the takeaway options below.</div>')

    for e in fits[:6]:
        H(card_html(e, best=e is best))
        stop_actions(e, "h")
    if tak:
        H('<div class="bb-sub" style="margin-top:1rem">Takeaway only: tight, but doable if you eat on the go.</div>')
        for e in tak[:4]:
            H(card_html(e))
            stop_actions(e, "t")
    if no:
        with st.expander(f"Won't fit this break ({len(no)})"):
            for e in no:
                H(card_html(e))
    H('<div class="bb-note">Times are estimates with a buffer, never a guarantee. Sample outlets on a schematic campus.</div>')


def page_detail(sid):
    ss = st.session_state
    A, B, brk, buf, mode, start = params()
    s = BY_ID[sid]
    e = evaluate(s, A, B, brk, buf, mode, start)
    emoji, tile, _ = KIND[s["kind"]]
    st.button("← Back to results", key="back", on_click=close_stop)

    H(f'<div class="bb-card" style="margin-top:.7rem"><div class="bb-thumb" style="background:{tile}">{emoji}</div>'
      f'<div class="bb-info"><div class="bb-nm" style="font-size:1.15rem">{esc(s["name"])}</div>'
      f'<div class="bb-tags">{esc(s["tags"])}</div><div><span class="pill">S${s["price"]:.2f}</span>'
      f'<span class="pill det">{e["detour"]} min detour</span></div>{status_tag(e)}</div></div>')

    if sid in ss["chope"]:
        H(f'<div class="bb-banner"><img src="{CHOPE["hips"]}" alt="Chope"><div><b>Chope!</b> {esc(s["name"])} is marked on your route.'
          f'<br><small>Chope marks a stop. It never means a held seat or order.</small></div></div>')

    H(map_svg(A, B, [e], selected=e))

    mode_note = "dine-in" if mode == "Dine in" else "takeaway"
    H(f'<div class="bb-panel"><div class="bb-nm" style="margin-bottom:.5rem">Break Math <span class="bb-tags">({brk} min break, {mode_note})</span></div>'
      + break_bar(e, brk, buf, mode) + "</div>")

    t0 = datetime.combine(date.today(), start)
    fmt = lambda d: d.strftime("%H:%M")
    leave_stop = t0 + timedelta(minutes=brk - e["w2"] - buf)
    rush_txt = " (lunch rush)" if e["mult"] > 1 else ""
    eat_line = (f"Eat for about {e['eat']} min." if mode == "Dine in" else f"Take it with you: about {max(e['eat'], 0)} min to spare.") if e["eat"] >= 0 else "This stop does not fit your break."
    steps = [
        f"Leave {esc(A)} at <b>{fmt(t0)}</b>.",
        f"Walk <b>{e['w1']} min</b> to {esc(s['name'])}.",
        f"Order and wait about <b>{e['order']} min</b>{rush_txt}.",
        eat_line,
    ]
    if e["eat"] >= 0:
        steps.append(f"Leave the stop by <b>{fmt(leave_stop)}</b>, walk <b>{e['w2']} min</b> to {esc(B)}, with {buf} min buffer.")
    H('<div class="bb-panel"><div class="bb-nm" style="margin-bottom:.3rem">Walking directions</div><ol class="bb-steps">'
      + "".join(f"<li>{x}</li>" for x in steps) + "</ol></div>")

    show_iframe(timer_html(brk), 170)

    c1, c2 = st.columns(2)
    saved = sid in ss["saved"]
    c1.button("♥ Saved" if saved else "♡ Save", key=f"dsv_{sid}", on_click=toggle_save, args=(sid,))
    if sid in ss["chope"]:
        c2.button("Chope'd ✓", key=f"dch_{sid}", disabled=True)
    else:
        c2.button("Chope this stop", key=f"dch_{sid}", on_click=chope_it, args=(sid,), type="primary")
    H('<div class="bb-note">Times are estimates with a buffer, never a guarantee.</div>')


def page_explore():
    header()
    H('<div class="bb-h2">Explore</div><div class="bb-sub">Every stop near your route, checked against your current break.</div>')
    q = st.text_input("Search", placeholder="coffee, bowls, bubble tea...", label_visibility="collapsed")
    cats = st.pills("Category", ["Coffee", "Meals", "Healthy", "Bubble tea", "Snacks"], selection_mode="multi", key="cats", label_visibility="collapsed")
    kmap = {"Coffee": "coffee", "Meals": "meal", "Healthy": "healthy", "Bubble tea": "tea", "Snacks": "snack"}
    A, B, brk, buf, mode, start = params()
    evs = sorted((evaluate(s, A, B, brk, buf, mode, start) for s in filtered_stops()), key=sort_key)
    if cats:
        evs = [e for e in evs if e["stop"]["kind"] in {kmap[c] for c in cats}]
    if q:
        evs = [e for e in evs if q.lower() in (e["stop"]["name"] + " " + e["stop"]["tags"]).lower()]
    if not evs:
        H(f'<div class="bb-empty"><img src="{CHOPE["sad"]}"><br>Nothing matches. Try another search.</div>')
    for e in evs:
        H(card_html(e))
        stop_actions(e, "x")
    H(f'<div class="bb-note">Showing {A} → {B}, {brk} min break. Change these on Home.</div>')


def page_saved():
    header()
    H('<div class="bb-h2">Saved</div><div class="bb-sub">Your go-to stops. Chope\'d stops are marked ✓.</div>')
    ss = st.session_state
    A, B, brk, buf, mode, start = params()
    ids = ss["saved"] + [i for i in ss["chope"] if i not in ss["saved"]]
    if not ids:
        H(f'<div class="bb-empty"><img src="{CHOPE["sad"]}"><br>Nothing saved yet. Tap ♡ on a stop you like.</div>')
        return
    for sid in ids:
        e = evaluate(BY_ID[sid], A, B, brk, buf, mode, start)
        H(card_html(e) + ('<div class="bb-note">✓ Chope\'d</div>' if sid in ss["chope"] else ""))
        stop_actions(e, "s")


def page_profile():
    header()
    H(f'<div class="bb-h2">Profile</div><div class="bb-panel" style="display:flex;gap:.8rem;align-items:center">'
      f'<img src="{CHOPE["wink"]}" style="width:84px"><div><div class="bb-nm">Hi, SMU student</div>'
      f'<div class="bb-tags">First-year, exchange or just hungry between classes.</div></div></div>')
    ss = st.session_state
    H(f'<div class="bb-panel"><div class="bb-nm" style="margin-bottom:.4rem">Your BiteBy so far</div>'
      f'<span class="pill">{len(ss["saved"])} saved stops</span><span class="pill">{len(ss["chope"])} Chope\'d</span>'
      f'<span class="pill">Free for students</span></div>')
    H('<div class="bb-panel"><div class="bb-nm" style="margin-bottom:.4rem">How Chope works</div>'
      '<div class="bb-tags" style="font-size:.85rem;line-height:1.5">In Singapore, a tissue packet on a table says: this spot is taken. '
      'In BiteBy, Chope says: <b>this stop fits your break.</b> Chope marks a stop. It never means a held seat or order.</div></div>')
    H('<div class="bb-panel"><div class="bb-nm" style="margin-bottom:.4rem">About this prototype</div>'
      '<div class="bb-tags" style="font-size:.82rem;line-height:1.5">The campus map is schematic and the outlets are sample data. '
      'Times are estimates with a buffer, never a guarantee. This prototype does not use your phone location and stores nothing about you.</div></div>')
    st.button("Reset the demo", key="reset", on_click=reset_app)


# ============================================================================
# APP SHELL
# ============================================================================
st.markdown(CSS, unsafe_allow_html=True)
init_state()

PAGES = ["🏠 Home", "🔍 Explore", "♡ Saved", "👤 Profile"]
page = st.session_state["page"]
if page == "🏠 Home":
    page_home()
elif page == "🔍 Explore":
    page_explore()
elif page == "♡ Saved":
    page_saved()
else:
    page_profile()

with st.container(key="nav"):
    st.radio("Navigate", PAGES, key="page", horizontal=True, label_visibility="collapsed")
