from .abstractdali import DataLink
from .dalipacket import DaliPacket, DaliResponse
import asyncio
import websockets


class WebSocketDataLink(DataLink):
    def __init__(self, uri, verbose=False, ping_interval=None):
        super(WebSocketDataLink, self).__init__(verbose)
        self.uri = uri
        self.ws = None
        self.ping_interval = ping_interval

    async def createDaliConnection(self):
        await self.close()
        if self.verbose: print(f"connect {self.uri}")
        self.ws = await websockets.connect(self.uri, ping_interval=self.ping_interval)
        if self.verbose:
            print("Websocket connect to {}".format(self.uri))

    async def send(self, header, data):
        try:
            if self.isClosed():
                 await self.reconnect()
            h = header.encode('UTF-8')
            if len(h) > 255:
                raise Exception("header lengh must be <= 255, {}".format(len(h)))
            pre = "DL"
            sendBytesLen = 3 + len(h)
            if(data):
                sendBytesLen += len(data)
            sendBytes = bytearray(sendBytesLen)
            sendBytes[0:2] = pre.encode('UTF-8')
            lenByte = len(h).to_bytes(1, byteorder='big', signed=False)
            sendBytes[2] = lenByte[0]
            sendBytes[3:len(h)+3] = h
            if(data):
                sendBytes[len(h)+3:] = data
                if self.verbose: print("send data of size {:d}".format(len(data)))
            out = await self.ws.send(bytes(sendBytes))
            if self.verbose: print("sent {}{} {}".format(pre, len(h), header))
            return out
        except:
            await self.close()
            raise

    async def parseResponse(self):
        try:
            if self.isClosed():
                 raise Exception("Connection is closed")
            response = await self.ws.recv()
            # pre header
            # D ==> 68, L ==> 76
            if response[0] == 68 and response[1] == 76:
                hSize = response[2]
            else:
                if self.verbose: print("did not receive DL from read pre {:d}{:d}{:d}".format(response[0],response[1],response[2]))
                await self.close()
                raise Exception("did not receive DL from read pre")
            h = response[3:hSize+3]
            header = h.decode("utf-8")
            type=None
            value=None
            message=None
            if self.verbose: print("parseRespone header: {}".format(h))
            if header.startswith("PACKET "):
                s = header.split(" ")
                type = s[0]
                streamId = s[1]
                packetId = s[2]
                packetTime = s[3]
                dataStartTime = s[4]
                dataEndTime = s[5]
                dSize = int(s[6])
                data = response[hSize+3:]
                return DaliPacket(type, streamId, packetId, packetTime, dataStartTime, dataEndTime, dSize, data)
            elif header.startswith("ID "):
                s = header.split(" ")
                type = s[0]
                value = ""
                message = header[3:]
                return DaliResponse(type, value, message)
            elif (header.startswith("INFO ") or header.startswith("OK ") or header.startswith("ERROR ")):
                s = header.split(" ")
                type = s[0]
                value = s[1]
                dSize = int(s[2])
                m = response[hSize+3:]
                message = m.decode("utf-8")
                return DaliResponse(type, value, message)
            elif header == "ENDSTREAM":
                return DaliResponse(header, value, message)
            else:
                raise Exception("Header does not start with INFO, ID, PACKET, OK or ERROR: {}".format(header))
            return DaliResponse(type, value, message)
        except:
            await self.close()
            raise

    def isClosed(self):
        return self.ws is None or not self.ws.open

    async def close(self):
        if self.ws is not None:
            await self.ws.close()
            self.ws = None
