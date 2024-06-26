import argparse
import importlib
import logging
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from ..cmd import Log, run
from ..facts.generate import generate_facts
from ..machines.machines import Machine
from ..nix import nix_shell

log = logging.getLogger(__name__)


def install_nixos(
    machine: Machine, kexec: str | None = None, debug: bool = False
) -> None:
    secret_facts_module = importlib.import_module(machine.secret_facts_module)
    log.info(f"installing {machine.name}")
    secret_facts_store = secret_facts_module.SecretStore(machine=machine)

    h = machine.target_host
    target_host = f"{h.user or 'root'}@{h.host}"
    log.info(f"target host: {target_host}")

    generate_facts(machine)

    with TemporaryDirectory() as tmpdir_:
        tmpdir = Path(tmpdir_)
        upload_dir_ = machine.secrets_upload_directory

        if upload_dir_.startswith("/"):
            upload_dir_ = upload_dir_[1:]
        upload_dir = tmpdir / upload_dir_
        upload_dir.mkdir(parents=True)
        secret_facts_store.upload(upload_dir)

        cmd = [
            "nixos-anywhere",
            "-f",
            f"{machine.flake}#{machine.name}",
            "--no-reboot",
            "--extra-files",
            str(tmpdir),
        ]
        if machine.target_host.port:
            cmd += ["--ssh-port", str(machine.target_host.port)]
        if kexec:
            cmd += ["--kexec", kexec]
        if debug:
            cmd.append("--debug")
        cmd.append(target_host)

        run(
            nix_shell(
                ["nixpkgs#nixos-anywhere"],
                cmd,
            ),
            log=Log.BOTH,
        )


@dataclass
class InstallOptions:
    flake: Path
    machine: str
    target_host: str
    kexec: str | None
    confirm: bool
    debug: bool


def install_command(args: argparse.Namespace) -> None:
    opts = InstallOptions(
        flake=args.flake,
        machine=args.machine,
        target_host=args.target_host,
        kexec=args.kexec,
        confirm=not args.yes,
        debug=args.debug,
    )
    machine = Machine(opts.machine, flake=opts.flake)
    machine.target_host_address = opts.target_host

    if opts.confirm:
        ask = input(f"Install {machine.name} to {opts.target_host}? [y/N] ")
        if ask != "y":
            return

    install_nixos(machine, kexec=opts.kexec, debug=opts.debug)


def register_install_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--kexec",
        type=str,
        help="use another kexec tarball to bootstrap NixOS",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="do not ask for confirmation",
        default=False,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="print debug information",
        default=False,
    )
    parser.add_argument(
        "machine",
        type=str,
        help="machine to install",
    )
    parser.add_argument(
        "target_host",
        type=str,
        help="ssh address to install to in the form of user@host:2222",
    )
    parser.set_defaults(func=install_command)
