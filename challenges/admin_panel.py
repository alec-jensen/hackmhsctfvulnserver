"""Secure admin panel for CTF operations."""
from html import escape
import time
from hmac import compare_digest
from secrets import token_urlsafe

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

import config
from admin_store import (
    create_admin_session,
    delete_admin_session,
    get_banner_settings,
    is_admin_session_valid,
    rotate_banner_version,
    set_banner_settings,
)
from challenges.sql_roulette import admin_get_player_count, admin_reset_all_player_dbs
from challenges.xss_practice import admin_get_chatroom_stats, admin_reset_chatroom_state
from ui.banner import render_ctf_banner

router = APIRouter()

ADMIN_COOKIE = "ctf_admin_session"
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 5 * 60
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 8
LOGIN_RATE_LIMIT_LOCKOUT_SECONDS = 10 * 60

# Best-effort in-memory login throttling keyed by client IP.
_failed_login_state: dict[str, dict[str, int]] = {}


def _client_key(request: Request) -> str:
    client = request.client
    if client and client.host:
        return client.host
    return "unknown"


def _is_locked_out(client_key: str, now: int) -> bool:
    state = _failed_login_state.get(client_key)
    if not state:
        return False
    locked_until = int(state.get("locked_until", 0))
    if now < locked_until:
        return True
    if locked_until > 0:
        _failed_login_state.pop(client_key, None)
    return False


def _record_failed_login(client_key: str, now: int) -> None:
    state = _failed_login_state.get(client_key)
    if not state:
        _failed_login_state[client_key] = {
            "window_start": now,
            "attempts": 1,
            "locked_until": 0,
        }
        return

    window_start = int(state.get("window_start", now))
    if now - window_start > LOGIN_RATE_LIMIT_WINDOW_SECONDS:
        state["window_start"] = now
        state["attempts"] = 1
        state["locked_until"] = 0
        return

    attempts = int(state.get("attempts", 0)) + 1
    state["attempts"] = attempts
    if attempts >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
        state["locked_until"] = now + LOGIN_RATE_LIMIT_LOCKOUT_SECONDS


def _clear_failed_login(client_key: str) -> None:
    _failed_login_state.pop(client_key, None)


def _is_authenticated(request: Request) -> bool:
    token = request.cookies.get(ADMIN_COOKIE)
    return is_admin_session_valid(token or "")


def _auth_redirect_or_none(request: Request) -> RedirectResponse | None:
    if _is_authenticated(request):
        return None
    return RedirectResponse(url="/admin-panel/login", status_code=302)


def _render_login(error: str = "") -> str:
    banner_html = render_ctf_banner()
    error_html = f"<p style='color: #b00020;'>{error}</p>" if error else ""
    return f"""
    <html>
    <head>
        <title>Admin Sign In</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 480px; margin: 0 auto; }}
            .panel {{ border: 1px solid #ccc; border-radius: 6px; padding: 20px; }}
            .input {{ width: 100%; padding: 10px; box-sizing: border-box; margin-bottom: 10px; }}
            .btn {{ padding: 10px 14px; background-color: #1a73e8; color: #fff; border: none; cursor: pointer; }}
        </style>
        <script>
            async function signIn(event) {{
                event.preventDefault();
                const password = document.getElementById('password').value;
                const message = document.getElementById('message');

                const response = await fetch('/admin-panel/login', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ password }})
                }});

                if (response.ok) {{
                    window.location.href = '/admin-panel/';
                    return;
                }}

                const data = await response.json();
                message.textContent = data.detail || 'Sign-in failed';
            }}
        </script>
    </head>
    <body>
        <div class="container">
            {banner_html}
            <h1>Admin Sign In</h1>
            <p style="color: #b00020; font-weight: bold;">
                this is NOT a part of the challenges. you are NOT authorized to pentest/exploit/otherwise misuse this page
            </p>
            <div class="panel">
                <form onsubmit="signIn(event)">
                    <label for="password">Password</label>
                    <input class="input" id="password" type="password" autocomplete="current-password" required>
                    <button class="btn" type="submit">Sign In</button>
                </form>
                <p id="message" style="color: #b00020; margin-top: 12px;"></p>
                {error_html}
            </div>
        </div>
    </body>
    </html>
    """


