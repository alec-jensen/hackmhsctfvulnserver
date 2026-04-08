"""Cross-Site Scripting (XSS) Challenge - demonstrates XSS vulnerabilities."""
import asyncio
from html import escape
import re
import time
from uuid import uuid4

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

import config
from ui.banner import render_ctf_banner

router = APIRouter()

FLAG = config.XSS_FLAG
PATH = "/chatroom/"
PLAYER_COOKIE = "xss_player_id"
INACTIVE_THRESHOLD_SECONDS = 5 * 60
MAX_GLOBAL_MESSAGES = 200
MAX_NAME_LENGTH = 24

# Dictionary to store per-player challenge state.
# {player_id: {"last_access": float, "solved": bool, "name": str}}
sessions: dict[str, dict[str, object]] = {}

# Global shared chat feed for all players.
# Each item: {"sender": str, "message": str, "timestamp": float}
global_messages: list[dict[str, object]] = []

cleanup_task_instance = None


def admin_get_chatroom_stats() -> dict[str, int]:
    """Return operational stats for the chatroom challenge."""
    solved_count = 0
    for data in sessions.values():
        if bool(data.get("solved", False)):
            solved_count += 1
    return {
        "active_sessions": len(sessions),
        "global_messages": len(global_messages),
        "solved_sessions": solved_count,
    }


def admin_reset_chatroom_state() -> None:
    """Reset all chatroom state across players."""
    sessions.clear()
    global_messages.clear()


def detect_xss(input_str: str) -> bool:
    """Detect common XSS patterns."""
    xss_patterns = [
        r"<script.*?>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript URIs
        r"on\w+=",  # Inline event handlers
        r"<.*?on\w+=.*?>",  # Event handlers in tags
    ]
    for pattern in xss_patterns:
        if re.search(pattern, input_str, re.IGNORECASE):
            return True
    return False


async def cleanup_task():
    """Background task to clean up inactive chat sessions."""
    while True:
        try:
            current_time = time.time()
            inactive_players: list[str] = []
            
            for player_id, data in list(sessions.items()):
                last_access = data.get("last_access", 0.0)
                if isinstance(last_access, (int, float)) and current_time - float(last_access) > INACTIVE_THRESHOLD_SECONDS:
                    inactive_players.append(player_id)
            
            for player_id in inactive_players:
                sessions.pop(player_id, None)
            
            if inactive_players:
                print(f"Cleaned up {len(inactive_players)} inactive chat sessions")
            
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in cleanup task: {e}")
            await asyncio.sleep(60)


async def start_cleanup_task() -> asyncio.Task:
    """Start the cleanup background task."""
    global cleanup_task_instance
    if cleanup_task_instance:
        cleanup_task_instance.cancel()
    cleanup_task_instance = asyncio.create_task(cleanup_task())
    return cleanup_task_instance


def ensure_player_id(request: Request, response: HTMLResponse | RedirectResponse) -> str:
    """Fetch player id from cookie or assign a new one."""
    player_id = request.cookies.get(PLAYER_COOKIE)
    if player_id:
        return player_id

    player_id = str(uuid4())
    response.set_cookie(
        key=PLAYER_COOKIE,
        value=player_id,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 8,
    )
    return player_id


def ensure_session(player_id: str) -> dict[str, object]:
    """Get or create a player session."""
    if player_id not in sessions:
        sessions[player_id] = {
            "last_access": time.time(),
            "solved": False,
            "name": f"User-{player_id[:8]}",
            "notice": "",
        }
    return sessions[player_id]


def normalize_name(raw_name: str) -> str:
    """Normalize a participant name to a safe display value."""
    trimmed = raw_name.strip()
    if not trimmed:
        return ""
    return trimmed[:MAX_NAME_LENGTH]

