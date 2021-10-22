
class DaliResponse:

    def __init__(self, type, value, message):
        self.type = type
        self.value=value
        self.message = message

    def __str__(self):
        return "type={} value={} message={}".format(self.type, self.value, self.message)

class DaliPacket:
    def __init__(self,
                 type,
                 streamId,
                 packetId,
                 packetTime,
                 dataStartTime,
                 dataEndTime,
                 dSize,
                 data):
        self.type = type
        self.streamId = streamId
        self.packetId = packetId
        self.packetTime = packetTime
        self.dataStartTime = dataStartTime
        self.dataEndTime = dataEndTime
        self.dSize = dSize
        self.data = data

    def __str__(self):
        return "{} {} {} {} {} {} {}".format(self.type, self.streamId, self.packetId, self.packetTime, self.dataStartTime, self.dataEndTime, self.dSize)
