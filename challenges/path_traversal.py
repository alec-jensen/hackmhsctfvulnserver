"""Path Traversal Challenge - demonstrates directory traversal vulnerabilities."""
import os
import logging
from urllib.parse import quote

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse

import config
from ui.banner import render_ctf_banner

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = config.PATH_TRAVERSAL_BASE
WEB_ROOT = os.path.join(BASE_DIR, "web", "files")
PATH = "/file-access/"


@router.get("/", response_class=HTMLResponse)
async def path_traversal_ui():
    """Path traversal UI with file access buttons."""
    banner_html = render_ctf_banner()
    html_content = f"""
    <html>
    <head>
        <title>File Browser</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .row {{ display: flex; gap: 8px; margin-bottom: 12px; }}
            .path-input {{ flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }}
            .btn {{ padding: 10px 15px; background-color: #4CAF50; color: white; border: none; cursor: pointer; margin: 5px; }}
            .file-buttons {{ display: flex; flex-wrap: wrap; gap: 10px; }}
            #file-content {{ margin-top: 20px; border: 1px solid #ccc; padding: 10px; background-color: #f9f9f9; min-height: 220px; }}
        </style>
        <script>
            async function fetchFile(filename) {{
                try {{
                    const response = await fetch(`{PATH}file?filename=${{encodeURIComponent(filename)}}`);
                    if (response.ok) {{
                        const content = await response.text();
                        const output = document.getElementById('file-content');
                        output.innerHTML = '';

                        if (content.includes('<a href=')) {{
                            // Directory views intentionally return HTML links for navigation.
                            output.innerHTML = content;
                        }} else {{
                            const pre = document.createElement('pre');
                            pre.textContent = content;
                            output.appendChild(pre);
                        }}

                        document.getElementById('path').value = filename;
                    }} else {{
                        const output = document.getElementById('file-content');
                        output.innerHTML = '';
                        const pre = document.createElement('pre');
                        pre.textContent = `Error: ${{response.statusText}}`;
                        output.appendChild(pre);
                    }}
                }} catch (error) {{
                    const output = document.getElementById('file-content');
                    output.innerHTML = '';
                    const pre = document.createElement('pre');
                    pre.textContent = `Error: ${{error.message}}`;
                    output.appendChild(pre);
                }}
            }}

            function browsePath() {{
                const pathValue = document.getElementById('path').value.trim();
                if (!pathValue) {{
                    return;
                }}
                fetchFile(pathValue);
            }}

            window.onload = function() {{
                fetchFile('notes.txt');
            }}
        </script>
    </head>
    <body>
        <div class="container">
            {banner_html}
            <h1>File Browser</h1>
            <p>Browse files by entering a relative path.</p>
            <div class="row">
                <input id="path" class="path-input" type="text" value="notes.txt" placeholder="e.g. notes.txt or ../Desktop/secrets.txt">
                <button class="btn" onclick="browsePath()">Open</button>
            </div>
            <div class="file-buttons">
                <button class="btn" onclick="fetchFile('notes.txt')">Notes</button>
                <button class="btn" onclick="fetchFile('todo.txt')">Todo</button>
                <button class="btn" onclick="fetchFile('contacts.csv')">Contacts</button>
                <button class="btn" onclick="fetchFile('data.json')">Data</button>
            </div>
            <div id="file-content"></div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/file")
async def access_file(filename: str = Query(...)):
    """Access files with path traversal vulnerability."""
    try:
        requested_path = os.path.normpath(os.path.join(WEB_ROOT, filename))
        real_base = os.path.realpath(BASE_DIR)
        real_requested = os.path.realpath(requested_path)
        
        logger.debug(f"Attempting to access: {requested_path}")
        
        # Security check: ensure path remains within challenge sandbox.
        if os.path.commonpath([real_base, real_requested]) != real_base:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Handle directory listing
        if os.path.isdir(requested_path):
            entries = os.listdir(requested_path)
            parent_path = os.path.dirname(requested_path)
            parent_link = ""
            if parent_path.startswith(BASE_DIR):
                rel_parent = os.path.relpath(parent_path, BASE_DIR)
                parent_link = f'<a href="{PATH}file?filename={quote(rel_parent, safe="/.")}">..</a><br>'

            links = parent_link + "".join(
                f'<a href="{PATH}file?filename={quote(os.path.relpath(os.path.join(requested_path, entry), BASE_DIR), safe="/.")}">{entry}</a><br>'
                for entry in sorted(entries)
            )
            return HTMLResponse(content=f"<div><strong>Directory contents:</strong><br>{links}</div>")
        
        # Serve file
        if os.path.isfile(requested_path):
            return FileResponse(requested_path)
        
        raise HTTPException(status_code=404, detail="File not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing file: {e}")
        raise HTTPException(status_code=400, detail=str(e))