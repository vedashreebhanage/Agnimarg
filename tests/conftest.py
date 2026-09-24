import os
import sys
import tempfile

# Keep test runs from writing into the real demo's audit trail — must be set
# before any test module imports `audit` or `main` (which imports `audit`).
os.environ.setdefault(
    "AGNIMARG_AUDIT_DB_PATH", os.path.join(tempfile.gettempdir(), "agnimarg_test_audit.db")
)

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))
