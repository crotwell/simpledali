class DaliResponse:
    def __init__(self, type, value, message):
        self.type = type
        self.value = value
        self.message = message

    def __str__(self):
        return "type={} value={} message={}".format(self.type, self.value, self.message)


class DaliPacket:
    def __init__(
        self,
        type,
        streamId,
        packetId,
        packetTime,
        dataStartTime,
        dataEndTime,
        dSize,
        data,
    ):
        self.type = type
        self.streamId = streamId
        self.packetId = packetId
        self.packetTime = packetTime
        self.dataStartTime = dataStartTime
        self.dataEndTime = dataEndTime
        self.dSize = dSize
        self.data = data

    def __str__(self):
        return "{} {} {} {} {} {} {}".format(
            self.type,
            self.streamId,
            self.packetId,
            self.packetTime,
            self.dataStartTime,
            self.dataEndTime,
            self.dSize,
        )

class DaliException(Exception):
    def __init__(self, message, daliResponse=None):
        super().__init__(message, daliResponse)
        self.message = message
        self.daliResponse = daliResponse
    def __str__(self):
        if self.daliResponse is not None:
            return f"Dali {self.daliResponse.type}: {self.daliResponse.message}"
        else:
            return super.__str__()
