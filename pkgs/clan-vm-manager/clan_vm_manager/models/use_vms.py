import os
import tempfile
import weakref
from datetime import datetime
from pathlib import Path
from typing import IO, Any, ClassVar

import gi
from clan_cli import vms
from clan_cli.clan_uri import ClanScheme, ClanURI
from clan_cli.errors import ClanError
from clan_cli.history.add import HistoryEntry
from clan_cli.history.list import list_history

from clan_vm_manager import assets
from clan_vm_manager.errors.show_error import show_error_dialog

from .executor import MPProcess, spawn

gi.require_version("Gtk", "4.0")
import logging
import multiprocessing as mp
import threading

from clan_cli.machines.machines import Machine
from gi.repository import Gio, GLib, GObject, Gtk

log = logging.getLogger(__name__)


class ClanGroup(GObject.Object):
    def __init__(self, url: str | Path, vms: list["VM"]) -> None:
        super().__init__()
        self.url = url
        self.vms = vms
        self.clan_name = vms[0].data.flake.clan_name
        self.list_store = Gio.ListStore.new(VM)

        for vm in vms:
            self.list_store.append(vm)


def init_grp_store(list_store: Gio.ListStore) -> None:
    groups: dict[str | Path, list["VM"]] = {}
    for vm in get_saved_vms():
        ll = groups.get(vm.data.flake.flake_url, [])
        ll.append(vm)
        groups[vm.data.flake.flake_url] = ll

    for url, vm_list in groups.items():
        grp = ClanGroup(url, vm_list)
        list_store.append(grp)


class Clans:
    list_store: Gio.ListStore
    _instance: "None | ClanGroup" = None

    # Make sure the VMS class is used as a singleton
    def __init__(self) -> None:
        raise RuntimeError("Call use() instead")

    @classmethod
    def use(cls: Any) -> "ClanGroup":
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls.list_store = Gio.ListStore.new(ClanGroup)
            init_grp_store(cls.list_store)

        return cls._instance

    def filter_by_name(self, text: str) -> None:
        if text:
            filtered_list = self.list_store
            filtered_list.remove_all()

            groups: dict[str | Path, list["VM"]] = {}
            for vm in get_saved_vms():
                ll = groups.get(vm.data.flake.flake_url, [])
                print(text, vm.data.flake.vm.machine_name)
                if text.lower() in vm.data.flake.vm.machine_name.lower():
                    ll.append(vm)
                    groups[vm.data.flake.flake_url] = ll

            for url, vm_list in groups.items():
                grp = ClanGroup(url, vm_list)
                filtered_list.append(grp)

        else:
            self.refresh()

    def refresh(self) -> None:
        self.list_store.remove_all()
        init_grp_store(self.list_store)


