from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import os
import logging

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FILES_DIR = os.path.join(BASE_DIR, "path_traversal_files", "bobmcgee")
WEB_ROOT = os.path.join(FILES_DIR, "web", "files")
PATH = "/file-access/"

@router.get("/", response_class=HTMLResponse)
async def path_traversal_ui():
    html_content = f"""
    <html>
    <head>
        <title>File Access Portal</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .btn {{ padding: 10px 15px; background-color: #4CAF50; color: white; border: none; cursor: pointer; margin: 5px; }}
            .file-buttons {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        </style>
        <script>
            async function fetchFile(filename) {{
                const response = await fetch(`{PATH}file?filename=${{encodeURIComponent(filename)}}`);
                const content = await response.text();
                document.getElementById('file-content').innerHTML = `<pre>${{content}}</pre>`;
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h1>File Access Portal</h1>
            <p>Select a file to access:</p>
            <div class="file-buttons">
                <button class="btn" onclick="fetchFile('notes.txt')">Notes</button>
                <button class="btn" onclick="fetchFile('todo.txt')">Todo</button>
                <button class="btn" onclick="fetchFile('contacts.csv')">Contacts</button>
                <button class="btn" onclick="fetchFile('data.json')">Data</button>
            </div>
            <div id="file-content" style="margin-top: 20px; border: 1px solid #ccc; padding: 10px; background-color: #f9f9f9;"></div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/file")
async def access_file(filename: str = Query(...)):
    try:
        requested_path = os.path.normpath(os.path.join(WEB_ROOT, filename))

        # Log the requested file path for debugging
        logging.debug(f"Attempting to access: {requested_path}")

        # Ensure the requested path is within the allowed directory
        if not os.path.realpath(requested_path).startswith(os.path.realpath(FILES_DIR)):
            raise HTTPException(status_code=403, detail="Access denied")

        # If the requested path is a directory, list its contents
        if os.path.isdir(requested_path):
            entries = os.listdir(requested_path)
            parent_path = os.path.dirname(requested_path)
            parent_link = ""
            if parent_path.startswith(FILES_DIR):
                rel_parent = os.path.relpath(parent_path, FILES_DIR)
                parent_link = f'<a href="{PATH}file?filename={rel_parent}">..</a><br>'

            links = parent_link + "".join(
                f'<a href="{PATH}file?filename={os.path.relpath(os.path.join(requested_path, entry), FILES_DIR)}">{entry}</a><br>'
                for entry in sorted(entries)
            )
            return HTMLResponse(content=f"<pre>Directory contents:\n{links}</pre>")

        # If the requested path is a file, serve it
        if os.path.isfile(requested_path):
            return FileResponse(requested_path)

        raise HTTPException(status_code=404, detail="File not found")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error accessing file: {e}")
        raise HTTPException(status_code=400, detail=str(e))