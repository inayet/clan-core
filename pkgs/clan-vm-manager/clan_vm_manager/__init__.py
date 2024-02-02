import argparse
import logging

from clan_cli.clan_uri import ClanURI
from clan_cli.custom_logger import setup_logging

from clan_vm_manager.models.interfaces import ClanConfig

from .app import MainApplication

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="clan-vm-manager")

    parser.add_argument("--debug", action="store_true", help="enable debug mode")

    # Add join subcommand
    subparser = parser.add_subparsers(
        title="command",
        description="command to execute",
        help="the command to execute",
    )
    register_join_parser(subparser.add_parser("join", help="join a clan"))

    register_overview_parser(subparser.add_parser("overview", help="overview screen"))

    # Executed when no command is given
    parser.set_defaults(func=show_overview)
    args = parser.parse_args()

    if args.debug:
        setup_logging("DEBUG", root_log_name=__name__.split(".")[0])
    else:
        setup_logging("INFO", root_log_name=__name__.split(".")[0])

    log.debug("Debug logging enabled")
    log.info("Info logging enabled")

    args.func(args)


def show_join(args: argparse.Namespace) -> None:
    app = MainApplication(
        config=ClanConfig(url=args.clan_uri, initial_view="list"),
    )
    return app.run()


def register_join_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("clan_uri", type=ClanURI, help="clan URI to join")
    parser.set_defaults(func=show_join)


def show_overview(args: argparse.Namespace) -> None:
    app = MainApplication(
        config=ClanConfig(url=None, initial_view="list"),
    )
    return app.run()


def register_overview_parser(parser: argparse.ArgumentParser) -> None:
    parser.set_defaults(func=show_overview)
