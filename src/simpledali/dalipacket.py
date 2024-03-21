
from simplemseed import FDSNSourceId, FDSN_PREFIX

JSON_TYPE = "JSON"
BZ2_JSON_TYPE = "BZJSON"
MSEED_TYPE = "MSEED"
MSEED3_TYPE = "MSEED3"

class DaliResponse:
    def __init__(self, packettype, value, message):
        self.type = packettype
        self.value = value
        self.message = message

    def __str__(self):
        return f"type={self.type} value={self.value} message={self.message}"


class DaliPacket:
    def __init__(
        self,
        packettype,
        streamId,
        packetId,
        packetTime,
        dataStartTime,
        dataEndTime,
        dSize,
        data,
    ):
        self.type = packettype
        self.streamId = streamId
        self.packetId = packetId
        self.packetTime = packetTime
        self.dataStartTime = dataStartTime
        self.dataEndTime = dataEndTime
        self.dSize = dSize
        self.data = data
    def streamIdChannel(self):
        return self.streamId.split("/")[0]
    def streamIdType(self):
        s = self.streamId.split("/")
        if len(s)>1:
            return s[1]
        return ""
    def __str__(self):
        return f"{self.type} {self.streamId} {self.packetId} {self.packetTime} {self.dataStartTime} {self.dataEndTime} {self.dSize}"

class DaliException(Exception):
    def __init__(self, message, daliResponse=None):
        super().__init__(message, daliResponse)
        self.message = message
        self.daliResponse = daliResponse
    def __str__(self):
        if self.daliResponse is not None:
            return f"Dali {self.daliResponse.type}: {self.daliResponse.message}"
        return self.message

def nslcToStreamId(net: str, sta: str, loc: str, chan: str, packettype: str) -> str:
    return f"{net}_{sta}_{loc}_{chan}/{packettype}"

def fdsnSourceIdToStreamId(sourceId: 'FDSNSourceId', packettype: str) -> str:
    sid = str(sourceId)
    if sid.startswith(FDSN_PREFIX):
        sid = sid[len(FDSN_PREFIX):]
    return f"{sid}/{packettype}"
