"""
ReelPilot — Flask web dashboard.

Dark-mode mint/emerald panel (#00E676) served on 0.0.0.0:8080.
  * Admin  (nadim / N@dim69): accounts, 2FA modal, TikTok cookie import,
    pause/activate/delete, member approvals, runtime health.
  * Guest (open view): community analytics only — account list is hidden.
  * GET /health → {"status": "healthy"} for uptime monitors.

Served by waitress (4 threads, 64-connection cap) — no gunicorn worker
army; the whole bot stays light enough for an always-on phone.
"""

import html
import hmac
import logging
import os
import re
import secrets
import time

from flask import Flask, jsonify, redirect, render_template_string, request, session

import config
import database
import ig_handler

logger = logging.getLogger("reelpilot.dashboard")

app = Flask(__name__)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(16)

_START = time.time()

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def is_admin() -> bool:
    return session.get("role") == "admin"


def _constant_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


def login_admin() -> bool:
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if _constant_eq(username, config.ADMIN_USERNAME) and _constant_eq(
        password, config.ADMIN_PASSWORD
    ):
        session["role"] = "admin"
        return True
    return False


# ---------------------------------------------------------------------------
# Shared CSS + JS (mint/emerald dark terminal)
# ---------------------------------------------------------------------------

_CSS = """
:root{--mint:#00E676;--mint-soft:rgba(0,230,118,.14);--bg:#0A100D;--panel:#0F1714;
--panel-2:#141E1A;--line:#1E2B26;--text:#D9EAE2;--dim:#7E948B;--red:#FF5D5D;}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--bg);color:var(--text);
font-family:ui-monospace,'Cascadia Mono','SF Mono',Menlo,Consolas,monospace;
font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:var(--mint);text-decoration:none}
.wrap{max-width:1080px;margin:0 auto;padding:20px 16px 60px}
header{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px;
padding:14px 0 18px;border-bottom:1px solid var(--line)}
header img{width:34px;height:34px;flex:none}
.brand{font-size:17px;font-weight:700;letter-spacing:.04em}
.brand em{color:var(--mint);font-style:normal}
.spacer{flex:1}
.badge{font-size:11px;letter-spacing:.09em;text-transform:uppercase;padding:4px 10px;
border:1px solid var(--line);border-radius:999px;color:var(--dim);background:transparent}
.badge.on{color:var(--mint);border-color:rgba(0,230,118,.45);background:var(--mint-soft)}
.badge:hover{border-color:var(--mint);color:var(--mint)}
.tab{font-size:13px;padding:6px 14px;border-radius:999px;color:var(--dim)}
.tab:hover{color:var(--text)}
.tab.active{color:var(--mint);background:var(--mint-soft)}
h2{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim);
margin:26px 0 12px}
.cards{display:flex;flex-wrap:wrap;gap:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;
padding:16px 18px;flex:1 1 150px;min-width:150px}
.card .label{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.card .value{font-size:26px;font-weight:700;color:var(--mint);margin-top:6px}
.card .sub{font-size:12px;color:var(--dim);margin-top:4px}
.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
button,.btn{font:inherit;background:transparent;color:var(--text);
border:1px solid var(--line);border-radius:10px;padding:7px 13px;cursor:pointer;
transition:border-color .15s,color .15s,background .15s}
button:hover,.btn:hover{border-color:var(--mint);color:var(--mint)}
button.primary{background:var(--mint);color:#04110A;font-weight:700;border-color:var(--mint)}
button.primary:hover{background:#3BFFA0;color:#04110A}
button.danger{color:var(--red);border-color:rgba(255,93,93,.4)}
button.danger:hover{border-color:var(--red);background:rgba(255,93,93,.08);color:var(--red)}
button.approve{color:var(--mint);border-color:rgba(0,230,118,.45)}
button.approve:hover{background:var(--mint-soft)}
.note{font-size:12px;color:var(--dim);margin-top:8px}
table{width:100%;border-collapse:collapse;font-size:14px}
th{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);
text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
td{padding:10px;border-bottom:1px solid var(--line);vertical-align:middle}
tr:last-child td{border-bottom:none}
.chip{display:inline-block;font-size:11px;padding:3px 10px;border-radius:999px;
border:1px solid var(--line);color:var(--dim)}
.chip.ig{color:#FF6E40;border-color:rgba(255,110,64,.4)}
.chip.tt{color:#33D6FF;border-color:rgba(51,214,255,.4)}
.chip.live{color:var(--mint);border-color:rgba(0,230,118,.45);background:var(--mint-soft)}
.chip.paused{color:#F2C94C;border-color:rgba(242,201,76,.4)}
.chip.pending{color:#F2C94C;border-color:rgba(242,201,76,.4)}
input,textarea{font:inherit;color:var(--text);background:var(--panel-2);
border:1px solid var(--line);border-radius:10px;padding:9px 11px;width:100%}
input:focus,textarea:focus{outline:none;border-color:rgba(0,230,118,.5)}
"""

