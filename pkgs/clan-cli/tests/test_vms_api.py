import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from api import TestClient
from cli import Cli
from httpx import SyncByteStream

if TYPE_CHECKING:
    from age_keys import KeyPair


@pytest.mark.impure
def test_inspect(api: TestClient, test_flake_with_core: Path) -> None:
    response = api.post(
        "/api/vms/inspect",
        json=dict(flake_url=str(test_flake_with_core), flake_attr="vm1"),
    )
    assert response.status_code == 200, "Failed to inspect vm"
    config = response.json()["config"]
    assert config.get("flake_attr") == "vm1"
    assert config.get("cores") == 1
    assert config.get("memory_size") == 1024
    assert config.get("graphics") is False


def test_incorrect_uuid(api: TestClient) -> None:
    uuid_endpoints = [
        "/api/vms/{}/status",
        "/api/vms/{}/logs",
    ]

    for endpoint in uuid_endpoints:
        response = api.get(endpoint.format("1234"))
        assert response.status_code == 422, "Failed to get vm status"


@pytest.mark.skipif(not os.path.exists("/dev/kvm"), reason="Requires KVM")
@pytest.mark.impure
def test_create(
    api: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    test_flake_with_core: Path,
    age_keys: list["KeyPair"],
) -> None:
    monkeypatch.chdir(test_flake_with_core)
    monkeypatch.setenv("SOPS_AGE_KEY", age_keys[0].privkey)
    cli = Cli()
    cli.run(["secrets", "users", "add", "user1", age_keys[0].pubkey])
    print(f"flake_url: {test_flake_with_core} ")
    response = api.post(
        "/api/vms/create",
        json=dict(
            flake_url=str(test_flake_with_core),
            flake_attr="vm1",
            cores=1,
            memory_size=1024,
            graphics=False,
        ),
    )
    assert response.status_code == 200, "Failed to create vm"

    uuid = response.json()["uuid"]
    assert len(uuid) == 36
    assert uuid.count("-") == 4

    response = api.get(f"/api/vms/{uuid}/status")
    assert response.status_code == 200, "Failed to get vm status"

    response = api.get(f"/api/vms/{uuid}/logs")
    print("=========VM LOGS==========")
    assert isinstance(response.stream, SyncByteStream)
    for line in response.stream:
        print(line.decode("utf-8"))
    print("=========END LOGS==========")
    assert response.status_code == 200, "Failed to get vm logs"

    response = api.get(f"/api/vms/{uuid}/status")
    assert response.status_code == 200, "Failed to get vm status"
    data = response.json()
    assert (
        data["status"] == "FINISHED"
    ), f"Expected to be finished, but got {data['status']} ({data})"
