"""
MSAL-based Microsoft Entra ID authentication manager.
Token is held in-memory only — never written to disk.
"""

import threading
import msal

from config import AZURE_CLIENT_ID, AZURE_AUTHORITY, FABRIC_SCOPES


class AuthManager:
    """
    Wraps an MSAL PublicClientApplication instance and provides
    interactive login + silent refresh logic.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._app = msal.PublicClientApplication(
            client_id=AZURE_CLIENT_ID,
            authority=AZURE_AUTHORITY,
        )
        self._account = None
        self._last_result: dict | None = None

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_authenticated(self) -> bool:
        return self._account is not None

    @property
    def display_name(self) -> str:
        if self._account:
            return self._account.get("username", "Unknown User")
        return ""

    @property
    def access_token(self) -> str | None:
        token = self._get_token_silent()
        if token:
            return token.get("access_token")
        return None

    # ── Public ────────────────────────────────────────────────────────────────

    def login_interactive(self) -> dict:
        """
        Opens an MSAL browser popup for interactive login.
        Returns the full MSAL result dict (or raises on failure).
        Thread-safe but keep calls from a non-main thread if you don't
        want to block the Qt event loop.
        """
        with self._lock:
            result = self._app.acquire_token_interactive(
                scopes=FABRIC_SCOPES,
                prompt="select_account",
            )
            self._handle_result(result)
            return result

    def logout(self) -> None:
        with self._lock:
            accounts = self._app.get_accounts()
            for account in accounts:
                self._app.remove_account(account)
            self._account = None
            self._last_result = None

    # ── Internal ──────────────────────────────────────────────────────────────

    def _handle_result(self, result: dict) -> None:
        if "access_token" in result:
            self._last_result = result
            accounts = self._app.get_accounts()
            if accounts:
                self._account = accounts[0]
        else:
            raise RuntimeError(
                result.get("error_description") or result.get("error") or "Authentication failed"
            )

    def _get_token_silent(self) -> dict | None:
        if not self._account:
            return None
        with self._lock:
            result = self._app.acquire_token_silent(
                scopes=FABRIC_SCOPES,
                account=self._account,
            )
            if result and "access_token" in result:
                return result
            # Silent refresh failed — caller should prompt interactive login
            return None


# Singleton — shared across the entire app session
auth_manager = AuthManager()