_JS = """
<script>
function qa(name){const r=document.getElementsByName(name)[0];return r?r.value.trim():''}
async function req(action,data){const fd=new FormData();
if(data)for(const k in data)fd.append(k,data[k]);
fd.append('action',action);
const res=await fetch(window.location.pathname,{method:'POST',body:fd});
return res.json().catch(()=>({ok:false,error:'network'}));}
function showFlash(msg){let f=document.getElementById('flash');
if(!f){f=document.createElement('div');f.id='flash';
f.style.cssText='position:fixed;top:18px;left:50%;transform:translateX(-50%);'+
'background:#0F1714;border:1px solid rgba(0,230,118,.45);color:#00E676;'+
'padding:10px 18px;border-radius:12px;font:13px ui-monospace,monospace;'+
'z-index:99;box-shadow:0 8px 30px rgba(0,0,0,.5)';document.body.appendChild(f);}
f.textContent=msg;setTimeout(()=>f.remove(),2600);}
async function toggleAccount(id){const r=await req('toggle_account',{id:id});
if(r.ok)location.reload();else showFlash(r.error||'Failed');}
async function deleteAccount(id){if(!confirm('Delete this account?'))return;
const r=await req('delete_account',{id:id});if(r.ok)location.reload();
else showFlash(r.error||'Failed');}
async function reviewUser(id,act){const r=await req('review_user',{id:id,act:act});
if(r.ok)location.reload();else showFlash(r.error||'Failed');}
async function addInstagram(ev){ev.preventDefault();
const u=qa('ig_user'),p=qa('ig_pass');if(!u||!p){showFlash('Fill username + password');return;}
const btn=document.getElementById('igBtn');btn.disabled=true;btn.textContent='Signing in…';
try{const r=await req('add_instagram',{username:u,password:p});
if(r.ok){showFlash('Instagram account added ✔');setTimeout(()=>location.reload(),700);}
else if(r.two_factor){open2FA();}
else{showFlash(r.error||'Login failed');}}
finally{btn.disabled=false;btn.textContent='Add Instagram';}}
async function addInstagram2FA(ev){ev.preventDefault();
const u=qa('ig_user'),p=qa('ig_pass'),c=qa('ig_code');
if(!c){showFlash('Enter the 6-digit code');return;}
const btn=document.getElementById('ig2faBtn');btn.disabled=true;btn.textContent='Verifying…';
try{const r=await req('add_instagram',{username:u,password:p,code:c});
if(r.ok){close2FA();showFlash('Instagram account added ✔');
setTimeout(()=>location.reload(),700);}
else{showFlash(r.error||'2FA verification failed');}}
finally{btn.disabled=false;btn.textContent='Verify & add';}}
async function addTikTok(ev){ev.preventDefault();
const u=qa('tt_user'),c=document.getElementsByName('tt_cookies')[0].value.trim();
if(!u){showFlash('Enter a username');return;}
if(!c){showFlash('Paste the Netscape cookie text');return;}
const btn=document.getElementById('ttBtn');btn.disabled=true;btn.textContent='Validating…';
try{const r=await req('add_tiktok',{username:u,cookies:c});
if(r.ok){showFlash('TikTok account added ✔');setTimeout(()=>location.reload(),700);}
else{showFlash(r.error||'Cookie validation failed');}}
finally{btn.disabled=false;btn.textContent='Add TikTok';}}
function open2FA(){document.getElementById('twofa-modal').style.display='block';
const i=document.getElementsByName('ig_code')[0];if(i)i.focus();}
function close2FA(){document.getElementById('twofa-modal').style.display='none';}
</script>
"""


# ---------------------------------------------------------------------------
# Page shell + login
# ---------------------------------------------------------------------------

