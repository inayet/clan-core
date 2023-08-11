import argparse
import json
import subprocess
from typing import Optional

from ..nix import nix_shell


def ssh(
    host: str,
    user: str = "root",
    password: Optional[str] = None,
    ssh_args: list[str] = [],
) -> None:
    packages = ["tor", "openssh"]
    password_args = []
    if password:
        packages.append("sshpass")
        password_args = [
            "sshpass",
            "-p",
            password,
        ]
    _ssh_args = ssh_args + [
        "ssh",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "StrictHostKeyChecking=no",
        f"{user}@{host}",
    ]
    cmd = nix_shell(packages, ["torify"] + password_args + _ssh_args)
    subprocess.run(cmd)


def qrcode_scan(pictureFile: str) -> str:
    return (
        subprocess.run(
            nix_shell(
                ["zbar"],
                [
                    "zbarimg",
                    "--quiet",
                    "--raw",
                    pictureFile,
                ],
            ),
            stdout=subprocess.PIPE,
            check=True,
        )
        .stdout.decode()
        .strip()
    )


def main(args: argparse.Namespace) -> None:
    if args.json:
        with open(args.json) as file:
            ssh_data = json.load(file)
        ssh(host=ssh_data["address"], password=ssh_data["password"])
    elif args.png:
        ssh_data = json.loads(qrcode_scan(args.png))
        ssh(host=ssh_data["address"], password=ssh_data["password"])


def register_parser(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-j",
        "--json",
        help="specify the json file for ssh data (generated by starting the clan installer)",
    )
    group.add_argument(
        "-P",
        "--png",
        help="specify the json file for ssh data as the qrcode image (generated by starting the clan installer)",
    )
    # TODO pass all args we don't parse into ssh_args, currently it fails if arg starts with -
    parser.add_argument("ssh_args", nargs="*", default=[])
    parser.set_defaults(func=main)