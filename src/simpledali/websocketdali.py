
import websockets

from .abstractdali import DataLink, QUERY_MODE, STREAM_MODE
from .dalipacket import DaliPacket, DaliResponse, DaliException

class WebSocketDataLink(DataLink):
    """
    A DataLink over a websocket.

    Websockets must first connect as HTTP before upgrading to web socket.

    This uses a port number often specified in ringservers's conf as a
    ListenPort as long as it includes all or HTTP as the type.
    """
    def __init__(self, uri, packet_size=-1, verbose=False, ping_interval=None):
        super().__init__(packet_size=packet_size, verbose=verbose)
        self.uri = uri
        self.ws = None
        self.ping_interval = ping_interval

    async def createDaliConnection(self):
        await self.close()
        if self.verbose:
            print(f"connect {self.uri}")
        self.ws = await websockets.connect(self.uri, ping_interval=self.ping_interval)
        if self.verbose:
            print(f"Websocket connect to {self.uri}")

    async def send(self, header, data):
        try:
            if self.isClosed():
                if header == "ENDSTREAM":
                    # no need to reopen conn just to endstream
                    self.updateMode(header)
                    return
                await self.reconnect()
            h = header.encode("UTF-8")
            if len(h) > 255:
                raise DaliException(f"header lengh must be <= 255, {len(h)}")
            pre = "DL"
            sendBytesLen = 3 + len(h)
            if data:
                sendBytesLen += len(data)
            sendBytes = bytearray(sendBytesLen)
            sendBytes[0:2] = pre.encode("UTF-8")
            lenByte = len(h).to_bytes(1, byteorder="big", signed=False)
            sendBytes[2] = lenByte[0]
            sendBytes[3 : len(h) + 3] = h
            if data:
                sendBytes[len(h) + 3 :] = data
                if self.verbose:
                    print(f"send data of size {len(data):d}")
            out = await self.ws.send(bytes(sendBytes))
            if self.verbose:
                print(f"sent {pre}{len(h)} {header}")
            self.updateMode(header)
            return out
        except:
            await self.close()
            raise

    async def parseResponse(self):
        try:
            if self.isClosed():
                raise DaliException("Connection is closed")
            response = await self.ws.recv()
            # pre header
            # D ==> 68, L ==> 76
            if response[0] == 68 and response[1] == 76:
                hSize = response[2]
            else:
                if self.verbose:
                    print(
                        f"did not receive DL from read pre {response[0]:d}{response[1]:d}{response[2]:d}"
                    )
                await self.close()
                raise DaliException("did not receive DL from read pre")
            h = response[3 : hSize + 3]
            header = h.decode("utf-8")
            packettype = None
            value = None
            message = None
            if self.verbose:
                print(f"parseRespone header: {h}")
            if header.startswith("PACKET "):
                s = header.split(" ")
                packettype = s[0]
                streamId = s[1]
                packetId = s[2]
                packetTime = s[3]
                dataStartTime = s[4]
                dataEndTime = s[5]
                dSize = int(s[6])
                data = response[hSize + 3 :]
                return DaliPacket(
                    packettype,
                    streamId,
                    packetId,
                    packetTime,
                    dataStartTime,
                    dataEndTime,
                    dSize,
                    data,
                )
            if header.startswith("ID "):
                s = header.split(" ")
                packettype = s[0]
                value = ""
                message = header[3:]
                return DaliResponse(packettype, value, message)
            if (
                header.startswith("INFO ")
                or header.startswith("OK ")
                or header.startswith("ERROR ")
            ):
                s = header.split(" ")
                packettype = s[0]
                value = s[1]
                dSize = int(s[2])
                m = response[hSize + 3 :]
                message = m.decode("utf-8")
                return DaliResponse(packettype, value, message)
            if header == "ENDSTREAM":
                packettype = header
                return DaliResponse(packettype, value, message)
            raise DaliException(
                f"Header does not start with INFO, ID, PACKET, ENDSTREAM, OK or ERROR: {header}",
            )
        except:
            await self.close()
            raise

    def isClosed(self):
        ans = self.ws is None or not self.ws.open
        if ans:
            # is socket is closed, make sure other state is updated
            self.ws = None
            self.__mode = QUERY_MODE
        return ans

    async def close(self):
        if self.ws is not None:
            await self.ws.close()
            self.ws = None
        self.__mode = QUERY_MODE
