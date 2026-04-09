"""Configuration management for the CTF server."""
import os
from dotenv import load_dotenv

load_dotenv()

# Flags
BROKEN_AUTH_FLAG = os.getenv("BROKEN_AUTH_FLAG", "flag{th1s_4uth3nt1c4t10n_5ux}")
SQL_INJECTION_FLAG = os.getenv("SQL_INJECTION_FLAG", "flag{1_sql-1nj3ct3d}")
XSS_FLAG = os.getenv("XSS_FLAG", "flag{i_5ucc3ssfu1ly_x553d}")
PATH_TRAVERSAL_FLAG = os.getenv("PATH_TRAVERSAL_FLAG", "flag{p4th_tr4v3rs4l_w1ns}")
ID_GUESSING_FLAG = os.getenv("ID_GUESSING_FLAG", "flag{1d0r_1d_gu3ss1ng_w1n}")
COOKIE_ROLE_FLAG = os.getenv("COOKIE_ROLE_FLAG", "flag{cl13nt_c00k13_r0l3_t4mp3r}")

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHALLENGES_DIR = os.path.join(BASE_DIR, "challenges")
PATH_TRAVERSAL_BASE = os.path.join(CHALLENGES_DIR, "path_traversal_files", "bobmcgee")
_ADMIN_DB_PATH_RAW = os.getenv("ADMIN_DB_PATH", os.path.join("data", "admin_panel.db"))
ADMIN_DB_PATH = _ADMIN_DB_PATH_RAW if os.path.isabs(_ADMIN_DB_PATH_RAW) else os.path.join(BASE_DIR, _ADMIN_DB_PATH_RAW)

# Feature flags
ENABLE_CORS = os.getenv("ENABLE_CORS", "true").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

# XSS Detection
XSS_DETECTION_ENABLED = os.getenv("XSS_DETECTION_ENABLED", "true").lower() == "true"

# CTF info banner
ENABLE_CTF_INFO_BANNER = os.getenv("ENABLE_CTF_INFO_BANNER", "true").lower() == "true"
CTF_INFO_BANNER_TEXT = os.getenv(
	"CTF_INFO_BANNER_TEXT",
	"This environment contains intentionally vulnerable challenge apps for CTF use only.",
)

# Admin panel
ADMIN_PANEL_PASSWORD = os.getenv("ADMIN_PANEL_PASSWORD", "")
ADMIN_SESSION_TTL_SECONDS = int(os.getenv("ADMIN_SESSION_TTL_SECONDS", "3600"))
ADMIN_SECURE_COOKIE = os.getenv("ADMIN_SECURE_COOKIE", "false").lower() == "true"
