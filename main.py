"""Main CTF server application."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from admin_store import initialize_admin_store
import config
from challenges.broken_auth import router as broken_auth_router
from challenges.admin_panel import router as admin_panel_router
from challenges.sql_roulette import router as sql_roulette_router
from challenges.xss_practice import router as xss_practice_router
from challenges.path_traversal import router as path_traversal_router
from challenges.id_guessing import router as id_guessing_router
from challenges.cookie_role_toggle import router as cookie_role_toggle_router


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
app.include_router(id_guessing_router, prefix="/my-profile", tags=["idor-lite"])
app.include_router(cookie_role_toggle_router, prefix="/dashboard", tags=["cookie-role"])


@app.get("/")
async def root():
    """Minimal public root endpoint."""
    return {"status": "ok"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)