"""Cookie role toggle challenge for beginner participants."""
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

import config
from ui.banner import render_ctf_banner

router = APIRouter()

FLAG = config.COOKIE_ROLE_FLAG
PATH = "/dashboard/"
ROLE_COOKIE = "ctf_role"


@router.get("/", response_class=HTMLResponse)
async def cookie_role_ui(request: Request):
    """Render a role-gated page that trusts a plain client-side cookie value."""
    role_cookie_present = ROLE_COOKIE in request.cookies
    role = request.cookies.get(ROLE_COOKIE, "user")
    banner_html = render_ctf_banner()

    dashboard_content_html = ""
    if role == "admin":
        dashboard_content_html = f"""
        <div class="panel notice">
            <h2>Operations Notice</h2>
            <p><strong>Internal verification token:</strong> {escape(FLAG)}</p>
        </div>
        """
    else:
        dashboard_content_html = """
        <div class="panel">
            <h2>Account Summary</h2>
            <p>Welcome back. Your account is active.</p>
            <p>No new admin notices are available.</p>
        </div>
        """

    response = HTMLResponse(content=f"""
    <html>
    <head>
        <title>Account Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 860px; margin: 0 auto; }}
            .panel {{ border: 1px solid #ccc; border-radius: 6px; padding: 16px; margin-top: 14px; background: #fafafa; }}
            .notice {{ border-color: #3465a4; background: #eef5ff; }}
            .row {{ display: grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap: 12px; margin-top: 14px; }}
            .stat {{ border: 1px solid #ddd; border-radius: 6px; padding: 12px; background: #fff; }}
            .label {{ color: #666; font-size: 13px; margin-bottom: 4px; }}
            .value {{ font-size: 18px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            {banner_html}
            <h1>Account Dashboard</h1>
            <p>Overview of your account and recent activity.</p>

            <div class="row">
                <div class="stat">
                    <div class="label">Membership</div>
                    <div class="value">Student</div>
                </div>
                <div class="stat">
                    <div class="label">Last Login</div>
                    <div class="value">Today</div>
                </div>
            </div>

            {dashboard_content_html}
        </div>
    </body>
    </html>
    """)

    if not role_cookie_present:
        response.set_cookie(
            key=ROLE_COOKIE,
            value="user",
            httponly=False,
            samesite="lax",
            secure=False,
            max_age=60 * 60 * 8,
        )

    return response


@router.get("/reset")
async def cookie_role_reset():
    """Reset role cookie back to the default user role."""
    response = RedirectResponse(url=PATH, status_code=302)
    response.set_cookie(
        key=ROLE_COOKIE,
        value="user",
        httponly=False,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 8,
    )
    return response