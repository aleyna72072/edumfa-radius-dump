import base64
import json
import os

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.wait_strategies import LogMessageWaitStrategy
from testcontainers.postgres import PostgresContainer

OTPKEY = "3132333435363738393031323334353637383930"
VALID_OTP_VALUES = [
    "755224",
    "287082",
    "359152",
    "969429",
    "338314",
    "254676",
    "287922",
    "162583",
    "399871",
    "520489",
]
DB_CONTAINER_NAME = "edumfa-radius-test-postgres"

postgres = PostgresContainer(
    "postgres:17-alpine", name=DB_CONTAINER_NAME
)
edumfa = DockerContainer("ghcr.io/edumfa/edumfa:v2.9.3")
radius_image = DockerImage(path="../").build()
radius = DockerContainer(str(radius_image))


def bashify_command(cmd: str) -> str:
    """The nesting levels of the commands were unreadable. Take a command and
    turn it into base64. Then create a string, which calls bash to decode it and
    pipe it into bash.
    Yes, this is an ugly hack.

    :param cmd: The command to base64 encode.
    :return: The bash command to execute the cmd.
    """
    cmd_b64 = base64.b64encode(cmd.encode("utf-8")).decode()
    return f"bash -c \"echo -n {cmd_b64} | base64 -d | bash -s\""


@pytest.fixture(scope="module", autouse=True)
def remove_built_image(request):
    def _remove_built_image():
        radius_image.remove()
    request.addfinalizer(_remove_built_image)

@pytest.fixture(scope="function", autouse=True)
def setup(request):
    network = Network()
    network.create()
    postgres.with_network(network)
    edumfa.with_network(network)
    postgres.start()
    # wait_for_logs(postgres, "database system is ready to accept connections") # is this necessary?
    edumfa_env = {
        "DB_DATABASE": postgres.dbname,
        "DB_DRIVER": "postgresql+psycopg2",
        "DB_HOSTNAME": f"{DB_CONTAINER_NAME}:5432",
        "DB_PASSWORD": postgres.password,
        "DB_USER": postgres.username,
        "EDUMFA_PEPPER": "46685d2555dc23910921cca2a4f2de0a2d021405fd5461b4",
        "SECRET_KEY": "8a155906a8a8d30ccf2980099faaa3e904f5b8bb75862c73",
    }
    edumfa.with_envs(**edumfa_env)
    edumfa.waiting_for(LogMessageWaitStrategy(r".*Listening at: http://0.0.0.0:8000.*"))
    edumfa.start()
    # add resolver and realm
    edumfa.exec("edumfa-manage -q resolver create_internal testresolver")
    edumfa.exec("edumfa-manage -q realm create testrealm testresolver")
    # add user1 to testresolver
    add_user_cmd = 'echo \'from edumfa.lib.user import create_user; create_user("testresolver", {"username":"user1","email":"user1@user1.local"}, password="user1")\' | edumfa-manage shell'
    add_user_cmd = bashify_command(add_user_cmd)
    edumfa.exec(add_user_cmd)
    # give a token with OTPKEY to user1
    add_token_cmd = f'echo \'from edumfa.lib.user import User; from edumfa.lib.token import init_token; user = User("user1",realm="testrealm"); init_token({{"type": "hotp","otpkey": "{OTPKEY}"}}, user=user)\' | edumfa-manage shell'
    add_token_cmd = bashify_command(add_token_cmd)
    edumfa.exec(add_token_cmd)

    def remove_container():
        radius.stop()
        edumfa.stop()
        postgres.stop()
        network.remove()

    request.addfinalizer(remove_container)


def test_auth():
    # Make sure direct auth via eduMFA's API is working.
    response = edumfa.exec(
        f"curl -s 'http://localhost:8000/validate/check?user=user1&pass={VALID_OTP_VALUES[0]}'"
    ).output
    response = json.loads(response)
    assert response["result"]["authentication"] == "ACCEPT"

    # TODO: add radius container  
    # https://testcontainers-python.readthedocs.io/en/latest/core/README.html
    # DockerImage
    #breakpoint()
