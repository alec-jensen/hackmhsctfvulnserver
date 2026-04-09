"""SQL Injection Challenge - demonstrates SQL injection vulnerabilities safely."""
from html import escape
import time
from uuid import uuid4

import aiosqlite
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

import config
from schemas import SQLQueryResponse
from ui.banner import render_ctf_banner

router = APIRouter()

FLAG = config.SQL_INJECTION_FLAG
PATH = "/profile-search/"
PLAYER_COOKIE = "sql_roulette_player_id"
MAX_QUERY_LENGTH = 500
MAX_SEARCH_LENGTH = 120
MAX_ACTIVE_PLAYER_DBS = 100
PLAYER_DB_TTL_SECONDS = 20 * 60

# One isolated in-memory DB per player cookie.
_player_dbs: dict[str, aiosqlite.Connection] = {}
_player_db_last_access: dict[str, float] = {}


def admin_get_player_count() -> int:
    """Return the number of active per-player SQL challenge DBs."""
    return len(_player_dbs)


async def admin_reset_all_player_dbs() -> None:
    """Reset all SQL challenge state across players."""
    dbs = list(_player_dbs.values())
    _player_dbs.clear()
    _player_db_last_access.clear()
    for conn in dbs:
        try:
            await conn.close()
        except Exception:
            # Best-effort cleanup for admin reset operations.
            pass


async def _remove_player_db(player_id: str) -> None:
    conn = _player_dbs.pop(player_id, None)
    _player_db_last_access.pop(player_id, None)
    if conn is not None:
        try:
            await conn.close()
        except Exception:
            # Best-effort cleanup for eviction and resets.
            pass


async def _prune_expired_player_dbs(now: float) -> None:
    expired_ids = [
        player_id
        for player_id, last_access in _player_db_last_access.items()
        if now - last_access > PLAYER_DB_TTL_SECONDS
    ]
    for player_id in expired_ids:
        await _remove_player_db(player_id)


async def _ensure_player_db_capacity() -> None:
    if len(_player_dbs) < MAX_ACTIVE_PLAYER_DBS:
        return

    # Evict least-recently-used DBs until there is room for a new one.
    overflow = len(_player_dbs) - MAX_ACTIVE_PLAYER_DBS + 1
    lru_players = sorted(_player_db_last_access.items(), key=lambda item: item[1])
    for player_id, _ in lru_players[:overflow]:
        await _remove_player_db(player_id)


async def initialize_db() -> aiosqlite.Connection:
    """Initialize an in-memory SQLite database for a single player."""
    conn = await aiosqlite.connect(":memory:")

    await conn.execute(
        """
        CREATE TABLE profiles (
            id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER
        )
        """
    )

    await conn.execute(
        """
        CREATE TABLE flags (
            id INTEGER PRIMARY KEY,
            flag TEXT
        )
        """
    )

    profiles = [
        (1, "Alice", 25),
        (2, "Bob", 30),
        (3, "Charlie", 35),
        (4, "David", 40),
        (5, "Eve", 28),
        (6, "Frank", 22),
        (7, "Grace", 29),
        (8, "Heidi", 32),
        (9, "Ivan", 27),
        (10, "Judy", 31),
        (11, "Karl", 26),
        (12, "Leo", 33),
        (13, "Mallory", 24),
        (14, "Nina", 36),
        (15, "Oscar", 38),
        (16, "Peggy", 23),
        (17, "Quentin", 34),
        (18, "Rupert", 37),
        (19, "Sybil", 39),
        (20, "Trent", 21),
    ]

    for profile in profiles:
        await conn.execute("INSERT INTO profiles (id, name, age) VALUES (?, ?, ?)", profile)

    await conn.execute("INSERT INTO flags (id, flag) VALUES (1, ?)", (FLAG,))
    await conn.commit()

    return conn


async def get_player_db(player_id: str) -> aiosqlite.Connection:
    """Get or create an isolated DB for a player."""
    now = time.time()
    await _prune_expired_player_dbs(now)

    if player_id not in _player_dbs:
        await _ensure_player_db_capacity()
        _player_dbs[player_id] = await initialize_db()

    _player_db_last_access[player_id] = now
    return _player_dbs[player_id]


async def reset_player_db(player_id: str) -> None:
    """Reset a player's isolated database to challenge defaults."""
    await _remove_player_db(player_id)
    _player_dbs[player_id] = await initialize_db()
    _player_db_last_access[player_id] = time.time()


def get_or_create_player_id(request: Request, response: Response) -> str:
    """Read player cookie or create a new player identity."""
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