@router.get("/", response_class=HTMLResponse)
async def xss_practice(request: Request, msg: str = Query(""), name: str = Query("")):
    """XSS vulnerable chatroom."""
    banner_html = render_ctf_banner()
    page_response = HTMLResponse(content="")
    player_id = ensure_player_id(request, page_response)
    session = ensure_session(player_id)
    session["last_access"] = time.time()

    # Update display name if provided.
    if name:
        normalized_name = normalize_name(name)
        if normalized_name:
            session["name"] = normalized_name

        redirect_response = RedirectResponse(url=PATH, status_code=302)
        ensure_player_id(request, redirect_response)
        return redirect_response

    # Add new message to global feed unless it matches blocked XSS patterns.
    if msg:
        is_xss = config.XSS_DETECTION_ENABLED and detect_xss(msg)
        if is_xss:
            session["solved"] = True
            session["notice"] = "Message blocked by safety policy."
        else:
            sender_name = str(session.get("name", f"User-{player_id[:8]}"))
            global_messages.append(
                {
                    "sender": player_id,
                    "sender_name": sender_name,
                    "message": msg,
                    "timestamp": time.time(),
                }
            )
            if len(global_messages) > MAX_GLOBAL_MESSAGES:
                del global_messages[:-MAX_GLOBAL_MESSAGES]
            session["notice"] = ""

        redirect_response = RedirectResponse(url=PATH, status_code=302)
        ensure_player_id(request, redirect_response)
        return redirect_response

    solved = bool(session.get("solved", False))
    display_name = str(session.get("name", f"User-{player_id[:8]}"))
    notice = str(session.get("notice", ""))

    # Create form
    name_form_html = f"""
    <form action="{PATH}" method="get" style="margin-bottom: 12px;">
        <label for="name">Display name:</label>
        <input type="text" id="name" name="name" maxlength="{MAX_NAME_LENGTH}" value="{escape(display_name)}" style="width: 40%; padding: 8px;">
        <input type="submit" value="Set Name" style="padding: 8px 12px;">
    </form>
    """

    form_html = f"""
    <form action="{PATH}" method="get">
        <label for="msg">Enter your message:</label>
        <input type="text" id="msg" name="msg" style="width: 70%; padding: 8px;">
        <input type="submit" value="Send" style="padding: 8px 12px;">
    </form>
    """
    
    chat_html = "<div style='border: 1px solid #ccc; padding: 10px; margin-top: 20px; min-height: 240px;'>"
    chat_html += "<h3>Global Chat Messages</h3>"

    if global_messages:
        for idx, entry in enumerate(global_messages, start=1):
            sender = str(entry.get("sender", ""))
            sender_name = str(entry.get("sender_name", f"User-{sender[:8]}"))
            sender_label = f"You ({sender_name})" if sender == player_id else sender_name
            message = str(entry.get("message", ""))
            chat_html += f"<p><strong>{idx}. {sender_label}:</strong> {message}</p>"
    else:
        chat_html += "<p>No messages yet.</p>"

    if solved:
        chat_html += f"<p style='color: green;'><strong>Verification Token:</strong> {FLAG}</p>"
        chat_html += "<p style='color: #666;'>Security note: Real XSS payloads are intentionally not rendered in this challenge environment.</p>"
    else:
        chat_html += "<p style='color: #666;'>Account verification pending.</p>"

    chat_html += "</div>"

    response = f"""
    <html>
    <head>
        <title>Community Chat</title>
        <script>
            // Lightweight live refresh for global room updates.
            setInterval(function() {{
                const active = document.activeElement;
                if (active && (active.id === 'msg' || active.id === 'name')) {{
                    return;
                }}
                window.location.reload();
            }}, 3000);
        </script>
    </head>
    <body style="font-family: Arial, sans-serif; margin: 20px;">
        <div style="max-width: 900px; margin: 0 auto;">
            {banner_html}
            <h1>Community Chat</h1>
            <p>Global room for all connected users.</p>
            <p><strong>Session:</strong> {player_id[:8]}...</p>
            <p><strong>Name:</strong> {escape(display_name)}</p>
            <p style="color: #666;">Live updates every 3 seconds</p>
            {f'<p style="color: #8a6d3b;">{escape(notice)}</p>' if notice else ''}
            {name_form_html}
            {form_html}
            {chat_html}
            <p style="margin-top: 14px;"><a href="{PATH}reset">Reset my session</a></p>
        </div>
    </body>
    </html>
    """

    page_response = HTMLResponse(content=response)
    ensure_player_id(request, page_response)
    return page_response


@router.get("/reset")
async def reset_xss_session(request: Request):
    """Reset only the current player's solve state (global messages stay)."""
    player_id = request.cookies.get(PLAYER_COOKIE)
    if player_id:
        sessions.pop(player_id, None)
    return RedirectResponse(url=PATH, status_code=302)