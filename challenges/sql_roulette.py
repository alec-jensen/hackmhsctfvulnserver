from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
import aiosqlite

router = APIRouter()

FLAG = "flag{1_sql-1nj3ct3d}"
PATH = "/profile-search/"

# working payload
# ' UNION SELECT id, flag, NULL FROM flags -- 

# Function to initialize an in-memory SQLite database for each user
async def initialize_db() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(":memory:")
    
    # Create tables
    await conn.execute("""
    CREATE TABLE profiles (
        id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER
    )
    """)

    await conn.execute("""
    CREATE TABLE flags (
        id INTEGER PRIMARY KEY,
        flag TEXT
    )
    """)

    # Insert sample data
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (1, 'Alice', 25)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (2, 'Bob', 30)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (3, 'Charlie', 35)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (4, 'David', 40)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (5, 'Eve', 28)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (6, 'Frank', 22)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (7, 'Grace', 29)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (8, 'Heidi', 32)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (9, 'Ivan', 27)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (10, 'Judy', 31)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (11, 'Karl', 26)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (12, 'Leo', 33)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (13, 'Mallory', 24)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (14, 'Nina', 36)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (15, 'Oscar', 38)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (16, 'Peggy', 23)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (17, 'Quentin', 34)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (18, 'Rupert', 37)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (19, 'Sybil', 39)")
    await conn.execute("INSERT INTO profiles (id, name, age) VALUES (20, 'Trent', 21)")
    await conn.execute(f"INSERT INTO flags (id, flag) VALUES (1, '{FLAG}')")

    await conn.commit()
    return conn

# Function to format results as HTML table
def format_results_as_html(results, column_names=None, search_term="", error=""):
    table_html = "<table border='1' style='width:100%; border-collapse:collapse; margin-top:20px'>"
    
    # Add header row if we have results
    if results and len(results) > 0:
        table_html += "<tr style='background-color:#f2f2f2'>"
        # Use actual column names if provided
        if column_names and len(column_names) > 0:
            for column in column_names:
                table_html += f"<th style='padding:8px;'>{column}</th>"
        else:
            # Fallback to generic column names
            for i in range(len(results[0])):
                table_html += f"<th style='padding:8px;'>Column {i+1}</th>"
        table_html += "</tr>"
        
        # Add data rows
        for row in results:
            table_html += "<tr>"
            for cell in row:
                table_html += f"<td style='padding:8px;'>{cell}</td>"
            table_html += "</tr>"
    elif error:
        table_html += f"<tr><td style='color:red; padding:8px;'>{error}</td></tr>"
    else:
        table_html += f"<tr><td style='padding:8px;'>No results found for '{search_term}'</td></tr>"
    
    table_html += "</table>"
    return table_html

# Original raw SQL query endpoint
@router.get("/raw")
async def sql_roulette_raw(query: str):
    try:
        # Initialize a new in-memory database for each request
        conn = await initialize_db()
        
        # Execute the provided SQL query (vulnerable to injection)
        async with conn.execute(query) as cursor:
            result = await cursor.fetchall()
            column_names = [description[0] for description in cursor.description] if cursor.description else []
        
        await conn.close()
        
        return {
            "columns": column_names,
            "result": result
        }
    except aiosqlite.Error as e:
        raise HTTPException(status_code=400, detail=str(e))

# New UI-based search endpoint (also vulnerable to injection)
@router.get("/", response_class=HTMLResponse)
async def sql_roulette_ui(search: str = Query(None), advanced: bool = Query(False)):
    results = []
    error_message = ""
    search_term = search or ""
    column_names = []
    
    try:
        # Initialize database
        conn = await initialize_db()
        
        if search:
            # Intentionally vulnerable SQL injection point by directly inserting user input
            query = f"SELECT * FROM profiles WHERE name LIKE '%{search}%' OR age = '{search}'"
            
            try:
                # Execute the query with the injection vulnerability
                async with conn.execute(query) as cursor:
                    results = await cursor.fetchall()
                    # Get column names from cursor description
                    column_names = [description[0] for description in cursor.description] if cursor.description else []
            except aiosqlite.Error as e:
                error_message = str(e)
        else:
            # Show all profiles by default
            async with conn.execute("SELECT * FROM profiles") as cursor:
                results = await cursor.fetchall()
                column_names = [description[0] for description in cursor.description]
        
        await conn.close()

        # Make sure query is bound for display purposes
        if search:
            query = f"SELECT * FROM profiles WHERE name LIKE '%{search}%' OR age = '{search}'"
        else:
            query = "SELECT * FROM profiles"
        
        # Build HTML UI
        html_content = f"""
        <html>
        <head>
            <title>Profile Search</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .search-box {{ padding: 10px; width: 70%; }}
                .submit-btn {{ padding: 10px 15px; background-color: #4CAF50; color: white; border: none; }}
                .toggle-link {{ margin-top: 20px; display: block; }}
                pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Profile Search</h1>
                <p>Search for profiles by name or age.</p>
                
                <form method="get" action="{PATH}">
                    <input type="text" name="search" class="search-box" value="{search_term}" placeholder="Enter name or age to search...">
                    <input type="submit" class="submit-btn" value="Search">
                </form>
                
                {f"<div style='margin-top:10px;'><strong>Executed Query:</strong> <pre>{query}</pre></div>" if advanced and search else ""}
                
                <h2>Results:</h2>
                {format_results_as_html(results, column_names, search_term, error_message)}
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        error_html = f"""
        <html>
        <body>
            <h1>Error</h1>
            <p style="color: red;">{str(e)}</p>
            <a href="{PATH}">Go back</a>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)
