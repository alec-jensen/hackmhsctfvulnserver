"""ID guessing challenge (IDOR lite) for beginner participants."""
from html import escape

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, RedirectResponse

import config
from ui.banner import render_ctf_banner

router = APIRouter()

FLAG = getattr(config, "ID_GUESSING_FLAG", "flag{1d0r_1d_gu3ss1ng_w1n}")
PATH = "/my-profile"


PROFILES = {
    1: {"name": "Ava", "club": "Robotics", "note": "Practice starts at 4:00 PM."},
    2: {"name": "Noah", "club": "Yearbook", "note": "Bring your camera tomorrow."},
    3: {"name": "Mia", "club": "Debate", "note": "Topic sheet posted in room 202."},
    4: {"name": "Liam", "club": "Math Team", "note": "Meet before school on Friday."},
    5: {"name": "CTF-Organizer", "club": "Staff", "note": f"Admin memo: {FLAG}"},
}


@router.get("/", response_class=HTMLResponse)
async def id_guessing_ui(user: int | None = Query(default=None, ge=1, le=20)):
    """Render a my-profile page that trusts a user query parameter."""
    if user is None:
        return RedirectResponse(url=f"{PATH}?user=1", status_code=302)

    banner_html = render_ctf_banner()
    profile = PROFILES.get(user)

    if profile:
        profile_html = f"""
        <div class="card">
            <p><strong>User ID:</strong> {user}</p>
            <p><strong>Name:</strong> {escape(profile['name'])}</p>
            <p><strong>Club:</strong> {escape(profile['club'])}</p>
            <p><strong>Note:</strong> {escape(profile['note'])}</p>
        </div>
        """
    else:
        profile_html = f"""
        <div class="card">
            <p>No profile found for user {user}.</p>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>My Profile</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 860px; margin: 0 auto; }}
            .card {{ border: 1px solid #ccc; border-radius: 6px; padding: 16px; margin-top: 16px; background: #fafafa; }}
            .meta {{ color: #666; margin-top: 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            {banner_html}
            <h1>My Profile</h1>
            {profile_html}
        </div>
    </body>
    </html>
    """