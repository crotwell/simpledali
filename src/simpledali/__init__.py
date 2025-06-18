__version__ = "0.8.3"

"""
Datalink in pure python.

Read the docs at https://simpledali.readthedocs.io/en/latest/

Datalink is a protocol for near-realtime transfer of seismic data, usually in
miniseed, but has flexibility to carry any payload such as JSON. The Protocol
is defined at
https://earthscope.github.io/libdali/datalink-protocol.html
"""

from .abstractdali import (
    DataLink,
    DLPROTO_1_0,
    DLPROTO_1_1,
)
from .dalipacket import (
    DaliPacket,
    DaliResponse,
    DaliException,
    DaliClosed,
    nslcToStreamId,
    fdsnSourceIdToStreamId,
    JSON_TYPE,
    BZ2_JSON_TYPE,
    MSEED_TYPE,
    MSEED3_TYPE,
)
from .jsonencoder import JsonEncoder
from .util import datetimeToHPTime, hptimeToDatetime, utcnowWithTz, encodeAuthToken
from .socketdali import SocketDataLink
from .websocketdali import WebSocketDataLink
from .dali2jsonl import Dali2Jsonl

__all__ = [
    "DataLink",
    "DaliResponse",
    "DaliPacket",
    "DaliException",
    "nslcToStreamId",
    "fdsnSourceIdToStreamId",
    "JSON_TYPE",
    "BZ2_JSON_TYPE",
    "MSEED_TYPE",
    "MSEED3_TYPE",
    "DLPROTO_1_0",
    "DLPROTO_1_1",
    "Dali2Jsonl",
    "datetimeToHPTime",
    "hptimeToDatetime",
    "JsonEncoder",
    "utcnowWithTz",
    "encodeAuthToken",
    "SocketDataLink",
    "WebSocketDataLink",
]