def _page_shell(nav: str, content: str, admin: bool = True) -> str:
    badge = (
        '<span class="badge on">admin</span>'
        '<form method="post" action="/logout" style="margin:0">'
        '<button style="padding:4px 12px">Exit</button></form>'
        if admin
        else '<a class="badge" href="/admin">admin →</a>'
    )
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ReelPilot</title><link rel="icon" href="/logo.svg" type="image/svg+xml">
<style>{_CSS}</style></head><body>
<header><div class="wrap" style="display:flex;flex-wrap:wrap;align-items:center;
gap:10px 14px;padding:14px 0;margin-bottom:0">
<img src="/logo.svg" alt="ReelPilot"><div class="brand">Reel<em>Pilot</em></div>
<div class="spacer"></div>{badge}</div></header>
<nav class="wrap" style="display:flex;flex-wrap:wrap;gap:8px;padding-bottom:6px">{nav}</nav>
<main class="wrap">{content}</main>
{_JS}
</body></html>"""


def _login_html(error: bool = False) -> str:
    err = (
        '<div class="note" style="color:var(--red);margin-top:10px">Invalid credentials.</div>'
        if error
        else ""
    )
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ReelPilot · Admin</title><link rel="icon" href="/logo.svg" type="image/svg+xml">
<style>{_CSS}</style></head><body>
<div class="wrap" style="max-width:420px;padding-top:9vh">
<form method="post" action="/login" class="card" style="padding:26px">
<div style="display:flex;align-items:center;gap:12px;margin-bottom:18px">
<img src="/logo.svg" alt="" style="width:40px;height:40px">
<div><div class="brand" style="font-size:18px">Reel<em>Pilot</em> Admin</div>
<div class="note">restricted area</div></div></div>
<input name="username" placeholder="username" autocomplete="username"
 style="width:100%;margin-bottom:10px">
<input name="password" type="password" placeholder="password"
 autocomplete="current-password" style="width:100%;margin-bottom:14px">
<button class="primary" type="submit" style="width:100%">Sign in</button>
{err}
</form>
<div class="note" style="text-align:center"><a href="/">← Guest analytics</a></div>
</div></body></html>"""


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

def _nav_tab(active: str, href: str, label: str) -> str:
    cls = "tab active" if href == active else "tab"
    return f'<a class="{cls}" href="{href}">{label}</a>'


def _platform_chip(platform: str, active: bool) -> str:
    base = "chip ig" if platform.lower() == "instagram" else "chip tt"
    state = " live" if active else " paused"
    return f'<span class="{base}{state}">{html.escape(platform.upper())}</span>'


def _system_health() -> dict:
    uptime_h = (time.time() - _START) / 3600
    free_mb = ig_handler.disk_free_mb()
    used_pct = ig_handler.disk_used_pct()
    status = "healthy" if free_mb >= config.MIN_FREE_DISK_MB else "degraded"
    return {
        "status": status,
        "uptime_h": uptime_h,
        "malloc_arenas": os.getenv("MALLOC_ARENA_MAX", "2"),
        "unbuffered": os.getenv("PYTHONUNBUFFERED", "1"),
        "disk": {"free_mb": free_mb, "used_pct": used_pct},
    }


