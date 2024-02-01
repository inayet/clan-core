import os
import signal
import sys
import traceback
from pathlib import Path
from typing import Any

import gi
from clan_cli.errors import ClanError

gi.require_version("GdkPixbuf", "2.0")

import dataclasses
import multiprocessing as mp
from collections.abc import Callable


# Kill the new process and all its children by sending a SIGTERM signal to the process group
def _kill_group(proc: mp.Process) -> None:
    pid = proc.pid
    if proc.is_alive() and pid:
        os.killpg(pid, signal.SIGTERM)
    else:
        print(f"Process {proc.name} with pid {pid} is already dead", file=sys.stderr)


@dataclasses.dataclass(frozen=True)
class MPProcess:
    name: str
    proc: mp.Process
    out_file: Path

    # Kill the new process and all its children by sending a SIGTERM signal to the process group
    def kill_group(self) -> None:
        _kill_group(proc=self.proc)


def _set_proc_name(name: str) -> None:
    if sys.platform != "linux":
        return
    import ctypes

    # Define the prctl function with the appropriate arguments and return type
    libc = ctypes.CDLL("libc.so.6")
    prctl = libc.prctl
    prctl.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
    ]
    prctl.restype = ctypes.c_int

    # Set the process name to "my_process"
    prctl(15, name.encode(), 0, 0, 0)


def _init_proc(
    func: Callable,
    out_file: Path,
    proc_name: str,
    on_except: Callable[[Exception, mp.process.BaseProcess], None] | None,
    **kwargs: Any,
) -> None:
    # Create a new process group
    os.setsid()

    # Open stdout and stderr
    with open(out_file, "w") as out_fd:
        os.dup2(out_fd.fileno(), sys.stdout.fileno())
        os.dup2(out_fd.fileno(), sys.stderr.fileno())

    # Print some information
    pid = os.getpid()
    gpid = os.getpgid(pid=pid)
    print(f"Started new process pid={pid} gpid={gpid}", file=sys.stderr)

    # Set the process name
    _set_proc_name(proc_name)

    # Close stdin
    sys.stdin.close()

    # Execute the main function
    print(f"Executing function {func.__name__} now", file=sys.stderr)
    try:
        func(**kwargs)
    except Exception as ex:
        traceback.print_exc()
        if on_except is not None:
            on_except(ex, mp.current_process())
    finally:
        pid = os.getpid()
        gpid = os.getpgid(pid=pid)
        print(f"Killing process group pid={pid} gpid={gpid}", file=sys.stderr)
        os.killpg(gpid, signal.SIGTERM)


def spawn(
    *,
    log_dir: Path,
    on_except: Callable[[Exception, mp.process.BaseProcess], None] | None,
    func: Callable,
    **kwargs: Any,
) -> MPProcess:
    # Decouple the process from the parent
    if mp.get_start_method(allow_none=True) is None:
        mp.set_start_method(method="forkserver")

    if not log_dir.is_dir():
        raise ClanError(f"Log path {log_dir} is not a directory")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Set names
    proc_name = f"MPExec:{func.__name__}"
    out_file = log_dir / "out.log"

    # Start the process
    proc = mp.Process(
        target=_init_proc,
        args=(func, out_file, proc_name, on_except),
        name=proc_name,
        kwargs=kwargs,
    )
    proc.start()

    # Print some information
    cmd = f"tail -f {out_file}"
    print(f"Connect to stdout with: {cmd}")

    # Return the process
    mp_proc = MPProcess(name=proc_name, proc=proc, out_file=out_file)

    return mp_proc