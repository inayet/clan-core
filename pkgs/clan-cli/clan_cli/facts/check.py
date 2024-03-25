import argparse
import importlib
import logging

from ..machines.machines import Machine

log = logging.getLogger(__name__)


def check_secrets(machine: Machine, service: None | str = None) -> bool:
    secret_facts_module = importlib.import_module(machine.secret_facts_module)
    secret_facts_store = secret_facts_module.SecretStore(machine=machine)
    public_facts_module = importlib.import_module(machine.public_facts_module)
    public_facts_store = public_facts_module.FactStore(machine=machine)

    missing_secret_facts = []
    missing_public_facts = []
    if service:
        services = [service]
    else:
        services = list(machine.secrets_data.keys())
    for service in services:
        for secret_fact in machine.secrets_data[service]["secrets"]:
            if isinstance(secret_fact, str):
                secret_name = secret_fact
            else:
                secret_name = secret_fact["name"]
            if not secret_facts_store.exists(service, secret_name):
                log.info(
                    f"Secret fact '{secret_fact}' for service {service} is missing."
                )
                missing_secret_facts.append((service, secret_name))

        for public_fact in machine.secrets_data[service]["facts"]:
            if not public_facts_store.exists(service, public_fact):
                log.info(
                    f"Public fact '{public_fact}' for service {service} is missing."
                )
                missing_public_facts.append((service, public_fact))

    log.debug(f"missing_secret_facts: {missing_secret_facts}")
    log.debug(f"missing_public_facts: {missing_public_facts}")
    if missing_secret_facts or missing_public_facts:
        return False
    return True


def check_command(args: argparse.Namespace) -> None:
    machine = Machine(
        name=args.machine,
        flake=args.flake,
    )
    check_secrets(machine, service=args.service)


def register_check_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "machine",
        help="The machine to check secrets for",
    )
    parser.add_argument(
        "--service",
        help="the service to check",
    )
    parser.set_defaults(func=check_command)
