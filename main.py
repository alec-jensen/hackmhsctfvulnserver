from fastapi import FastAPI

app = FastAPI()

# Import challenge routes
from challenges.broken_auth import router as broken_auth_router
from challenges.sql_roulette import router as sql_roulette_router
from challenges.xss_practice import router as xss_practice_router
from challenges.path_traversal import router as path_traversal_router

# Include challenge routers
app.include_router(broken_auth_router, prefix="/login")
app.include_router(sql_roulette_router, prefix="/profile-search")
app.include_router(xss_practice_router, prefix="/chatroom")
app.include_router(path_traversal_router, prefix="/file-access")

@app.get("/")
async def root():
    return {"message": "Webserver for some HackMHS 7 CTF Challenges"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)