def _render_dashboard(updated: bool = False) -> str:
    banner_html = render_ctf_banner()
    chat_stats = admin_get_chatroom_stats()
    sql_players = admin_get_player_count()
    banner_enabled, banner_message, banner_version = get_banner_settings()
    status_message = (
        "<p style='color: #0a7d30;'>Banner settings updated.</p>"
        if updated
        else ""
    )
    return f"""
    <html>
    <head>
        <title>CTF Admin Panel</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .grid {{ display: grid; grid-template-columns: repeat(2, minmax(260px, 1fr)); gap: 12px; }}
            .card {{ border: 1px solid #ccc; border-radius: 6px; padding: 16px; }}
            .btn {{ padding: 10px 14px; border: none; cursor: pointer; color: #fff; }}
            .danger {{ background-color: #b00020; }}
            .neutral {{ background-color: #555; }}
        </style>
    </head>
    <body>
        <div class="container">
            {banner_html}
            <h1>CTF Admin Panel</h1>
            <p>Operational dashboard for challenge state management.</p>

            <div class="grid">
                <div class="card">
                    <h3>SQL Roulette</h3>
                    <p><strong>Active Player DBs:</strong> {sql_players}</p>
                    <form method="post" action="/admin-panel/actions/reset-sql">
                        <button class="btn danger" type="submit">Reset SQL Challenge State</button>
                    </form>
                </div>

                <div class="card">
                    <h3>Chatroom</h3>
                    <p><strong>Active Sessions:</strong> {chat_stats['active_sessions']}</p>
                    <p><strong>Messages in Feed:</strong> {chat_stats['global_messages']}</p>
                    <p><strong>Solved Sessions:</strong> {chat_stats['solved_sessions']}</p>
                    <form method="post" action="/admin-panel/actions/reset-chatroom">
                        <button class="btn danger" type="submit">Reset Chatroom State</button>
                    </form>
                </div>

                <div class="card" style="grid-column: 1 / -1;">
                    <h3>Challenge Catalog (Admin Only)</h3>
                    <ul style="line-height: 1.8; margin: 0; padding-left: 18px;">
                        <li><a href="/login/">Broken Authentication</a> - Usernames and passwords accidentally send to client</li>
                        <li><a href="/profile-search/">SQL Injection</a> - Direct SQL injection</li>
                        <li><a href="/chatroom/">Cross-Site Scripting (XSS)</a> - Stored/reflected XSS</li>
                        <li><a href="/file-access/">Path Traversal</a> - Directory traversal attack</li>
                        <li><a href="/my-profile/">My Profile (IDOR Lite)</a> - IDOR attack via query parameter</li>
                        <li><a href="/dashboard/">Account Dashboard</a> - Client-side role cookie trust</li>
                    </ul>
                </div>

                <div class="card" style="grid-column: 1 / -1;">
                    <h3>Banner Configuration</h3>
                    {status_message}
                    <form method="post" action="/admin-panel/actions/banner">
                        <label style="display:block; margin-bottom: 8px;">
                            <input type="checkbox" name="enabled" value="1" {'checked' if banner_enabled else ''}>
                            Enable banner on pages
                        </label>
                        <label for="banner_message" style="display:block; margin-bottom: 6px;">Banner message</label>
                        <textarea id="banner_message" name="message" rows="3" style="width:100%; box-sizing:border-box; padding:10px;">{escape(banner_message)}</textarea>
                        <p style="margin: 8px 0 0 0; color:#666;"><strong>Banner Version:</strong> {escape(banner_version)}</p>
                        <div style="margin-top:10px;">
                            <button class="btn neutral" type="submit">Save Banner Settings</button>
                        </div>
                    </form>
                    <form method="post" action="/admin-panel/actions/banner/reset" style="margin-top: 10px;">
                        <button class="btn danger" type="submit">Reset Banner Visibility For All Users</button>
                    </form>
                </div>
            </div>

            <div style="margin-top: 16px;">
                <form method="post" action="/admin-panel/logout" style="display: inline-block;">
                    <button class="btn neutral" type="submit">Sign Out</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, error: str = Query("")):
    if _is_authenticated(request):
        return RedirectResponse(url="/admin-panel/", status_code=302)

    if not config.ADMIN_PANEL_PASSWORD:
        return HTMLResponse(_render_login("Admin panel disabled: set ADMIN_PANEL_PASSWORD in .env"), status_code=503)

    return HTMLResponse(_render_login(error))


@router.post("/login")
async def admin_login(request: Request):
    if not config.ADMIN_PANEL_PASSWORD:
        raise HTTPException(status_code=503, detail="Admin panel is not configured")

    now = int(time.time())
    client_key = _client_key(request)
    if _is_locked_out(client_key, now):
        return RedirectResponse(url="/admin-panel/login?error=Too+many+attempts.+Try+again+later.", status_code=302)

    body = await request.json()
    password = str(body.get("password", ""))

    if not compare_digest(password, config.ADMIN_PANEL_PASSWORD):
        _record_failed_login(client_key, now)
        return RedirectResponse(url="/admin-panel/login?error=Invalid+password", status_code=302)

    _clear_failed_login(client_key)
    token = token_urlsafe(32)
    create_admin_session(token, int(time.time()) + config.ADMIN_SESSION_TTL_SECONDS)

    response = RedirectResponse(url="/admin-panel/", status_code=302)
    response.set_cookie(
        key=ADMIN_COOKIE,
        value=token,
        httponly=True,
        samesite="strict",
        secure=config.ADMIN_SECURE_COOKIE,
        max_age=config.ADMIN_SESSION_TTL_SECONDS,
    )
    return response


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, updated: bool = Query(False)):
    auth_redirect = _auth_redirect_or_none(request)
    if auth_redirect:
        return auth_redirect
    return HTMLResponse(_render_dashboard(updated=updated))


@router.post("/actions/banner")
async def admin_update_banner(request: Request):
    auth_redirect = _auth_redirect_or_none(request)
    if auth_redirect:
        return auth_redirect
    form = await request.form()

    enabled = str(form.get("enabled", "")).strip() == "1"
    message = str(form.get("message", "")).strip()
    if not message:
        message = config.CTF_INFO_BANNER_TEXT

    # Keep dashboard content bounded for display.
    message = message[:500]
    set_banner_settings(enabled=enabled, message=message)
    return RedirectResponse(url="/admin-panel/?updated=true", status_code=302)


@router.post("/actions/banner/reset")
async def admin_reset_banner_visibility(request: Request):
    auth_redirect = _auth_redirect_or_none(request)
    if auth_redirect:
        return auth_redirect
    rotate_banner_version()
    return RedirectResponse(url="/admin-panel/?updated=true", status_code=302)


@router.post("/actions/reset-sql")
async def admin_reset_sql(request: Request):
    auth_redirect = _auth_redirect_or_none(request)
    if auth_redirect:
        return auth_redirect
    await admin_reset_all_player_dbs()
    return RedirectResponse(url="/admin-panel/", status_code=302)


@router.post("/actions/reset-chatroom")
async def admin_reset_chatroom(request: Request):
    auth_redirect = _auth_redirect_or_none(request)
    if auth_redirect:
        return auth_redirect
    admin_reset_chatroom_state()
    return RedirectResponse(url="/admin-panel/", status_code=302)


@router.post("/logout")
async def admin_logout(request: Request):
    token = request.cookies.get(ADMIN_COOKIE)
    if token:
        delete_admin_session(token)

    response = RedirectResponse(url="/admin-panel/login", status_code=302)
    response.delete_cookie(ADMIN_COOKIE)
    return response