def render_admin_page(tab: str) -> str:
    accounts = database.all_accounts()
    pending = database.users_by_status("pending")
    approved = database.users_by_status("approved")
    rejected = database.users_by_status("rejected")
    total_uploads = database.upload_count() or database.get_stat("total_uploads")
    health = _system_health()

    nav = (
        _nav_tab(tab, "/admin", "Accounts")
        + _nav_tab(tab, "/admin/members", "Members")
        + _nav_tab(tab, "/admin/health", "Health")
    )

    rows = []
    for a in accounts:
        toggle_cls = "" if a["is_active"] else "approve"
        toggle_label = "⏸ Pause" if a["is_active"] else "▶ Activate"
        rows.append(f"""
        <tr>
          <td>{_platform_chip(a["platform"], a["is_active"] == 1)}</td>
          <td><b>{html.escape(a["username"])}</b></td>
          <td class="note">{"live" if a["is_active"] else "paused"}</td>
          <td><div class="actions" style="margin:0">
            <button class="{toggle_cls}" onclick="toggleAccount({a["id"]})">{toggle_label}</button>
            <button class="danger" onclick="deleteAccount({a["id"]})">🗑 Delete</button>
          </div></td>
        </tr>""")

    add_forms = """
    <div class="cards">
      <form class="card" style="flex:1 1 320px" onsubmit="addInstagram(event)">
        <div class="label">Instagram · instagrapi session</div>
        <input name="ig_user" placeholder="username" style="margin:10px 0 8px">
        <input name="ig_pass" type="password" placeholder="password" style="margin-bottom:10px">
        <button class="primary" id="igBtn" type="submit">Add Instagram</button>
        <div class="note">2FA account? The code modal pops up after submit.</div>
      </form>
      <form class="card" style="flex:1 1 320px" onsubmit="addTikTok(event)">
        <div class="label">TikTok · Netscape cookie text</div>
        <input name="tt_user" placeholder="username / handle" style="margin:10px 0 8px">
        <textarea name="tt_cookies" rows="5" placeholder="# Netscape HTTP Cookie File …"
          style="margin-bottom:10px;resize:vertical"></textarea>
        <button class="primary" id="ttBtn" type="submit">Add TikTok</button>
        <div class="note">Paste the exported cookies.txt (must contain sessionid).</div>
      </form>
    </div>
    <div id="twofa-modal" style="display:none;position:fixed;inset:0;z-index:100;
      background:rgba(4,8,6,.72)">
      <form onsubmit="addInstagram2FA(event)" class="card" style="position:absolute;
        top:50%;left:50%;transform:translate(-50%,-50%);width:min(92vw,360px);
        background:var(--panel);padding:22px">
        <div class="label" style="color:var(--mint)">2FA code required</div>
        <div class="note" style="margin:8px 0 14px">Enter the 6-digit code from your
authenticator app.</div>
        <input name="ig_code" placeholder="123456" inputmode="numeric" maxlength="6"
          style="margin-bottom:14px;text-align:center;letter-spacing:.3em">
        <button class="primary" id="ig2faBtn" type="submit" style="width:100%">Verify &amp; add</button>
        <button type="button" onclick="close2FA()" style="width:100%;margin-top:8px">Cancel</button>
      </form>
    </div>"""

    member_rows = []
    for u in pending:
        member_rows.append(f"""
        <tr>
          <td><b>{html.escape(u["first_name"] or "—")}</b></td>
          <td class="note">@{html.escape(u["username"] or "—")}</td>
          <td class="note">{u["user_id"]}</td>
          <td><div class="actions" style="margin:0">
            <button class="approve" onclick="reviewUser({u["user_id"]},'approve')">✔ Approve</button>
            <button class="danger" onclick="reviewUser({u["user_id"]},'reject')">✖ Reject</button>
          </div></td>
        </tr>""")

    all_member_rows = "".join(
        f"<tr><td><b>{html.escape(u['first_name'] or '—')}</b></td>"
        f"<td class='note'>@{html.escape(u['username'] or '—')}</td>"
        f"<td class='note'>{u['user_id']}</td>"
        f"<td><span class='chip'>{html.escape(u['status'])}</span></td></tr>"
        for u in database.all_users()
    )

    if tab == "/admin":
        content = f"""
        <div class="cards">
          <div class="card"><div class="label">Linked accounts</div>
            <div class="value">{len(accounts)}</div></div>
          <div class="card"><div class="label">Active</div>
            <div class="value">{sum(1 for a in accounts if a["is_active"])}</div></div>
          <div class="card"><div class="label">Pending members</div>
            <div class="value">{len(pending)}</div></div>
          <div class="card"><div class="label">Reels posted</div>
            <div class="value">{total_uploads}</div></div>
        </div>
        <h2>Add accounts</h2>
        {add_forms}
        <h2>Linked accounts</h2>
        <div class="card" style="padding:0;overflow-x:auto">
          <table><thead><tr><th>Platform</th><th>Account</th><th>State</th><th>Actions</th></tr></thead>
          <tbody>{''.join(rows) or '<tr><td colspan="4" class="note" style="padding:22px;text-align:center">No accounts yet — add your first Instagram or TikTok above.</td></tr>'}</tbody></table>
        </div>"""
    elif tab == "/admin/members":
        content = f"""
        <div class="cards">
          <div class="card"><div class="label">Pending approval</div>
            <div class="value">{len(pending)}</div></div>
          <div class="card"><div class="label">Approved members</div>
            <div class="value">{len(approved)}</div></div>
          <div class="card"><div class="label">Rejected</div>
            <div class="value">{len(rejected)}</div></div>
        </div>
        <h2>Pending Telegram members</h2>
        <div class="card" style="padding:0;overflow-x:auto">
          <table><thead><tr><th>Name</th><th>Handle</th><th>ID</th><th>Actions</th></tr></thead>
          <tbody>{''.join(member_rows) or '<tr><td colspan="4" class="note" style="padding:22px;text-align:center">No pending members. New Telegram users appear here automatically.</td></tr>'}</tbody></table>
        </div>
        <h2>All members</h2>
        <div class="card" style="padding:0;overflow-x:auto">
          <table><thead><tr><th>Name</th><th>Handle</th><th>ID</th><th>Status</th></tr></thead>
          <tbody>{all_member_rows or '<tr><td colspan="4" class="note" style="padding:22px;text-align:center">No members yet.</td></tr>'}</tbody></table>
        </div>"""
    else:  # /admin/health
        content = f"""
        <div class="cards">
          <div class="card"><div class="label">Status</div>
            <div class="value" style="font-size:20px">{health["status"].upper()}</div>
            <div class="sub">GET /health → healthy</div></div>
          <div class="card"><div class="label">Uptime</div>
            <div class="value">{health["uptime_h"]:.1f}h</div><div class="sub">since process start</div></div>
          <div class="card"><div class="label">Disk free</div>
            <div class="value">{health["disk"]["free_mb"]:.0f}MB</div>
            <div class="sub">{health["disk"]["used_pct"]:.0f}% volume used</div></div>
          <div class="card"><div class="label">Reels posted</div>
            <div class="value">{total_uploads}</div></div>
        </div>
        <h2>Runtime guards</h2>
        <div class="card">
          <table>
            <tr><td>MALLOC_ARENA_MAX</td><td><b>{health["malloc_arenas"]}</b></td></tr>
            <tr><td>PYTHONUNBUFFERED</td><td><b>{health["unbuffered"]}</b></td></tr>
            <tr><td>Headless browsers</td><td><b style="color:var(--mint)">blocked ✔</b></td></tr>
            <tr><td>yt-dlp streaming</td><td><b>16K chunks · 5MB/s cap</b></td></tr>
            <tr><td>gc.collect()</td><td><b>after each video lifecycle</b></td></tr>
            <tr><td>Temp files</td><td><b>deleted immediately post-upload</b></td></tr>
          </table>
        </div>"""
    return _page_shell(nav, content)


