from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter()

FLAG = "flag{th1s_4uth3nt1c4t10n_5ux}"
PATH = "/login/"

# theres 2 ways to get the flag
# 1. get admin password from the javascript or web requests, login, and get the flag
# 2. see the /admin endpoint, and see that the flag is in the response

# Simulated database of users with passwords
users = {
    "admin": {
        "password": "supersecretadminpass",
        "flag": FLAG
    },
    "user1": {
        "password": "password123",
        "flag": None
    },
    "guest": {
        "password": "guest",
        "flag": None
    }
}

@router.get("/users")
async def get_users():
    return users

@router.get("/admin")
async def admin_page(username: str):
    if username in users and users[username].get("flag"):
        return {"flag": users[username]["flag"]}
    raise HTTPException(status_code=403, detail="Forbidden")

@router.get("/", response_class=HTMLResponse)
async def broken_auth_ui():
    html_content = f"""
    <html>
    <head>
        <title>Broken Authentication Challenge</title>
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
            <h1>Broken Authentication Challenge</h1>
            
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
                <h2>Access Admin Area</h2>
                <div>
                    <button onclick="accessAdmin()" class="btn" id="admin-btn" disabled>Access Admin</button>
                </div>
                <div id="admin-message"></div>
            </div>
            
            <div id="result"></div>
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
                
                // Client-side authentication - extremely insecure!
                if (userData[username] && userData[username].password === password) {{
                    currentUser = username;
                    document.getElementById('login-message').innerHTML = 
                        `<p class="success">Login successful! Welcome, ${{username}}!</p>`;
                    document.getElementById('admin-btn').disabled = false;
                }} else {{
                    document.getElementById('login-message').innerHTML = 
                        `<p class="error">Invalid username or password</p>`;
                    document.getElementById('admin-btn').disabled = true;
                }}
            }}
            
            async function accessAdmin() {{
                if (!currentUser) {{
                    document.getElementById('admin-message').innerHTML = 
                        `<p class="error">You need to login first</p>`;
                    return;
                }}
                
                try {{
                    const response = await fetch(`{PATH}admin?username=${{encodeURIComponent(currentUser)}}`);
                    const data = await response.json();
                    
                    if (response.ok) {{
                        const resultDiv = document.getElementById('result');
                        resultDiv.style.display = 'block';
                        resultDiv.innerHTML = `<h3>Success!</h3><p>Flag: ${{data.flag}}</p>`;
                        document.getElementById('admin-message').innerHTML = 
                            '<p class="success">Access granted!</p>';
                    }} else {{
                        document.getElementById('admin-message').innerHTML = 
                            `<p class="error">Error: ${{data.detail}}</p>`;
                    }}
                }} catch (error) {{
                    document.getElementById('admin-message').innerHTML = 
                        `<p class="error">Error: ${{error.message}}</p>`;
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html_content