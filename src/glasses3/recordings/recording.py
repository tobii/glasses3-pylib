from datetime import datetime, timedelta
from typing import List, Optional, cast

from glasses3.g3typing import URI
from glasses3.utils import APIComponent, EndpointKind
from glasses3.websocket import G3WebSocketClientProtocol


class Recording(APIComponent):
    def __init__(
        self, connection: G3WebSocketClientProtocol, api_base_uri: URI, uuid: str
    ):
        self._connection = connection
        self._uuid = uuid
        super().__init__(URI(f"{api_base_uri}/{uuid}"))

    @property
    def uuid(self) -> str:
        return self._uuid

    async def get_created(self) -> datetime:
        created = cast(
            str,
            await self._connection.require_get(
                self.generate_endpoint_uri(EndpointKind.PROPERTY, "created")
            ),
        )
        return datetime.fromisoformat(created.strip("Z"))

    async def get_duration(self) -> Optional[timedelta]:
        duration = cast(
            float,
            await self._connection.require_get(
                self.generate_endpoint_uri(EndpointKind.PROPERTY, "duration")
            ),
        )
        if duration == -1:
            return None
        return timedelta(seconds=duration)

    async def get_folder(self) -> str:
        return cast(
            str,
            await self._connection.require_get(
                self.generate_endpoint_uri(EndpointKind.PROPERTY, "folder")
            ),
        )

    async def get_gaze_overlay(self) -> bool:
        return cast(
            bool,
            await self._connection.require_get(
                self.generate_endpoint_uri(EndpointKind.PROPERTY, "gaze-overlay")
            ),
        )

    async def get_gaze_samples(self) -> Optional[int]:
        gaze_samples = cast(
            int,
            await self._connection.require_get(
                self.generate_endpoint_uri(EndpointKind.PROPERTY, "gaze-samples")
            ),
        )
        if gaze_samples == -1:
            return None
        return gaze_samples

    async def get_http_path(self) -> str:
        return cast(
            str,
            await self._connection.require_get(
                self.generate_endpoint_uri(EndpointKind.PROPERTY, "http-path")
            ),
        )

    async def get_name(self) -> str:
        return cast(
            str,
            await self._connection.require_get(
                self.generate_endpoint_uri(EndpointKind.PROPERTY, "name")
            ),
        )

    async def get_rtsp_path(self) -> str:
        return cast(
            str,
            await self._connection.require_get(
                self.generate_endpoint_uri(EndpointKind.PROPERTY, "rtsp-path")
            ),
        )

    async def get_timezone(self) -> str:
        return cast(
            str,
            await self._connection.require_get(
                self.generate_endpoint_uri(EndpointKind.PROPERTY, "timezone")
            ),
        )

    async def get_valid_gaze_samples(self) -> Optional[int]:
        valid_gaze_samples = cast(
            int,
            await self._connection.require_get(
                self.generate_endpoint_uri(EndpointKind.PROPERTY, "valid-gaze-samples")
            ),
        )
        if valid_gaze_samples == -1:
            return None
        return valid_gaze_samples

    async def get_visible_name(self) -> str:
        return cast(
            str,
            await self._connection.require_get(
                self.generate_endpoint_uri(EndpointKind.PROPERTY, "visible-name")
            ),
        )

    async def set_visible_name(self, value: str) -> bool:
        return cast(
            bool,
            await self._connection.require_post(
                self.generate_endpoint_uri(EndpointKind.PROPERTY, "visible-name"),
                body=value,
            ),
        )

    async def meta_insert(self, key: str, meta: Optional[str]) -> bool:
        return cast(
            bool,
            await self._connection.require_post(
                self.generate_endpoint_uri(EndpointKind.ACTION, "meta-insert"),
                body=[key, meta],
            ),
        )

    async def meta_keys(self) -> List[str]:
        return cast(
            List[str],
            await self._connection.require_post(
                self.generate_endpoint_uri(EndpointKind.ACTION, "meta-keys")
            ),
        )

    async def meta_lookup(self, key: str) -> str:
        return cast(
            str,
            await self._connection.require_post(
                self.generate_endpoint_uri(EndpointKind.ACTION, "meta-lookup"),
                body=[key],
            ),
        )

    async def move(self, folder: str) -> bool:
        return cast(
            bool,
            await self._connection.require_post(
                self.generate_endpoint_uri(EndpointKind.ACTION, "move"), body=[folder]
            ),
        )
