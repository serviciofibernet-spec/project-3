from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Iterable, Optional

import paramiko


@dataclass
class SSHClientConfig:
    host: str
    port: int
    username: str
    password: str
    prompt_regex: str = r"[#>] ?$"
    timeout_s: int = 15


class SSHClient:
    def __init__(self, cfg: SSHClientConfig):
        self._cfg = cfg
        self._client: Optional[paramiko.SSHClient] = None
        self._shell: Optional[paramiko.Channel] = None
        self._prompt_re = re.compile(cfg.prompt_regex)

    def __enter__(self) -> "SSHClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def connect(self) -> None:
        if self._client is not None:
            return
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self._cfg.host,
            port=self._cfg.port,
            username=self._cfg.username,
            password=self._cfg.password,
            look_for_keys=False,
            allow_agent=False,
            timeout=self._cfg.timeout_s,
        )
        self._client = client
        self._shell = client.invoke_shell(term="vt100", width=160, height=1000)
        self._shell.settimeout(self._cfg.timeout_s)
        # Drain initial banner until prompt
        self._read_until_prompt()

    def close(self) -> None:
        try:
            if self._shell is not None:
                self._shell.close()
        finally:
            self._shell = None
            if self._client is not None:
                self._client.close()
                self._client = None

    def run_commands(self, commands: Iterable[str], stop_on_error: bool = False) -> str:
        if self._client is None:
            self.connect()
        assert self._shell is not None
        outputs: list[str] = []
        for raw_cmd in commands:
            cmd = raw_cmd.rstrip("\r\n") + "\n"
            self._shell.send(cmd)
            out = self._read_until_prompt()
            outputs.append(out)
            if stop_on_error and self._looks_like_error(out):
                break
        return "\n".join(outputs)

    def send(self, text: str) -> None:
        assert self._shell is not None
        self._shell.send(text)

    def _read_until_prompt(self) -> str:
        """Read from shell until prompt regex matches the last line or timeout.
        Not a full expect; good enough for CLI-style interactions typical of OLTs.
        """
        assert self._shell is not None
        chunks: list[str] = []
        buffer = ""
        end_by = time.time() + self._cfg.timeout_s
        while True:
            try:
                if self._shell.recv_ready():
                    data = self._shell.recv(65536)
                    if not data:
                        break
                    text = data.decode(errors="ignore")
                    buffer += text
                    chunks.append(text)
                    # Check last line for prompt
                    last_line = buffer.splitlines()[-1] if buffer.splitlines() else buffer
                    if self._prompt_re.search(last_line):
                        break
                else:
                    if time.time() > end_by:
                        break
                    time.sleep(0.05)
            except Exception:
                break
        return "".join(chunks)

    @staticmethod
    def _looks_like_error(output: str) -> bool:
        lowered = output.lower()
        return any(token in lowered for token in ["error", "invalid", "unknown command", "fail", "% "])
