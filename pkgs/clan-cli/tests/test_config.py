import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from clan_cli import config

example_schema = f"{Path(config.__file__).parent}/jsonschema/example-schema.json"


# use pytest.parametrize
@pytest.mark.parametrize(
    "argv,expected",
    [
        (["name", "DavHau"], {"name": "DavHau"}),
        (
            ["kernelModules", "foo", "bar", "baz"],
            {"kernelModules": ["foo", "bar", "baz"]},
        ),
        (["services.opt", "test"], {"services": {"opt": "test"}}),
        (["userIds.DavHau", "42"], {"userIds": {"DavHau": 42}}),
    ],
)
def test_set_some_option(
    argv: list[str],
    expected: dict[str, Any],
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # monkeypatch sys.argv
    monkeypatch.setattr(sys, "argv", [""] + argv)
    parser = argparse.ArgumentParser()
    config.register_parser(parser=parser, file=Path(example_schema))
    args = parser.parse_args()
    args.func(args)
    captured = capsys.readouterr()
    print(captured.out)
    json_out = json.loads(captured.out)
    assert json_out == expected


def test_walk_jsonschema_all_types() -> None:
    schema = dict(
        type="object",
        properties=dict(
            array=dict(
                type="array",
                items=dict(
                    type="string",
                ),
            ),
            boolean=dict(type="boolean"),
            integer=dict(type="integer"),
            number=dict(type="number"),
            string=dict(type="string"),
        ),
    )
    expected = {
        "array": list[str],
        "boolean": bool,
        "integer": int,
        "number": float,
        "string": str,
    }
    assert config.options_types_from_schema(schema) == expected


def test_walk_jsonschema_nested() -> None:
    schema = dict(
        type="object",
        properties=dict(
            name=dict(
                type="object",
                properties=dict(
                    first=dict(type="string"),
                    last=dict(type="string"),
                ),
            ),
            age=dict(type="integer"),
        ),
    )
    expected = {
        "age": int,
        "name.first": str,
        "name.last": str,
    }
    assert config.options_types_from_schema(schema) == expected


# test walk_jsonschema with dynamic attributes (e.g. "additionalProperties")
def test_walk_jsonschema_dynamic_attrs() -> None:
    schema = dict(
        type="object",
        properties=dict(
            age=dict(type="integer"),
            users=dict(
                type="object",
                additionalProperties=dict(type="string"),
            ),
        ),
    )
    expected = {
        "age": int,
        "users.<name>": str,  # <name> is a placeholder for any string
    }
    assert config.options_types_from_schema(schema) == expected