def render_guest_page(tab: str) -> str:
    total = database.upload_count()
    creators = database.active_creators()
    health = _system_health()
    nav = _nav_tab(tab, "/", "Analytics") + _nav_tab(tab, "/about", "About")

    if tab == "/about":
        content = """
        <h2>What is ReelPilot?</h2>
        <div class="card" style="line-height:1.7;flex-basis:100%">
          ReelPilot is a memory-frugal cross-poster that downloads a reel once
          (streamed to disk in 16K chunks) and publishes it to every active
          Instagram and TikTok account with a random 3-7s pacing delay.
          It runs as a single lean process — no headless browsers, ever.
        </div>
        <h2>Privacy</h2>
        <div class="card" style="line-height:1.7;flex-basis:100%">
          This public view intentionally hides the connected social accounts.
          Admins sign in to manage accounts and member approvals.
        </div>"""
    else:
        content = f"""
        <div class="cards">
          <div class="card"><div class="label">Reels posted</div>
            <div class="value">{total}</div>
            <div class="sub">all-time successful uploads</div></div>
          <div class="card"><div class="label">Active creators</div>
            <div class="value">{creators}</div>
            <div class="sub">accounts with at least one post</div></div>
          <div class="card"><div class="label">System health</div>
            <div class="value" style="font-size:20px">{health["status"].upper()}</div>
            <div class="sub">uptime {health["uptime_h"]:.1f}h · {health["disk"]["free_mb"]:.0f}MB disk free</div></div>
        </div>
        <h2>How it works</h2>
        <div class="card" style="line-height:1.7;flex-basis:100%">
          Send a link → download → post everywhere → cleanup. Progress bars
          stream to Telegram; temp video files are deleted the moment an
          upload lifecycle ends.
        </div>"""
    return _page_shell(nav, content, admin=False)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/logo.svg")
