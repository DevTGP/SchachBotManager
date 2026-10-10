"""A Windows job object holding a bot and every process it starts (ctypes, no dependency).

The job ends all its processes when the arena exits, even when it crashes. The process starts
suspended and is resumed only once it is in the job, so its children start inside it, too.
Some children leave the job anyway: a venv's launcher starts the real Python as a child, and
the Python from the Microsoft Store runs outside of the job. Freezing and killing therefore
also cover the descendants of the job's processes; the launcher ends its child when it ends.
"""

import contextlib
import ctypes
from ctypes import wintypes

from sbm.arena import windows_processes as processes
from sbm.arena.windows_processes import Process, check, declare, kernel32

CREATE_SUSPENDED = 0x00000004
# Ctrl+C in the console reaches the arena only; the arena then ends the bots itself.
CREATE_NEW_PROCESS_GROUP = 0x00000200
POPEN_OPTIONS = {"creationflags": CREATE_SUSPENDED | CREATE_NEW_PROCESS_GROUP}

JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x00000800
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_BASIC_PROCESS_ID_LIST = 3
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
MAX_LISTED_PROCESSES = 256


class IO_COUNTERS(ctypes.Structure):  # noqa: N801 (Win32 name)
    _fields_ = [
        (f"{kind}{count}", ctypes.c_ulonglong)
        for count in ("OperationCount", "TransferCount")
        for kind in ("Read", "Write", "Other")
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):  # noqa: N801
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):  # noqa: N801
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class JOBOBJECT_BASIC_PROCESS_ID_LIST(ctypes.Structure):  # noqa: N801
    _fields_ = [
        ("NumberOfAssignedProcesses", wintypes.DWORD),
        ("NumberOfProcessIdsInList", wintypes.DWORD),
        ("ProcessIdList", ctypes.c_size_t * MAX_LISTED_PROCESSES),
    ]


declare(kernel32.CreateJobObjectW, [wintypes.LPVOID, wintypes.LPCWSTR], wintypes.HANDLE)
declare(
    kernel32.SetInformationJobObject,
    [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD],
)
declare(
    kernel32.QueryInformationJobObject,
    [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, wintypes.LPDWORD],
)
declare(kernel32.AssignProcessToJobObject, [wintypes.HANDLE, wintypes.HANDLE])
declare(kernel32.TerminateJobObject, [wintypes.HANDLE, wintypes.UINT])


def _create_job(process: int) -> int:
    job = kernel32.CreateJobObjectW(None, None)
    check(job)
    try:
        limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        # Breakaway only on request: the viewer window of the bot leaves the job (E106).
        limits.BasicLimitInformation.LimitFlags = (
            JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_BREAKAWAY_OK
        )
        check(
            kernel32.SetInformationJobObject(
                job,
                JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                ctypes.byref(limits),
                ctypes.sizeof(limits),
            )
        )
        check(kernel32.AssignProcessToJobObject(job, process))
    except OSError:
        kernel32.CloseHandle(job)
        raise
    return job


class ProcessGroup:
    """The processes of one bot started with POPEN_OPTIONS; resumes the bot when created.

    Known processes stay open, so their ids are not reused, and are frozen first, so the bot
    stops at once; the search for new processes follows.
    """

    def __init__(self, pid: int) -> None:
        root = Process.open(pid, processes.MEMBER_ACCESS | processes.PROCESS_SET_QUOTA)
        if root is None:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            try:
                self._job = _create_job(root.handle)
            finally:
                # Resumed in any case: without the job the bot still runs, only unfrozen.
                root.resume()
        except OSError:
            root.close()
            raise
        self._started = root.created
        self._members: dict[int, Process] = {pid: root}
        self._suspended: list[Process] = []

    def _job_pids(self) -> list[int]:
        listing = JOBOBJECT_BASIC_PROCESS_ID_LIST()
        check(
            kernel32.QueryInformationJobObject(
                self._job,
                JOB_OBJECT_BASIC_PROCESS_ID_LIST,
                ctypes.byref(listing),
                ctypes.sizeof(listing),
                None,
            )
        )
        return list(listing.ProcessIdList[: listing.NumberOfProcessIdsInList])

    def _discover(self) -> list[Process]:
        """Processes of the bot not known yet: new ones in the job and descendants of known
        ones, parents before children."""
        children = processes.children_by_parent()
        found = []

        def adopt(pid: int, earliest: int) -> None:
            if pid in self._members:
                return
            process = Process.open(pid)
            if process is None:
                return
            if process.created < earliest:  # the id belonged to the parent's predecessor
                process.close()
                return
            self._members[pid] = process
            found.append(process)

        for pid in self._job_pids():
            adopt(pid, self._started)
        parents = list(self._members.values())
        for parent in parents:
            count = len(found)
            for pid in children.get(parent.pid, []):
                adopt(pid, parent.created)
            parents.extend(found[count:])
        return found

    def _freeze(self, members: list[Process]) -> None:
        for member in members:
            if member.suspend():
                self._suspended.append(member)
            else:
                self._members.pop(member.pid).close()

    def suspend(self) -> None:
        self._freeze(list(self._members.values()))
        # Look again after freezing new processes: they may have started children meanwhile.
        while new := self._discover():
            self._freeze(new)

    def resume(self) -> None:
        suspended, self._suspended = self._suspended, []
        for member in reversed(suspended):
            member.resume()

    def kill(self) -> None:
        with contextlib.suppress(OSError):
            self._discover()
        check(kernel32.TerminateJobObject(self._job, 1))
        for member in self._members.values():
            member.terminate()

    def close(self) -> None:
        """Releases the job and the handles; processes still in the job end."""
        for member in self._members.values():
            member.close()
        self._members.clear()
        if self._job:
            kernel32.CloseHandle(self._job)
            self._job = None