def validate_query_shape(query: str, select_only: bool = True) -> None:
    """Allow SQL injection learning but prevent destructive and multi-statement queries."""
    query_stripped = query.strip()
    if not query_stripped:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if len(query_stripped) > MAX_QUERY_LENGTH:
        raise HTTPException(status_code=400, detail=f"Query too long (max {MAX_QUERY_LENGTH} chars)")

    if ";" in query_stripped.rstrip(";"):
        raise HTTPException(status_code=400, detail="Multiple statements are not allowed")

    lowered = query_stripped.lower()
    blocked_keywords = [
        " drop ",
        " delete ",
        " update ",
        " insert ",
        " alter ",
        " create ",
        " attach ",
        " detach ",
        " pragma ",
        " vacuum ",
        " reindex ",
    ]
    padded = f" {lowered} "
    if any(keyword in padded for keyword in blocked_keywords):
        raise HTTPException(status_code=400, detail="Destructive SQL keywords are blocked in this challenge")

    if select_only and not lowered.startswith("select"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")


def format_results_as_html(results, column_names=None, search_term="", error="") -> str:
    """Format query results as a safe HTML table."""
    table_html = "<table border='1' style='width:100%; border-collapse:collapse; margin-top:20px'>"

    if results and len(results) > 0:
        table_html += "<tr style='background-color:#f2f2f2'>"
        if column_names and len(column_names) > 0:
            for column in column_names:
                table_html += f"<th style='padding:8px;'>{escape(str(column))}</th>"
        else:
            for i in range(len(results[0])):
                table_html += f"<th style='padding:8px;'>Column {i + 1}</th>"
        table_html += "</tr>"

        for row in results:
            table_html += "<tr>"
            for cell in row:
                table_html += f"<td style='padding:8px;'>{escape(str(cell))}</td>"
            table_html += "</tr>"
    elif error:
        table_html += f"<tr><td style='color:red; padding:8px;'>{escape(error)}</td></tr>"
    else:
        table_html += f"<tr><td style='padding:8px;'>No results found for '{escape(search_term)}'</td></tr>"

    table_html += "</table>"
    return table_html


@router.get("/raw")
async def sql_roulette_raw(request: Request, response: Response, query: str) -> SQLQueryResponse:
    """Raw SQL endpoint for advanced players with isolated DB per player."""
    player_id = get_or_create_player_id(request, response)
    validate_query_shape(query, select_only=True)

    conn = await get_player_db(player_id)

    try:
        async with conn.execute(query) as cursor:
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description] if cursor.description else []

        serial_rows = [[str(cell) for cell in row] for row in rows]
        return SQLQueryResponse(columns=columns, result=serial_rows)
    except aiosqlite.Error as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/reset")
async def sql_roulette_reset(request: Request, response: Response):
    """Reset only the requesting player's challenge database."""
    player_id = get_or_create_player_id(request, response)
    await reset_player_db(player_id)
    return RedirectResponse(url=PATH, status_code=302)


@router.get("/", response_class=HTMLResponse)
async def sql_roulette_ui(
    request: Request,
    response: Response,
    search: str | None = Query(default=None),
    advanced: bool = Query(default=False),
):
    """SQL injection vulnerable search UI with isolated state per player."""
    banner_html = render_ctf_banner()
    player_id = get_or_create_player_id(request, response)
    conn = await get_player_db(player_id)

    results = []
    results_count = 0
    error_message = ""
    error_type = ""
    search_term = search or ""
    column_names = []
    query = "SELECT * FROM profiles"

    if search is not None and len(search) > MAX_SEARCH_LENGTH:
        error_message = f"Search input too long (max {MAX_SEARCH_LENGTH} chars)"
        error_type = "InputValidationError"
    else:
        try:
            if search:
                query = f"SELECT * FROM profiles WHERE name LIKE '%{search}%' OR age = '{search}'"
                validate_query_shape(query, select_only=True)

                async with conn.execute(query) as cursor:
                    results = list(await cursor.fetchall())
                    results_count = len(results)
                    column_names = [description[0] for description in cursor.description] if cursor.description else []
            else:
                async with conn.execute("SELECT * FROM profiles") as cursor:
                    results = list(await cursor.fetchall())
                    results_count = len(results)
                    column_names = [description[0] for description in cursor.description]
        except HTTPException as http_err:
            error_message = str(http_err.detail)
            error_type = "InputValidationError"
        except aiosqlite.Error as db_err:
            error_message = str(db_err)
            error_type = "SQLiteError"

    safe_query = escape(query)
    safe_search_term = escape(search_term)
    safe_error_type = escape(error_type)

    html_content = f"""
    <html>
    <head>
        <title>People Directory</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .search-box {{ padding: 10px; width: 70%; }}
            .submit-btn {{ padding: 10px 15px; background-color: #4CAF50; color: white; border: none; }}
            .secondary-btn {{ padding: 10px 15px; background-color: #555; color: white; border: none; text-decoration: none; display: inline-block; margin-left: 8px; }}
            .meta {{ margin-top: 12px; background: #f8f8f8; padding: 10px; border-radius: 6px; }}
            pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <div class="container">
            {banner_html}
            <h1>People Directory</h1>
            <p>Search for records by name or age.</p>

            <form method="get" action="{PATH}">
                <input type="text" name="search" class="search-box" value="{safe_search_term}" placeholder="Enter name or age to search...">
                <input type="hidden" name="advanced" value="{'true' if advanced else 'false'}">
                <input type="submit" class="submit-btn" value="Search">
                <a class="secondary-btn" href="{PATH}reset">Reset Session</a>
            </form>

            {f"<div class='meta'><p><strong>Executed Query:</strong></p><pre>{safe_query}</pre><p><strong>Rows Returned:</strong> {results_count}</p><p><strong>Error Type:</strong> {safe_error_type if safe_error_type else 'None'}</p></div>" if advanced else ""}

            <h2>Results</h2>
            {format_results_as_html(results, column_names, search_term, error_message)}
        </div>
    </body>
    </html>
    """

    page_response = HTMLResponse(content=html_content)
    if PLAYER_COOKIE not in request.cookies:
        page_response.set_cookie(
            key=PLAYER_COOKIE,
            value=player_id,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=60 * 60 * 8,
        )
    return page_response
