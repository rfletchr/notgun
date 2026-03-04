from __future__ import annotations

import platform
import time
import webbrowser
import dataclasses

import requests
import requests.exceptions
import shotgun_api3
import threading


class NotgunAuthError(Exception):
    """Base class for notgun authentication errors."""


class AuthenticationError(NotgunAuthError):
    """Raised on network or API failure during authentication."""


class AuthenticationTimeout(NotgunAuthError):
    """Raised when the user does not approve the browser session before timeout."""


@dataclasses.dataclass(frozen=True)
class Credentials:
    site_url: str
    login: str
    session_token: str


_POLL_INTERVAL = 2  # seconds
_ASL_PATH = "/internal_api/app_session_request"


def authenticate(
    site_url: str,
    http_proxy: str | None = None,
    timeout: int = 180,
    cancel_event: threading.Event | None = None,
) -> Credentials:
    """Authenticate against a ShotGrid site using the App Session Launcher flow.

    Opens the system browser so the user can log in, then polls the ShotGrid
    backend until the session is approved.

    Args:
        site_url:   The ShotGrid site URL, e.g. ``https://studio.shotgunstudio.com``.
        http_proxy: Optional proxy URL, e.g. ``http://proxy.example.com:8080``.
        timeout:    Seconds to wait for browser approval before raising
                    :class:`AuthenticationTimeout`.

    Returns:
        :class:`Credentials` on success.

    Raises:
        :class:`AuthenticationError` on network or API failure.
        :class:`AuthenticationTimeout` if the user does not approve in time.
    """
    cancel_event = cancel_event or threading.Event()

    site_url = site_url.strip().rstrip("/")
    if not site_url.startswith(("http://", "https://")):
        site_url = "https://" + site_url

    session = requests.Session()
    if http_proxy:
        session.proxies = {"http": http_proxy, "https": http_proxy}

    session_id, browser_url = begin_request(session, site_url)

    webbrowser.open(browser_url)

    return poll_for_credentials(
        session,
        site_url,
        session_id,
        timeout,
        cancel_event,
    )


def begin_request(session: requests.Session, site_url: str):
    try:
        data = {"appName": "toolkit", "machineId": platform.node()}
        resp = session.post(site_url + _ASL_PATH, json=data, timeout=15)
        resp.raise_for_status()

        response_data = resp.json()

    except requests.exceptions.RequestException as exc:
        raise AuthenticationError(f"Failed to create session request: {exc}") from exc

    session_id = response_data.get("sessionRequestId") or response_data.get("id")
    browser_url = response_data.get("url")

    if not session_id or not browser_url:
        raise AuthenticationError(f"Unexpected ASL response: {response_data!r}")

    return session_id, browser_url


def poll_for_credentials(
    session: requests.Session,
    site_url: str,
    session_id: str,
    timeout: int,
    cancel_event: threading.Event,
) -> Credentials:

    poll_url = f"{site_url}{_ASL_PATH}/{session_id}"
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline and not cancel_event.is_set():
        time.sleep(_POLL_INTERVAL)

        if cancel_event.is_set():
            break

        try:
            resp = session.put(poll_url, json={}, timeout=15)

            if resp.status_code == 404:
                raise AuthenticationTimeout(
                    "The login session expired before it was approved in the browser."
                )
            resp.raise_for_status()
            result = resp.json()

        except AuthenticationTimeout:
            raise
        except requests.exceptions.RequestException as exc:
            raise AuthenticationError(f"Network error while polling: {exc}") from exc

        if result.get("approved"):
            login = result.get("userLogin") or result.get("login", "")
            token = result.get("sessionToken") or result.get("session_token", "")
            if not token:
                raise AuthenticationError(
                    f"Session approved but no token in response: {result!r}"
                )
            return Credentials(site_url=site_url, login=login, session_token=token)

    raise AuthenticationTimeout(
        f"Timed out after {timeout}s waiting for browser login approval."
    )


def validate(creds: Credentials, http_proxy: str | None = None) -> bool:
    """Return True if *creds* are still accepted by the server, False if expired.

    Makes a minimal authenticated API call (``find_one("HumanUser", [])``) and
    interprets :class:`shotgun_api3.AuthenticationFault` as an expired token.

    Raises:
        :class:`AuthenticationError` on unexpected network failures.
    """
    try:
        sg = shotgun_api3.Shotgun(
            creds.site_url,
            session_token=creds.session_token,
            http_proxy=http_proxy,
        )
        sg.find_one("HumanUser", [])
        return True
    except shotgun_api3.AuthenticationFault:
        return False
    except Exception as exc:
        raise AuthenticationError(
            f"Unexpected error validating credentials: {exc}"
        ) from exc


if __name__ == "__main__":
    creds = authenticate("https://elephant-goldfish.shotgrid.autodesk.com")
    if validate(creds):
        print("Success")
