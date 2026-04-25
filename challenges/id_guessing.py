"""ID guessing challenge themed as a cybercriminal member portal."""
from html import escape

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, RedirectResponse

import config
from ui.banner import render_ctf_banner

router = APIRouter()

FLAG = getattr(config, "ID_GUESSING_FLAG", "flag{1d0r_1d_gu3ss1ng_w1n}")
PATH = "/my-profile"


PROFILES = {
    1: {
        "handle": "ZeroDayJack",
        "crew": "Access Brokers",
        "intel": "Supply-chain recon complete. Awaiting buyer bids.",
    },
    2: {
        "handle": "PacketViper",
        "crew": "Credential Crew",
        "intel": "Fresh combo list uploaded to dead drop node #3.",
    },
    3: {
        "handle": "GhostCipher",
        "crew": "Ransom Ops",
        "intel": "Affiliate onboarding moved to encrypted forum thread.",
    },
    4: {
        "handle": "RootMonger",
        "crew": "Initial Access",
        "intel": "Phishing kit updated with region-specific lures.",
    },
    5: {
        "handle": "NightKing",
        "crew": "Gang Leader",
        "intel": f"Leader priority memo: {FLAG}",
    },
}


@router.get("/", response_class=HTMLResponse)
async def id_guessing_ui(user: int | None = Query(default=None, ge=1, le=20)):
    """Render a member portal page that trusts a user query parameter."""
    if user is None:
        return RedirectResponse(url=f"{PATH}?user=1", status_code=302)

    banner_html = render_ctf_banner()
    profile = PROFILES.get(user)

    if profile:
        profile_html = f"""
        <div class="card">
            <p><strong>Member ID:</strong> {user}</p>
            <p><strong>Handle:</strong> {escape(profile['handle'])}</p>
            <p><strong>Crew:</strong> {escape(profile['crew'])}</p>
            <p><strong>Intel:</strong> {escape(profile['intel'])}</p>
        </div>
        """
    else:
        profile_html = f"""
        <div class="card">
            <p>No member dossier found for ID {user}.</p>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>BlackCipher Member Portal</title>
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
            <h1>BlackCipher Member Portal</h1>
            <p class="meta">Internal gang dossiers indexed by member ID.</p>
            {profile_html}
        </div>
    </body>
    </html>
    """