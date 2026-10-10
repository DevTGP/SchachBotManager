"""A viewer process that records what the SDK writes, instead of opening a window."""

import io
import json


class FakeStdin(io.BytesIO):
    def __init__(self, broken: bool = False) -> None:
        super().__init__()
        self.broken = broken

    def write(self, data: bytes) -> int:
        if self.broken:
            raise BrokenPipeError("the window was closed")
        return super().write(data)

    def close(self) -> None:
        self.text = self.getvalue()
        super().close()


class FakeProcess:
    def __init__(self, broken: bool = False) -> None:
        self.stdin = FakeStdin(broken)
        self.returncode = None
        self.waited = False

    def poll(self) -> int | None:
        return self.returncode

    def wait(self) -> int:
        self.waited = True
        self.returncode = 0
        return 0

    def messages(self) -> list[dict]:
        data = self.stdin.text if self.stdin.closed else self.stdin.getvalue()
        return [json.loads(line) for line in data.splitlines()]
