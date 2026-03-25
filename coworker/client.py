import base64
import json
import re

import requests


class CoworkerClient:
    def __init__(self, base_url: str, username: str, password: str, case_id: str = None):
        self.base_url = base_url.rstrip("/")
        self.admin_base = self.base_url.replace("/api/v1", "")
        self.username = username
        self.password = password
        self.case_id = case_id
        self._session: requests.Session = None

    def _basic_header(self) -> str:
        return "Basic " + base64.b64encode(f"{self.username}:{self.password}".encode()).decode()

    def login(self) -> None:
        s = requests.Session()
        s.headers.update({"Authorization": self._basic_header()})

        r = s.get(f"{self.admin_base}/admin/login")
        xsrf = s.cookies.get("XSRF-TOKEN", "")

        s.post(f"{self.admin_base}/admin/login", data={
            "username": self.username,
            "password": self.password,
            "_csrf": xsrf,
        }, allow_redirects=True, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-XSRF-TOKEN": xsrf,
        })

        s.get(f"{self.admin_base}/admin/test")
        self._session = s

    def _ensure_logged_in(self) -> None:
        if self._session is None:
            self.login()

    def get_coworkers(self) -> list:
        self._ensure_logged_in()
        r = self._session.get(f"{self.base_url}/coworkers")
        r.raise_for_status()
        return r.json()

    def create_session(self, coworker_id: str) -> str:
        self._ensure_logged_in()
        xsrf = self._session.cookies.get("XSRF-TOKEN", "")
        params = {"coworkerId": coworker_id}
        if self.case_id:
            params["caseId"] = self.case_id

        r = self._session.post(f"{self.admin_base}/admin/test/session", params=params, headers={
            "X-XSRF-TOKEN": xsrf,
            "Hx-Request": "true",
        })
        r.raise_for_status()
        m = re.search(r'data-session-id="([^"]+)"', r.text)
        if not m:
            raise ValueError("Session ID not found in response")
        return m.group(1)

    def stream_message(self, session_id: str, prompt: str):
        """Yields response tokens as strings."""
        self._ensure_logged_in()
        xsrf = self._session.cookies.get("XSRF-TOKEN", "")

        with self._session.get(
            f"{self.admin_base}/admin/test/stream",
            params={"sessionId": session_id, "message": prompt},
            headers={"X-XSRF-TOKEN": xsrf, "Hx-Request": "true"},
            stream=True,
        ) as r:
            r.raise_for_status()
            current_event = None
            for line in r.iter_lines():
                if not line:
                    current_event = None
                    continue
                decoded = line.decode("utf-8")
                if decoded.startswith("event:"):
                    current_event = decoded[6:].strip()
                elif decoded.startswith("data:") and current_event == "token":
                    try:
                        yield json.loads(decoded[5:].strip())
                    except Exception:
                        pass
