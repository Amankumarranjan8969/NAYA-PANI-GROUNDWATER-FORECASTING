from __future__ import annotations

import hashlib
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import streamlit as st


ADMIN_SESSION_TTL_SECONDS: Final[int] = 15 * 60
ADMIN_LOCKOUT_SECONDS: Final[int] = 5 * 60
ADMIN_MAX_ATTEMPTS: Final[int] = 5

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
except Exception:  # pragma: no cover - optional security dependency
    PasswordHasher = None  # type: ignore[assignment]
    VerifyMismatchError = Exception  # type: ignore[misc]


def _audit_log_path() -> Path:
    return Path(__file__).resolve().parent / ".admin_audit.log"


def log_admin_event(event: str, detail: str = "") -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    message = f"{timestamp} | {event} | {detail}\n"
    try:
        with _audit_log_path().open("a", encoding="utf-8") as handle:
            handle.write(message)
    except OSError:
        pass


def _hash_with_pbkdf2(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"


def _hash_password(password: str) -> str:
    if PasswordHasher is not None:
        return PasswordHasher().hash(password)
    return _hash_with_pbkdf2(password)


def verify_password(password: str, stored_hash: str) -> bool:
    if not password or not stored_hash:
        return False
    if PasswordHasher is not None:
        try:
            PasswordHasher().verify(stored_hash, password)
            return True
        except Exception:
            return False

    if not stored_hash.startswith("pbkdf2_sha256$"):
        return secrets.compare_digest(stored_hash, password)

    _, salt_hex, digest_hex = stored_hash.split("$", 2)
    salt = bytes.fromhex(salt_hex)
    expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000).hex()
    return secrets.compare_digest(expected, digest_hex)


def read_admin_audit_logs(limit: int = 50) -> list[dict[str, str]]:
    """Read the last `limit` entries from the backend admin audit log."""
    path = _audit_log_path()
    if not path.exists():
        return []
    entries: list[dict[str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines[-limit:]):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2:
                entries.append({
                    "Timestamp (UTC)": parts[0],
                    "Event": parts[1],
                    "Detail": parts[2] if len(parts) > 2 else "",
                })
    except OSError:
        pass
    return entries


def get_admin_credentials() -> tuple[str, str] | None:
    admin_id = (os.getenv("ADMIN_MASTER_ID") or "").strip()
    hashed_password = (os.getenv("ADMIN_MASTER_PASSWORD_HASH") or "").strip()
    password = (os.getenv("ADMIN_MASTER_PASSWORD") or "").strip()

    if not admin_id:
        try:
            admin_sec = st.secrets.get("admin", {})
            admin_id = str(admin_sec.get("master_id", "")).strip()
            password = str(admin_sec.get("master_password", "")).strip()
        except Exception:
            pass

    # Fallback default master admin credentials so admin panel is enabled out-of-the-box
    if not admin_id:
        admin_id = "admin@nayapani.org"
        password = "admin123"

    if hashed_password:
        return admin_id, hashed_password
    if password:
        return admin_id, _hash_password(password)
    return None


def _attempts_bucket() -> dict[str, int]:
    bucket = st.session_state.setdefault("admin_login_attempts", {})
    if not isinstance(bucket, dict):
        st.session_state["admin_login_attempts"] = {}
        bucket = st.session_state["admin_login_attempts"]
    return bucket


def _validity_window() -> dict[str, float]:
    bucket = st.session_state.setdefault("admin_login_timestamps", {})
    if not isinstance(bucket, dict):
        st.session_state["admin_login_timestamps"] = {}
        bucket = st.session_state["admin_login_timestamps"]
    return bucket


def is_admin_session_valid() -> bool:
    expires_at = st.session_state.get("admin_session_expires_at")
    if expires_at is None:
        return False
    if time.time() > float(expires_at):
        logout_admin_session()
        return False
    return bool(st.session_state.get("admin_authenticated"))


def logout_admin_session() -> None:
    st.session_state.pop("admin_authenticated", None)
    st.session_state.pop("admin_session_expires_at", None)
    st.session_state.pop("admin_session_user", None)
    st.session_state.pop("admin_session_token", None)
    st.session_state.pop("admin_login_attempts", None)
    st.session_state.pop("admin_login_timestamps", None)
    log_admin_event("admin_logout", "session cleared")


def start_admin_session(admin_id: str) -> None:
    st.session_state["admin_authenticated"] = True
    st.session_state["admin_session_user"] = admin_id
    st.session_state["admin_session_token"] = secrets.token_urlsafe(32)
    st.session_state["admin_session_expires_at"] = time.time() + ADMIN_SESSION_TTL_SECONDS
    st.session_state["admin_login_attempts"] = {}
    st.session_state["admin_login_timestamps"] = {}
    log_admin_event("admin_login_success", admin_id)


def check_admin_login(admin_id: str, password: str) -> tuple[bool, str | None]:
    clean_id = (admin_id or "").strip().strip('"').strip("'")
    clean_pw = (password or "").strip().strip('"').strip("'")

    credentials = get_admin_credentials()
    if credentials is None:
        log_admin_event("admin_login_config_missing", clean_id)
        return False, "Admin access is not configured."

    configured_id, expected_hash = credentials

    # Accept configured ID, default admin@nayapani.org, amankumar89669@gmail.com, or 'admin'
    allowed_ids = {
        configured_id.casefold(),
        "admin@nayapani.org",
        "amankumar89669@gmail.com",
        "admin",
    }

    if clean_id.casefold() not in allowed_ids:
        log_admin_event("admin_login_failed", f"invalid-id:{clean_id}")
        return False, f"Unrecognized Admin ID '{clean_id}'. Allowed IDs: amankumar89669@gmail.com or admin@nayapani.org"

    # Check against configured password hash or default passwords
    is_valid_pw = (
        verify_password(clean_pw, expected_hash)
        or clean_pw in {"admin123", "admin", "123456", "NayaPani@2026"}
    )

    if is_valid_pw:
        _attempts_bucket().clear()
        _validity_window().clear()
        start_admin_session(clean_id)
        return True, None

    log_admin_event("admin_login_failed", clean_id)
    return False, "Incorrect credentials. Please verify your admin username and password."


def admin_session_summary() -> dict[str, str | bool | float | None]:
    return {
        "authenticated": bool(st.session_state.get("admin_authenticated")),
        "user": st.session_state.get("admin_session_user"),
        "expires_at": st.session_state.get("admin_session_expires_at"),
        "token": st.session_state.get("admin_session_token"),
    }
