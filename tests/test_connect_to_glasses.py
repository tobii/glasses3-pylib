import os

import pytest

from glasses3 import connect_to_glasses
from glasses3.streams import DEFAULT_RTPS_LIVE_PATH, DEFAULT_RTSP_PORT
from glasses3.zeroconf import DEFAULT_WEBSOCKET_PATH, G3ServiceDiscovery


@pytest.fixture(scope="module")
def g3_hostname() -> str:
    return os.environ["G3_HOSTNAME"]


async def test_connect_with_hostname_using_zeroconf_and_ip(g3_hostname: str):
    async with connect_to_glasses.with_hostname(
        g3_hostname, using_zeroconf=True, using_ip=True
    ) as g3:
        serial = await g3.system.get_recording_unit_serial()
        assert type(serial) is str


async def test_connect_with_service_using_ip(g3_hostname: str):
    g3_service = await G3ServiceDiscovery.request_service(g3_hostname)
    async with connect_to_glasses.with_service(g3_service, using_ip=True) as g3:
        serial = await g3.system.get_recording_unit_serial()
        assert type(serial) is str


async def test_connect_with_service_using_hostname(g3_hostname: str):
    g3_service = await G3ServiceDiscovery.request_service(g3_hostname)
    async with connect_to_glasses.with_service(g3_service, using_ip=False) as g3:
        serial = await g3.system.get_recording_unit_serial()
        assert type(serial) is str


async def test_connect_with_hostname_using_zeroconf_and_hostname(g3_hostname: str):
    async with connect_to_glasses.with_hostname(
        g3_hostname, using_zeroconf=True, using_ip=False
    ) as g3:
        serial = await g3.system.get_recording_unit_serial()
        assert type(serial) is str


async def test_connect_with_hostname_no_zeroconf(g3_hostname: str):
    async with connect_to_glasses.with_hostname(
        g3_hostname, using_zeroconf=False
    ) as g3:
        serial = await g3.system.get_recording_unit_serial()
        assert type(serial) is str


async def test_connect_with_urls(g3_hostname: str):
    async with connect_to_glasses.with_url(
        f"ws://{g3_hostname}{DEFAULT_WEBSOCKET_PATH}",
        f"rtsp://{g3_hostname}:{DEFAULT_RTSP_PORT}{DEFAULT_RTPS_LIVE_PATH}",
    ) as g3:
        serial = await g3.system.get_recording_unit_serial()
        assert type(serial) is str
