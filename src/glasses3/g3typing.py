from logging import Logger, LoggerAdapter
from typing import TYPE_CHECKING, Any, Dict, List, NewType, Union

if TYPE_CHECKING:
    LoggerLike = Union[Logger, LoggerAdapter[Any]]
else:
    LoggerLike = Union[Logger, LoggerAdapter]
MessageId = NewType("MessageId", int)
URI = NewType("URI", str)
JSONObject = Union[int, str, bool, Dict[str, "JSONObject"], List["JSONObject"], None]
JSONDict = Dict[str, JSONObject]
SignalType = NewType("SignalType", str)
SignalId = NewType("SignalId", str)
SignalBody = NewType("SignalBody", List[JSONObject])
SubscriptionId = NewType("SubscriptionId", int)
