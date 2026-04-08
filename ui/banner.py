"""Reusable CTF information banner for HTML pages."""
from html import escape

import config
from admin_store import get_banner_settings

BANNER_COOKIE = "ctf_info_banner_dismissed"


def render_ctf_banner() -> str:
    """Render a dismissible banner controlled by a persistent cookie."""
    try:
        enabled, banner_message, banner_version = get_banner_settings()
    except Exception:
        # Fail open with env-config fallback if store is unavailable.
        enabled = config.ENABLE_CTF_INFO_BANNER
        banner_message = config.CTF_INFO_BANNER_TEXT
        banner_version = "v1"

    if not enabled:
        return ""

    message = escape(banner_message)

    return f"""
    <div id="ctf-info-banner" style="display:none; background:#fff3cd; border:1px solid #ffe69c; color:#664d03; padding:12px 14px; border-radius:6px; margin-bottom:14px;">
        <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
            <span>{message}</span>
            <button id="ctf-info-banner-close" type="button" style="border:none; background:#664d03; color:#fff; padding:6px 10px; border-radius:4px; cursor:pointer;">Dismiss</button>
        </div>
    </div>
    <script>
        (function () {{
            const cookieName = '{BANNER_COOKIE}';
            const banner = document.getElementById('ctf-info-banner');
            const closeBtn = document.getElementById('ctf-info-banner-close');
            if (!banner || !closeBtn) {{
                return;
            }}

            function hasDismissedCookie() {{
                return document.cookie.split(';').some(function (c) {{
                    return c.trim().startsWith(cookieName + '={banner_version}');
                }});
            }}

            if (!hasDismissedCookie()) {{
                banner.style.display = 'block';
            }}

            closeBtn.addEventListener('click', function () {{
                const maxAge = 60 * 60 * 24 * 365 * 3;
                document.cookie = cookieName + '={banner_version}; path=/; max-age=' + maxAge + '; samesite=lax';
                banner.style.display = 'none';
            }});
        }})();
    </script>
    """
