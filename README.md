# HackMHS CTF Vulnerability Server

A web server designed with simulated vulnerabilities to teach web security concepts through CTF (Capture The Flag) challenges.

## Features

- **Broken Authentication**: Client-side authentication bypass
- **SQL Injection**: Direct SQL injection vulnerability
- **Cross-Site Scripting (XSS)**: Stored XSS in chatroom
- **Path Traversal**: Directory traversal attacks
- **ID Guessing (IDOR Lite)**: Accessing other user records by changing IDs
- **Cookie Role Toggle**: Client-side cookie role tampering

## Quick Start

### Prerequisites

- Python 3.13+
- `uv` package manager (or pip)

### Installation

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### Running the Server

```bash
# Using uv
uv run python main.py

# Or if you have dependencies installed globally
python main.py
```

The server will start on `http://0.0.0.0:8080`

## Configuration

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Configurable options:

- `BROKEN_AUTH_FLAG`: Flag for authentication challenge
- `SQL_INJECTION_FLAG`: Flag for SQL injection challenge
- `XSS_FLAG`: Flag for XSS challenge
- `PATH_TRAVERSAL_FLAG`: Flag for path traversal challenge
- `ID_GUESSING_FLAG`: Flag for ID guessing (IDOR lite) challenge
- `COOKIE_ROLE_FLAG`: Flag for cookie role toggle challenge
- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8080`)
- `DEBUG`: Enable debug logging (default: `false`)
- `ADMIN_DB_PATH`: On-disk SQLite file path for admin settings storage
- `ENABLE_CORS`: Enable CORS middleware (default: `true`)
- `CORS_ORIGINS`: Comma-separated CORS allowed origins
- `ENABLE_CTF_INFO_BANNER`: Show info banner on HTML pages (default: `true`)
- `CTF_INFO_BANNER_TEXT`: Banner text shown to participants
- `ADMIN_PANEL_PASSWORD`: Password for secure admin panel login (required to enable panel)
- `ADMIN_SESSION_TTL_SECONDS`: Admin session lifetime in seconds (default: `3600`)
- `ADMIN_SECURE_COOKIE`: Set `true` to require HTTPS-only admin session cookie

## Challenges

### 1. Broken Authentication (`/login/`)

**Difficulty**: Easy

**Description**: Learn about client-side authentication vulnerabilities.

**Tasks**:
1. Access `/login/users` to view all user credentials (endpoint shows passwords)
2. Use the leaked credentials to login on the UI
3. Access the admin area to get the flag

**Vulnerability**: Passwords are stored and transmitted in plaintext via a public endpoint.

**Solution**:
1. Open `/login/users` and copy one valid username/password pair.
2. Visit `/login/` and submit those credentials in the form.
3. The page redirects to `/login/admin?username=...&password=...` and returns the flag.

### 2. SQL Injection (`/profile-search/`)

**Difficulty**: Hard

**Description**: Learn how to exploit SQL vulnerabilities.

**Payload Example**: 
```
' UNION SELECT id, flag, NULL FROM flags --
```

**Vulnerability**: User input is directly concatenated into SQL queries without parameterization.

**Solution**:
1. Open `/profile-search/`.
2. In the search box, inject a UNION payload that matches the 3-column query shape.
3. Example payload:
	```
	' UNION SELECT id, flag, NULL FROM flags --
	```
4. Submit search and read the returned row containing the flag.

### 3. XSS Challenge (`/chatroom/`)

**Difficulty**: Medium

**Description**: Learn about cross-site scripting attacks.

**Tasks**:
1. Use the `/chatroom/` endpoint to join a chat session
2. Submit a message with XSS payload (e.g., `<script>alert('xss')</script>`)
3. The server will detect the XSS and display the flag

**Detection**: The server has regex-based XSS detection that can be bypassed using obfuscation techniques.

**Solution**:
1. Open `/chatroom/`.
2. Send a message that matches the XSS detector patterns.
3. A standard payload works:
	```
	<script>alert('xss')</script>
	```
4. When detected, your session is marked solved and the page shows the verification token/flag.

### 4. Path Traversal (`/file-access/`)

**Difficulty**: Medium

**Description**: Learn about directory traversal vulnerabilities.

**Tasks**:
1. Start with the provided files
2. Use path traversal (`../`) to navigate outside the `web/files` directory
3. Access files from the user's home directory

**Security**: The server has basic path validation, so traversal is partially mitigated.

**Solution**:
1. Open `/file-access/` and inspect starter files under `web/files`.
2. Traverse upward with inputs like `../` and enumerate directories.
3. Use breadcrumbs in notes/todo/log data to pivot toward hidden dotfiles in the home area.
4. Retrieve the file that contains `{{FLAG}}`; when served, the backend replaces it with the real `PATH_TRAVERSAL_FLAG` value.
5. Read the resolved file content to obtain the flag.

### 5. ID Guessing (IDOR Lite) (`/my-profile/`)

**Difficulty**: Easy

**Description**: Learn how direct object references can expose other users' data.

**Tasks**:
1. Open the student profile viewer
2. Change the `id` query parameter to view other profiles
3. Find the staff profile note that contains the flag

**Vulnerability**: The endpoint trusts user-supplied record IDs without ownership checks.

**Solution**:
1. Open `/my-profile/` (it redirects to a default user record).
2. Modify the `user` query parameter in the URL and iterate values (`?user=1`, `?user=2`, etc.).
3. Locate the staff/organizer profile entry.
4. Read the note field on that record to get the flag.

### 6. Cookie Role Toggle (`/dashboard/`)

**Difficulty**: Easy

**Description**: Learn why role decisions must not trust plain client-side cookies.

**Tasks**:
1. Open the role dashboard
2. Inspect and edit the `ctf_role` cookie from `user` to `admin`
3. Refresh to reveal the admin token

**Vulnerability**: Authorization is based entirely on an unsigned, client-controlled cookie value.

**Solution**:
1. Open `/dashboard/` and inspect cookies in browser dev tools.
2. Find `ctf_role` and change its value from `user` to `admin`.
3. Refresh `/dashboard/`.
4. The admin-only notice appears and reveals the token/flag.

## Project Structure

```
.
├── main.py                    # Main FastAPI application
├── config.py                  # Configuration management
├── schemas.py                 # Pydantic response models
├── pyproject.toml            # Project dependencies (uv)
├── requirements.txt          # Pip requirements (auto-generated)
├── .env.example              # Example environment configuration
├── challenges/
│   ├── broken_auth.py        # Authentication challenge
│   ├── sql_roulette.py       # SQL injection challenge
│   ├── xss_practice.py       # XSS challenge
│   ├── path_traversal.py     # Path traversal challenge
│   ├── id_guessing.py        # ID guessing (IDOR lite) challenge
│   ├── cookie_role_toggle.py # Cookie role tampering challenge
│   └── path_traversal_files/ # Files accessible via traversal
└── README.md                 # This file
```

## API Endpoints

### Root
- `GET /` - Minimal service status response
- `GET /health` - Health check endpoint

### Broken Auth
- `GET /login/` - Authentication UI
- `GET /login/users` - Leak all user credentials
- `GET /login/admin?username=<user>` - Get admin flag

### SQL Injection
- `GET /profile-search/` - Search UI
- `GET /profile-search/raw?query=<sql>` - Raw SQL query endpoint

### XSS
- `GET /chatroom/` - Chatroom UI

### Path Traversal
- `GET /file-access/` - File access UI
- `GET /file-access/file?filename=<path>` - Access files

### ID Guessing (IDOR Lite)
- `GET /my-profile?user=<number>` - My profile page by direct user parameter

### Cookie Role Toggle
- `GET /dashboard/` - Account dashboard route (cookie role challenge)
- `GET /dashboard/reset` - Reset role cookie back to default

### Admin Panel
- `GET /admin-panel/login` - Admin login page
- `POST /admin-panel/login` - Admin login action
- `GET /admin-panel/` - Admin dashboard (authenticated)
- `POST /admin-panel/actions/banner` - Persist banner enabled/message settings
- `POST /admin-panel/actions/banner/reset` - Rotate banner version so dismissed banners reappear
- `POST /admin-panel/actions/reset-sql` - Reset all SQL challenge player DBs
- `POST /admin-panel/actions/reset-chatroom` - Reset chatroom sessions + global feed
- `POST /admin-panel/logout` - End admin session

Admin panel settings (including banner message and enabled state) are stored in an on-disk SQLite database at `ADMIN_DB_PATH`.

## Recent Improvements

### Configuration Management
- Centralized config with environment variables via `python-dotenv`
- Easily customize flags and server settings without code changes
- Secure `.env` file handling with `.gitignore`

### Type Safety & Validation
- Added Pydantic models for API responses (`schemas.py`)
- Automatic OpenAPI documentation generation
- Better type hints throughout

### Network & Middleware
- Added CORS middleware (configurable)
- Configurable CORS origins for frontend integration
- Health check endpoint for monitoring

### Code Quality
- Replaced deprecated FastAPI event system with lifespan context manager
- Better organized imports and module structure
- Single database initialization for SQL challenge (performance improvement)
- Improved error handling and logging

### Documentation
- Module docstrings and function docstrings throughout
- Comprehensive README with quick start guide
- Configuration example file

## Docker Support

Build and run with Docker:

```bash
docker build -t ctf-server .
docker run -p 8080:8080 ctf-server
```

Or use Docker Compose:

```bash
docker-compose up
```

## Disclaimer

⚠️ **This server is intentionally vulnerable for educational purposes only!**

This application contains numerous security vulnerabilities demonstrated for learning purposes. It should:
- **Never** be deployed to production
- **Only** be used in controlled educational environments
- **Not** be exposed to untrusted networks

## License

MIT