def logo():
    path = config.APP_ROOT / "static" / "logo.svg"
    if path.exists():
        return path.read_text(encoding="utf-8"), 200, {"Content-Type": "image/svg+xml"}
    embedded = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect width="64" height="64" rx="14" fill="#0E1512"/>'
        '<path d="M14 38 A 18 18 0 1 0 32 20" fill="none" stroke="#00E676" '
        'stroke-width="4" stroke-linecap="round"/>'
        '<path d="M27 26 L 40 32 L 27 38 Z" fill="#00E676"/></svg>'
    )
    return embedded, 200, {"Content-Type": "image/svg+xml"}


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if login_admin():
            return redirect("/admin")
        return render_template_string(_login_html(error=True))
    return render_template_string(_login_html())


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")


@app.route("/")
def guest_analytics():
    return render_template_string(render_guest_page("/"))


@app.route("/about")
def guest_about():
    return render_template_string(render_guest_page("/about"))


@app.route("/admin")
def admin():
    if not is_admin():
        return redirect("/login")
    return render_template_string(render_admin_page("/admin"))


@app.route("/admin/members")
def admin_members():
    if not is_admin():
        return redirect("/login")
    return render_template_string(render_admin_page("/admin/members"))


@app.route("/admin/health")
def admin_health():
    if not is_admin():
        return redirect("/login")
    return render_template_string(render_admin_page("/admin/health"))


@app.route("/admin", methods=["POST"])
@app.route("/admin/members", methods=["POST"])
def admin_actions():
    if not is_admin():
        return jsonify({"ok": False, "error": "unauthorized"}), 403
    action = request.form.get("action", "")

    if action == "toggle_account":
        account = database.query_one(
            "SELECT * FROM accounts WHERE id=?", (request.form.get("id"),)
        )
        if not account:
            return jsonify({"ok": False, "error": "not found"}), 404
        database.set_account_active(int(account["id"]), not account["is_active"])
        return jsonify({"ok": True})

    if action == "delete_account":
        database.delete_account(int(request.form.get("id")))
        return jsonify({"ok": True})

    if action == "review_user":
        act = request.form.get("act")
        if act not in ("approve", "reject"):
            return jsonify({"ok": False, "error": "bad action"}), 400
        database.set_user_status(
            int(request.form.get("id")), "approved" if act == "approve" else "rejected"
        )
        return jsonify({"ok": True})

    if action == "add_instagram":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        code = request.form.get("code", "").strip()
        if not username or not password:
            return jsonify({"ok": False, "error": "username and password required"})
        try:
            session_json = ig_handler.login_instagram(username, password, code)
        except Exception as exc:
            msg = str(exc) or "challenge required"
            if "two_factor" in msg.lower() or "2fa" in msg.lower() or "challenge" in msg.lower():
                return jsonify({"ok": False, "two_factor": True})
            return jsonify({"ok": False, "error": _scrub(msg)})
        database.add_account("instagram", username, session_json)
        return jsonify({"ok": True})

    if action == "add_tiktok":
        username = request.form.get("username", "").strip()
        cookies = request.form.get("cookies", "")
        if not username or not cookies:
            return jsonify({"ok": False, "error": "username and cookies required"})
        ok, hint = ig_handler.verify_tiktok_cookies(cookies)
        if not ok:
            return jsonify({"ok": False, "error": hint})
        database.add_account("tiktok", username, cookies)
        return jsonify({"ok": True})

    return jsonify({"ok": False, "error": "unknown action"}), 400


def _scrub(msg: str) -> str:
    """Strip credentials from error text before surfacing it in the panel."""
    msg = re.sub(r"(password=)[^\s,)]+", r"\1***", msg, flags=re.I)
    msg = re.sub(r"'[^']*'", "'***'", msg)
    return msg[:200]


def run_dashboard() -> None:
    """Serve the panel (waitress, 4 threads) on 0.0.0.0:8080."""
    from waitress import serve

    logger.info("dashboard on %s:%s", config.DASHBOARD_HOST, config.DASHBOARD_PORT)
    serve(
        app,
        host=config.DASHBOARD_HOST,
        port=config.DASHBOARD_PORT,
        threads=4,
        connection_limit=64,
        channel_timeout=60,
    )
