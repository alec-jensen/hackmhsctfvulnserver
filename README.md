# HackMHS CTF Vulnerability Server

A intentionally vulnerable web server designed to teach web security concepts through CTF (Capture The Flag) challenges.

## Features

- **Broken Authentication**: Client-side authentication bypass
- **SQL Injection**: Direct SQL injection vulnerability
- **Cross-Site Scripting (XSS)**: Stored XSS in chatroom
- **Path Traversal**: Directory traversal attacks

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

**Description**: Learn about client-side authentication vulnerabilities.

**Tasks**:
1. Access `/login/users` to view all user credentials (endpoint shows passwords)
2. Use the leaked credentials to login on the UI
3. Access the admin area to get the flag

**Vulnerability**: Passwords are stored and transmitted in plaintext via a public endpoint.

### 2. SQL Injection (`/profile-search/`)

**Description**: Learn how to exploit SQL vulnerabilities.

**Payload Example**: 
```
' UNION SELECT id, flag, NULL FROM flags --
```

**Vulnerability**: User input is directly concatenated into SQL queries without parameterization.

### 3. XSS Challenge (`/chatroom/`)

**Description**: Learn about cross-site scripting attacks.

**Tasks**:
1. Use the `/chatroom/` endpoint to join a chat session
2. Submit a message with XSS payload (e.g., `<script>alert('xss')</script>`)
3. The server will detect the XSS and display the flag

**Detection**: The server has regex-based XSS detection that can be bypassed using obfuscation techniques.

### 4. Path Traversal (`/file-access/`)

**Description**: Learn about directory traversal vulnerabilities.

**Tasks**:
1. Start with the provided files
2. Use path traversal (`../`) to navigate outside the `web/files` directory
3. Access files from the user's home directory

**Security**: The server has basic path validation, so traversal is partially mitigated.

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
│   └── path_traversal_files/ # Files accessible via traversal
└── README.md                 # This file
```

## API Endpoints

### Root
- `GET /` - Server info and challenge list
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
