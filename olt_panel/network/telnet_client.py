from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Iterable, Optional

import telnetlib


@dataclass
class TelnetClientConfig:
    host: str
    port: int = 23
    username: str = ""
    password: str = ""
    prompt_regex: str = r"[#>] ?$"
    timeout_s: int = 15


class TelnetClient:
    def __init__(self, cfg: TelnetClientConfig):
        self._cfg = cfg
        self._tn: Optional[telnetlib.Telnet] = None
        self._prompt_re = re.compile(cfg.prompt_regex, re.IGNORECASE)

    def __enter__(self) -> "TelnetClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def connect(self) -> None:
        if self._tn is not None:
            return
        tn = telnetlib.Telnet(self._cfg.host, self._cfg.port, timeout=self._cfg.timeout_s)
        self._tn = tn
        # Attempt login conversation commonly used by network devices
        self._login()
        # Drain banner until prompt
        self._read_until_prompt()

    def close(self) -> None:
        try:
            if self._tn is not None:
                try:
                    self._tn.write(b"exit\n")
                except Exception:
                    pass
                self._tn.close()
        finally:
            self._tn = None

    def run_commands(self, commands: Iterable[str], stop_on_error: bool = False) -> str:
        if self._tn is None:
            self.connect()
        outputs: list[str] = []
        for raw_cmd in commands:
            cmd = raw_cmd.rstrip("\r\n") + "\n"
            self._tn.write(cmd.encode())
            out = self._read_until_prompt()
            outputs.append(out)
            if stop_on_error and self._looks_like_error(out):
                break
        return "\n".join(outputs)

    def _login(self) -> None:
        assert self._tn is not None
        # Try to detect username/password prompts
        end_by = time.time() + self._cfg.timeout_s
        received = b""
        while time.time() < end_by:
            try:
                chunk = self._tn.read_very_eager()
            except EOFError:
                break
            if chunk:
                received += chunk
                lower = received.lower()
                if b"login:" in lower or b"username:" in lower:
                    self._tn.write((self._cfg.username + "\n").encode())
                    received = b""
                if b"password:" in lower:
                    self._tn.write((self._cfg.password + "\n").encode())
                    received = b""
                # If we already see a prompt, stop
                if self._prompt_re.search(received.decode(errors="ignore")):
                    break
            else:
                time.sleep(0.05)

    def _read_until_prompt(self) -> str:
        assert self._tn is not None
        buffer = ""
        end_by = time.time() + self._cfg.timeout_s
        while time.time() < end_by:
            data = self._tn.read_very_eager()
            if data:
                text = data.decode(errors="ignore")
                buffer += text
                last_line = buffer.splitlines()[-1] if buffer.splitlines() else buffer
                if self._prompt_re.search(last_line):
                    break
            else:
                time.sleep(0.05)
        return buffer

    @staticmethod
    def _looks_like_error(output: str) -> bool:
        lowered = output.lower()
        return any(token in lowered for token in ["error", "invalid", "unknown", "fail", "% "])
