import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from ..dirs import get_clan_flake_toplevel
from ..nix import nix_build, nix_config, nix_eval
from ..ssh import Host, parse_deployment_address


def build_machine_data(machine_name: str, clan_dir: Path) -> dict:
    config = nix_config()
    system = config["system"]

    outpath = subprocess.run(
        nix_build(
            [
                f'path:{clan_dir}#clanInternals.machines."{system}"."{machine_name}".config.system.clan.deployment.file'
            ]
        ),
        stdout=subprocess.PIPE,
        check=True,
        text=True,
    ).stdout.strip()
    return json.loads(Path(outpath).read_text())


class Machine:
    def __init__(
        self,
        name: str,
        clan_dir: Optional[Path] = None,
        machine_data: Optional[dict] = None,
    ) -> None:
        """
        Creates a Machine
        @name: the name of the machine
        @clan_dir: the directory of the clan, optional, if not set it will be determined from the current working directory
        @machine_json: can be optionally used to skip evaluation of the machine, location of the json file with machine data
        """
        self.name = name
        if clan_dir is None:
            self.clan_dir = get_clan_flake_toplevel()
        else:
            self.clan_dir = clan_dir

        if machine_data is None:
            self.machine_data = build_machine_data(name, self.clan_dir)
        else:
            self.machine_data = machine_data

        self.deployment_address = self.machine_data["deploymentAddress"]
        self.upload_secrets = self.machine_data["uploadSecrets"]
        self.generate_secrets = self.machine_data["generateSecrets"]
        self.secrets_upload_directory = self.machine_data["secretsUploadDirectory"]

    @property
    def host(self) -> Host:
        return parse_deployment_address(
            self.name, self.deployment_address, meta={"machine": self}
        )

    def run_upload_secrets(self, secrets_dir: Path) -> None:
        """
        Upload the secrets to the provided directory
        @secrets_dir: the directory to store the secrets in
        """
        env = os.environ.copy()
        env["CLAN_DIR"] = str(self.clan_dir)
        env["PYTHONPATH"] = str(
            ":".join(sys.path)
        )  # TODO do this in the clanCore module
        env["SECRETS_DIR"] = str(secrets_dir)
        subprocess.run(
            [self.upload_secrets],
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )

    def eval_nix(self, attr: str) -> str:
        """
        eval a nix attribute of the machine
        @attr: the attribute to get
        """
        output = subprocess.run(
            nix_eval([f"path:{self.clan_dir}#{attr}"]),
            stdout=subprocess.PIPE,
            check=True,
            text=True,
        ).stdout.strip()
        return output

    def build_nix(self, attr: str) -> Path:
        """
        build a nix attribute of the machine
        @attr: the attribute to get
        """
        outpath = subprocess.run(
            nix_build([f"path:{self.clan_dir}#{attr}"]),
            stdout=subprocess.PIPE,
            check=True,
            text=True,
        ).stdout.strip()
        return Path(outpath)