"""Broken Authentication Challenge - demonstrates insecure query-param auth flow."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

import config
from schemas import UserInfo
from ui.banner import render_ctf_banner

router = APIRouter()

FLAG = config.BROKEN_AUTH_FLAG
PATH = "/login/"

# Simulated database of users with passwords
users = {
    "admin": UserInfo(password="5up3rs3cret4dm1npa55"),
    "user1": UserInfo(password="Password123!"),
    "guest": UserInfo(password="guest67"),
    "alec": UserInfo(password="alecspassword_9"),
}


@router.get("/users")
async def get_users():
    """Endpoint that leaks user credentials (intentional vulnerability)."""
    return {
        username: {"password": data.password}
        for username, data in users.items()
    }


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(username: str = Query(""), password: str = Query("")):
    """Validation page that checks query params and displays the flag if valid."""
    banner_html = render_ctf_banner()
    if not username or not password or username not in users or users[username].password != password:
        return f"""
        <html>
        <head>
            <title>Login Validation</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .panel {{ border: 1px solid #ccc; padding: 20px; border-radius: 5px; }}
                .success {{ color: green; }}
            </style>
        </head>
        <body>
            <div class="container">
                {banner_html}
                <h1>Credentials Invalid</h1>
                <p><a href="{PATH}">Back to login</a></p>
            </div>
        </body>
        </html>
        """

    if username in users and users[username].password == password:
        return f"""
        <html>
        <head>
            <title>Login Validation</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .panel {{ border: 1px solid #ccc; padding: 20px; border-radius: 5px; }}
                .success {{ color: green; }}
            </style>
        </head>
        <body>
            <div class="container">
                {banner_html}
                <h1>Credentials Verified</h1>
                <div class="panel">
                    <p><strong>User:</strong> {username}</p>
                    <p class="success"><strong>Flag:</strong> {FLAG}</p>
                </div>
                <p><a href="{PATH}">Back to login</a></p>
            </div>
        </body>
        </html>
        """

    raise HTTPException(status_code=403, detail="Invalid username or password")

@router.get("/", response_class=HTMLResponse)
async def broken_auth_ui():
    banner_html = render_ctf_banner()
    html_content = f"""
    <html>
    <head>
        <title>Login</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .panel {{ border: 1px solid #ccc; padding: 20px; margin-bottom: 20px; border-radius: 5px; }}
            .input-field {{ padding: 8px; margin-bottom: 10px; width: 100%; box-sizing: border-box; }}
            .btn {{ padding: 10px 15px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }}
            .error {{ color: red; }}
            .success {{ color: green; }}
            #result {{ margin-top: 20px; padding: 10px; background-color: #f5f5f5; border-radius: 5px; display: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            {banner_html}
            <h1>Account Login</h1>
            
            <div class="panel">
                <h2>Login</h2>
                <div>
                    <input type="text" id="username" class="input-field" placeholder="Enter username">
                    <input type="password" id="password" class="input-field" placeholder="Enter password">
                    <button onclick="login()" class="btn">Login</button>
                </div>
                <div id="login-message"></div>
            </div>

            <div class="panel">
                <h2>Need Help?</h2>
                <p>If your login appears to fail, refresh and try again.</p>
            </div>
        </div>
        
        <script>
            // Store user data and current authenticated user
            let userData = {{}};
            let currentUser = null;
            
            // Fetch all users on page load
            window.onload = async function() {{
                try {{
                    const response = await fetch('{PATH}users');
                    userData = await response.json();
                    console.log("User data loaded");
                }} catch (error) {{
                    console.error("Error loading user data:", error);
                }}
            }}
            
            function login() {{
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                if (!username || !password) {{
                    document.getElementById('login-message').innerHTML = '<p class="error">Please enter both username and password</p>';
                    return;
                }}
                
                // Check password
                if (userData[username] && userData[username].password === password) {{
                    currentUser = username;
                    document.getElementById('login-message').innerHTML = 
                        `<p class="success">Login successful! Redirecting to validation page...</p>`;

                    window.location.href = `{PATH}admin?username=${{encodeURIComponent(username)}}&password=${{encodeURIComponent(password)}}`;
                }} else {{
                    document.getElementById('login-message').innerHTML = 
                        `<p class="error">Invalid username or password</p>`;
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html_content