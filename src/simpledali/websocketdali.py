
import websockets

from .abstractdali import DataLink, QUERY_MODE, STREAM_MODE, DLPROTO_1_0
from .dalipacket import DaliPacket, DaliResponse, DaliException, DaliClosed

class WebSocketDataLink(DataLink):
    """
    A DataLink over a websocket.

    Websockets must first connect as HTTP before upgrading to web socket.

    This uses a port number often specified in ringservers's conf as a
    ListenPort as long as it includes all or HTTP as the type.
    """
    def __init__(self, uri, packet_size=-1, dlproto=DLPROTO_1_0, verbose=False, ping_interval=None):
        super().__init__(packet_size=packet_size, dlproto=dlproto, verbose=verbose)
        self.uri = uri
        self.ws = None
        self.ping_interval = ping_interval

    async def createDaliConnection(self):
        await self.close()
        if self.verbose:
            print(f"connecting {self.uri}")
        self.ws = await websockets.connect(self.uri, ping_interval=self.ping_interval)
        if self.verbose:
            print(f"Websocket connected to {self.uri}")

    async def send(self, header, data):
        if self.isClosed():
            self._force_close()
            raise DaliClosed("Connection is closed")
        try:
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
            out = await self.ws.send(bytes(sendBytes))
            self.updateMode(header)
            return out
        except:
            await self.close()
            raise

    async def parseResponse(self):
        try:
            if self.isClosed():
                raise DaliClosed("Connection is closed")
            response = await self.ws.recv()
            # pre header
            # D ==> 68, L ==> 76
            if response[0] == 68 and response[1] == 76:
                hSize = response[2]
            else:
                await self.close()
                raise DaliException("did not receive DL from read " \
                                    f"{response[0]:d}{response[1]:d}{response[2]:d}")
            h = response[3 : hSize + 3]
            header = h.decode("utf-8")
            packettype = None
            value = None
            message = None
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
        except websockets.exceptions.ConnectionClosedError as e:
            # ringserver v4 doesn't gracefully close connections
            logging.warning("Server did not gracefully close websocket: ", exc_info=e)
            self._force_close()
            raise DaliClosed("Connection is closed") from e
        except websockets.exceptions.ConnectionClosed as e:
            self._force_close()
            raise DaliClosed("Connection is closed") from e
        except:
            await self.close()
            raise

    def isClosed(self):
        ans = self.ws is None or self.ws.state != websockets.protocol.State.OPEN
        if ans:
            # is socket is closed, make sure other state is updated
            self._force_close()
        return ans

    async def close(self):
        if self.ws is not None:
            await self.ws.close()
        self._force_close()

    def _force_close(self):
        """
        Unset websocket and reset mode. This should be not be called, prefer
        close() as it does the websocket close handshake.
        """
        self.ws = None
        self.__mode = QUERY_MODE
