"""Main CTF server application."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from admin_store import initialize_admin_store
import config
from ui.banner import render_ctf_banner
from challenges.broken_auth import router as broken_auth_router
from challenges.admin_panel import router as admin_panel_router
from challenges.sql_roulette import router as sql_roulette_router
from challenges.xss_practice import router as xss_practice_router
from challenges.path_traversal import router as path_traversal_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle including background tasks."""
    initialize_admin_store()

    # Startup
    from challenges.xss_practice import start_cleanup_task
    cleanup_task = await start_cleanup_task()
    
    yield
    
    # Shutdown
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="HackMHS CTF Server",
    description="Vulnerable web server for CTF challenges",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware if enabled
if config.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include challenge routers
app.include_router(broken_auth_router, prefix="/login", tags=["broken-auth"])
app.include_router(admin_panel_router, prefix="/admin-panel", tags=["admin"])
app.include_router(sql_roulette_router, prefix="/profile-search", tags=["sql-injection"])
app.include_router(xss_practice_router, prefix="/chatroom", tags=["xss"])
app.include_router(path_traversal_router, prefix="/file-access", tags=["path-traversal"])


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root landing page with links to all challenges."""
    banner_html = render_ctf_banner()
    return """
    <html>
    <head>
        <title>HackMHS CTF Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            ul { line-height: 1.9; }
            a { color: #1a73e8; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .description { color: #555; }
        </style>
    </head>
    <body>
        <div class="container">
            """ + banner_html + """
            <h1>HackMHS CTF Challenges</h1>
            <p>Select a challenge:</p>
            <ul>
                <li><a href="/login/">Broken Authentication</a> <span class="description">- SQL-like injection in auth</span></li>
                <li><a href="/profile-search/">SQL Injection</a> <span class="description">- Direct SQL injection</span></li>
                <li><a href="/chatroom/">Cross-Site Scripting (XSS)</a> <span class="description">- Stored/reflected XSS</span></li>
                <li><a href="/file-access/">Path Traversal</a> <span class="description">- Directory traversal attack</span></li>
            </ul>
            <p><a href="/docs">Open API Docs</a> | <a href="/health">Health Check</a></p>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)