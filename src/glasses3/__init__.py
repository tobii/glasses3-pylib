"""
.. include:: ../../README.md

g3pylib is a python wrapper around the Glasses3 web API which lets you control Glasses3 devices.

## API Endpoints
All endpoints in the `glasses3` module corresponding to an endpoint in the Glasses3 web API are undocumented and placed first in each module.
The following naming convention is used to translate web API endpoint names to `glasses3` API endpoint names:
 - Properties: example_property -> get_example_property/set_example_property
 - Actions: example_action -> example_action
 - Signals: example_signal -> subscribe_to_example_signal

The web API endpoints can be browsed in the Glasses3 Example web client accessed via http://*your-g3-address*.

## Useful information
In any code examples, `g3` will be a connected instance of `Glasses3`.

The default hostname of a Glasses3 device is its serial number.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Any, AsyncIterator, Generator, Optional, Type, cast

import glasses3.websocket
from glasses3._utils import APIComponent
from glasses3.calibrate import Calibrate
from glasses3.g3typing import URI, LoggerLike
from glasses3.recorder import Recorder
from glasses3.recordings import Recordings
from glasses3.rudimentary import Rudimentary
from glasses3.settings import Settings
from glasses3.streams import Streams
from glasses3.system import System
from glasses3.websocket import G3WebSocketClientProtocol
from glasses3.zeroconf import G3Service, G3ServiceDiscovery

__version__ = "0.1.0-alpha"


class Glasses3(APIComponent):
    """
    Represents a Glasses3 device.

    Holds the API components and a WebSocket connection to a Glasses3 device.
    The `stream_rtsp` context can be used for live stream functionality.

    For the recommended way to create a connected instance of Glasses3, see `connect_to_glasses`.
    """

    def __init__(
        self,
        connection: G3WebSocketClientProtocol,
        rtsp_url: str,
        logger: Optional[LoggerLike] = None,
    ) -> None:
        self.logger: LoggerLike = (
            logging.getLogger(__name__) if logger is None else logger
        )
        self._rtsp_url = rtsp_url
        self._connection: G3WebSocketClientProtocol = connection
        self._recorder: Optional[Recorder] = None
        self._recordings: Optional[Recordings] = None
        self._rudimentary: Optional[Rudimentary] = None
        self._system: Optional[System] = None
        self._calibrate: Optional[Calibrate] = None
        self._settings: Optional[Settings] = None

    @property
    def calibrate(self) -> Calibrate:
        if self._calibrate is None:
            self._calibrate = Calibrate(self._connection, URI("/calibrate"))
        return self._calibrate

    @property
    def recorder(self) -> Recorder:
        if self._recorder is None:
            self._recorder = Recorder(self._connection, URI("/recorder"))
        return self._recorder

    @property
    def recordings(self) -> Recordings:
        if self._recordings is None:
            self._recordings = Recordings(self._connection, URI("/recordings"))
        return self._recordings

    @property
    def rudimentary(self) -> Rudimentary:
        if self._rudimentary is None:
            self._rudimentary = Rudimentary(self._connection, URI("/rudimentary"))
        return self._rudimentary

    @property
    def system(self) -> System:
        if self._system is None:
            self._system = System(self._connection, URI("/system"))
        return self._system

    @property
    def settings(self) -> Settings:
        if self._settings is None:
            self._settings = Settings(self._connection, URI("/settings"))
        return self._settings

    @property
    def rtsp_url(self) -> str:
        """The RTSP URL used for live stream."""
        return self._rtsp_url

    @asynccontextmanager
    async def stream_rtsp(
        self,
        scene_camera: bool = True,
        audio: bool = False,
        eye_cameras: bool = False,
        gaze: bool = False,
        sync: bool = False,
        imu: bool = False,
        events: bool = False,
    ) -> AsyncIterator[Streams]:
        """Set up an RTSP connection in the form of a Streams object with the Stream properties indicated by the arguments.

        The Stream objects can be used to demux/decode their stream. For example, `stream_rtsp()` can be used as follows:
        ```
        async with connect_to_glasses(g3_hostname) as g3:
            async with g3.stream_rtsp() as streams:
                async with streams.scene_camera.decode() as decoded_stream:
                    for _ in range(500):
                        frame = await decoded_stream.get()
                        image = frame.to_ndarray(format="bgr24")
                        cv2.imshow("Video", image)
                        cv2.waitKey(1)
        ```

        *Beta version note:* Only the scene_camera, eye_camera and gaze attributes are implemented so far.
        """
        async with Streams.connect(
            self.rtsp_url,
            scene_camera=scene_camera,
            audio=audio,
            eye_cameras=eye_cameras,
            gaze=gaze,
            sync=sync,
            imu=imu,
            events=events,
        ) as streams:
            await streams.play()
            yield streams

    async def close(self) -> None:
        """Close down the underlying websocket connection to the Glasses3 device."""
        await self._connection.close()


class connect_to_glasses:
    def __init__(
        self,
        g3_hostname: Optional[str] = None,
        service: Optional[G3Service] = None,
    ) -> None:
        self.g3_hostname = g3_hostname
        self.service = service

    def __await__(self) -> Generator[Any, None, Glasses3]:
        return self.__await_impl__().__await__()

    async def __await_impl__(self) -> Glasses3:
        if self.g3_hostname is None and self.service is None:
            async with G3ServiceDiscovery.listen() as service_discovery:
                self.service = await service_discovery.wait_for_single_service(
                    service_discovery.events
                )
            self.g3_hostname = self.service.hostname
        elif self.service is None and self.g3_hostname is not None:
            self.service = await G3ServiceDiscovery.request_service(self.g3_hostname)
        elif self.g3_hostname is None and self.service is not None:
            self.g3_hostname = self.service.hostname
        else:
            raise ValueError

        connection = await glasses3.websocket.connect(self.g3_hostname)
        connection = cast(G3WebSocketClientProtocol, connection)
        connection.start_receiver_task()
        self.connection = connection
        return Glasses3(connection, self.service.rtsp_url)

    async def __aenter__(self) -> Glasses3:
        return await self

    async def __aexit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.connection.close()
