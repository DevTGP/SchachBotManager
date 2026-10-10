"""Single Windows processes through the Win32 API (ctypes, no dependency).

NtSuspendProcess is not documented but stable since Windows XP; debuggers and Process Explorer
use it.
"""

import ctypes
from ctypes import wintypes

from sbm.viewer.process import PROGRAM as VIEWER_PROGRAM

TH32CS_SNAPPROCESS = 0x00000002
PROCESS_TERMINATE = 0x0001
PROCESS_SET_QUOTA = 0x0100
PROCESS_SUSPEND_RESUME = 0x0800
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SYNCHRONIZE = 0x00100000
MEMBER_ACCESS = (
    PROCESS_TERMINATE | PROCESS_SUSPEND_RESUME | PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE
)
WAIT_TIMEOUT = 0x00000102
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value


class PROCESSENTRY32W(ctypes.Structure):  # noqa: N801 (Win32 name)
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_ntdll = ctypes.WinDLL("ntdll")


def declare(function, argtypes, restype=wintypes.BOOL) -> None:
    function.argtypes = argtypes
    function.restype = restype


declare(kernel32.CreateToolhelp32Snapshot, [wintypes.DWORD, wintypes.DWORD], wintypes.HANDLE)
declare(kernel32.Process32FirstW, [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)])
declare(kernel32.Process32NextW, [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)])
declare(kernel32.OpenProcess, [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE)
declare(kernel32.CloseHandle, [wintypes.HANDLE])
declare(kernel32.TerminateProcess, [wintypes.HANDLE, wintypes.UINT])
declare(kernel32.WaitForSingleObject, [wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD)
declare(kernel32.GetProcessTimes, [wintypes.HANDLE, *[ctypes.POINTER(wintypes.FILETIME)] * 4])
declare(_ntdll.NtSuspendProcess, [wintypes.HANDLE], ctypes.c_long)
declare(_ntdll.NtResumeProcess, [wintypes.HANDLE], ctypes.c_long)


def check(succeeded: object) -> None:
    if not succeeded:
        raise ctypes.WinError(ctypes.get_last_error())


def children_by_parent() -> dict[int, list[int]]:
    """The ids of the running processes by the id of the process that started them.

    Windows keeps a parent's id after the parent ended and reuses ids, so a listed child may
    be unrelated; compare the creation times. The viewer window of a bot (E106) is left out, so
    that it stays usable while the bot is frozen.
    """
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        children: dict[int, list[int]] = {}
        found = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while found:
            if (
                entry.th32ProcessID != entry.th32ParentProcessID
                and entry.szExeFile.lower() != VIEWER_PROGRAM
            ):
                children.setdefault(entry.th32ParentProcessID, []).append(entry.th32ProcessID)
            found = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
        return children
    finally:
        kernel32.CloseHandle(snapshot)


class Process:
    """An open handle to a process; while it is open, the id is not reused."""

    def __init__(self, pid: int, handle: int) -> None:
        self.pid = pid
        self._handle = handle
        times = [wintypes.FILETIME() for _ in range(4)]
        check(kernel32.GetProcessTimes(handle, *(ctypes.byref(time) for time in times)))
        self.created = times[0].dwHighDateTime << 32 | times[0].dwLowDateTime

    @classmethod
    def open(cls, pid: int, access: int = MEMBER_ACCESS) -> "Process | None":
        """None if the process no longer exists or cannot be opened."""
        handle = kernel32.OpenProcess(access, False, pid)
        if not handle:
            return None
        try:
            return cls(pid, handle)
        except OSError:
            kernel32.CloseHandle(handle)
            return None

    @property
    def handle(self) -> int:
        return self._handle

    def alive(self) -> bool:
        return kernel32.WaitForSingleObject(self._handle, 0) == WAIT_TIMEOUT

    def suspend(self) -> bool:
        """False if the process has ended."""
        return self._nt_call(_ntdll.NtSuspendProcess)

    def resume(self) -> bool:
        return self._nt_call(_ntdll.NtResumeProcess)

    def _nt_call(self, function) -> bool:
        status = function(self._handle)
        if status >= 0:
            return True
        if not self.alive():
            return False
        raise OSError(f"NTSTATUS {status & 0xFFFFFFFF:#010x} for process {self.pid}")

    def terminate(self) -> None:
        kernel32.TerminateProcess(self._handle, 1)  # fails only if it is already ending

    def close(self) -> None:
        if self._handle:
            kernel32.CloseHandle(self._handle)
            self._handle = None