class VM(GObject.Object):
    # Define a custom signal with the name "vm_stopped" and a string argument for the message
    __gsignals__: ClassVar = {
        "vm_status_changed": (GObject.SignalFlags.RUN_FIRST, None, [GObject.Object]),
        "build_vm": (GObject.SignalFlags.RUN_FIRST, None, [GObject.Object, bool]),
    }

    def __init__(
        self,
        icon: Path,
        data: HistoryEntry,
    ) -> None:
        super().__init__()
        self.KILL_TIMEOUT = 6  # seconds
        self.data = data
        self.process = MPProcess("dummy", mp.Process(), Path("./dummy"))
        self._watcher_id: int = 0
        self._stop_watcher_id: int = 0
        self._stop_timer_init: datetime | None = None
        self._logs_id: int = 0
        self._log_file: IO[str] | None = None
        self.progress_bar: Gtk.ProgressBar = Gtk.ProgressBar()
        self.progress_bar.hide()
        self.progress_bar.set_hexpand(True)  # Horizontally expand
        self.prog_bar_id: int = 0
        self.log_dir = tempfile.TemporaryDirectory(
            prefix="clan_vm-", suffix=f"-{self.data.flake.flake_attr}"
        )
        self._finalizer = weakref.finalize(self, self.kill)
        self.connect("build_vm", self.build_vm)
        uri = ClanURI.from_str(
            url=self.data.flake.flake_url, flake_attr=self.data.flake.flake_attr
        )
        match uri.scheme:
            case ClanScheme.LOCAL.value(path):
                self.machine = Machine(
                    name=self.data.flake.flake_attr,
                    flake=path,  # type: ignore
                )
            case ClanScheme.REMOTE.value(url):
                self.machine = Machine(
                    name=self.data.flake.flake_attr,
                    flake=url,  # type: ignore
                )

    def _pulse_progress_bar(self) -> bool:
        self.progress_bar.pulse()
        return GLib.SOURCE_CONTINUE

    def build_vm(self, vm: "VM", _vm: "VM", building: bool) -> None:
        if building:
            log.info("Building VM")
            self.progress_bar.show()
            self.prog_bar_id = GLib.timeout_add(100, self._pulse_progress_bar)
            if self.prog_bar_id == 0:
                raise ClanError("Couldn't spawn a progess bar task")
        else:
            self.progress_bar.hide()
            if not GLib.Source.remove(self.prog_bar_id):
                log.error("Failed to remove progress bar task")
            log.info("VM built")

    def __start(self) -> None:
        log.info(f"Starting VM {self.get_id()}")
        vm = vms.run.inspect_vm(self.machine)

        # GLib.idle_add(self.emit, "build_vm", self, True)
        # self.process = spawn(
        #     on_except=None,
        #     log_dir=Path(str(self.log_dir.name)),
        #     func=vms.run.build_vm,
        #     machine=self.machine,
        #     vm=vm,
        # )
        # self.process.proc.join()

        # GLib.idle_add(self.emit, "build_vm", self, False)

        # if self.process.proc.exitcode != 0:
        #     log.error(f"Failed to build VM {self.get_id()}")
        #     return

        self.process = spawn(
            on_except=None,
            out_file=Path(str(self.log_dir.name)) / "vm.log",
            func=vms.run.run_vm,
            vm=vm,
        )
        log.debug(f"Started VM {self.get_id()}")
        GLib.idle_add(self.emit, "vm_status_changed", self)
        log.debug(f"Starting logs watcher on file: {self.process.out_file}")
        self._logs_id = GLib.timeout_add(50, self._get_logs_task)
        if self._logs_id == 0:
            raise ClanError("Failed to add logs watcher")

        log.debug(f"Starting VM watcher for: {self.machine.name}")
        self._watcher_id = GLib.timeout_add(50, self._vm_watcher_task)
        if self._watcher_id == 0:
            raise ClanError("Failed to add watcher")

    def start(self) -> None:
        if self.is_running():
            log.warn("VM is already running")
            return
        threading.Thread(target=self.__start).start()

    def _vm_watcher_task(self) -> bool:
        if not self.is_running():
            self.emit("vm_status_changed", self)
            log.debug("Removing VM watcher")
            return GLib.SOURCE_REMOVE

        return GLib.SOURCE_CONTINUE

    def _get_logs_task(self) -> bool:
        if not self.process.out_file.exists():
            return GLib.SOURCE_CONTINUE

        if not self._log_file:
            try:
                self._log_file = open(self.process.out_file)
            except Exception as ex:
                log.exception(ex)
                self._log_file = None
                return GLib.SOURCE_REMOVE

        line = os.read(self._log_file.fileno(), 4096)
        if len(line) != 0:
            print(line.decode("utf-8"), end="", flush=True)

        if not self.is_running():
            log.debug("Removing logs watcher")
            self._log_file = None
            return GLib.SOURCE_REMOVE

        return GLib.SOURCE_CONTINUE

    def is_running(self) -> bool:
        return self.process.proc.is_alive()

    def get_id(self) -> str:
        return f"{self.data.flake.flake_url}#{self.data.flake.flake_attr}"

    def __shutdown_watchdog(self) -> None:
        if self.is_running():
            assert self._stop_timer_init is not None
            diff = datetime.now() - self._stop_timer_init
            if diff.seconds > self.KILL_TIMEOUT:
                log.error(f"VM {self.get_id()} has not stopped. Killing it")
                self.process.kill_group()
            return GLib.SOURCE_CONTINUE
        else:
            log.info(f"VM {self.get_id()} has stopped")
            return GLib.SOURCE_REMOVE

    def __stop(self) -> None:
        log.info(f"Stopping VM {self.get_id()}")

        try:
            with self.machine.vm.qmp_ctx() as qmp:
                qmp.command("system_powerdown")
        except ClanError as e:
            log.debug(e)

        self._stop_timer_init = datetime.now()
        self._stop_watcher_id = GLib.timeout_add(100, self.__shutdown_watchdog)
        if self._stop_watcher_id == 0:
            raise ClanError("Failed to add stop watcher")

    def shutdown(self) -> None:
        if not self.is_running():
            return
        log.info(f"Stopping VM {self.get_id()}")
        threading.Thread(target=self.__stop).start()

    def kill(self) -> None:
        if not self.is_running():
            log.warning(f"Tried to kill VM {self.get_id()} is not running")
            return
        log.info(f"Killing VM {self.get_id()} now")
        self.process.kill_group()

    def read_whole_log(self) -> str:
        if not self.process.out_file.exists():
            log.error(f"Log file {self.process.out_file} does not exist")
            return ""
        return self.process.out_file.read_text()


class VMs:
    list_store: Gio.ListStore
    _instance: "None | VMs" = None

    # Make sure the VMS class is used as a singleton
    def __init__(self) -> None:
        raise RuntimeError("Call use() instead")

    @classmethod
    def use(cls: Any) -> "VMs":
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls.list_store = Gio.ListStore.new(VM)

            for vm in get_saved_vms():
                cls.list_store.append(vm)
        return cls._instance

    def filter_by_name(self, text: str) -> None:
        if text:
            filtered_list = self.list_store
            filtered_list.remove_all()
            for vm in get_saved_vms():
                if text.lower() in vm.data.flake.vm.machine_name.lower():
                    filtered_list.append(vm)
        else:
            self.refresh()

    def get_by_id(self, ident: str) -> None | VM:
        for vm in self.list_store:
            if ident == vm.get_id():
                return vm

        return None

    def get_running_vms(self) -> list[VM]:
        return list(filter(lambda vm: vm.is_running(), self.list_store))

    def kill_all(self) -> None:
        log.debug(f"Running vms: {self.get_running_vms()}")
        for vm in self.get_running_vms():
            vm.kill()

    def refresh(self) -> None:
        log.error("NEVER FUCKING DO THIS")
        return
        self.list_store.remove_all()
        for vm in get_saved_vms():
            self.list_store.append(vm)


def get_saved_vms() -> list[VM]:
    vm_list = []
    log.info("=====CREATING NEW VM OBJ====")
    try:
        # Execute `clan flakes add <path>` to democlan for this to work
        for entry in list_history():
            if entry.flake.icon is None:
                icon = assets.loc / "placeholder.jpeg"
            else:
                icon = entry.flake.icon

            base = VM(
                icon=Path(icon),
                data=entry,
            )
            vm_list.append(base)
    except ClanError as e:
        show_error_dialog(e)

    return vm_list
