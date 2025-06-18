import asyncio

from .abstractdali import DataLink, QUERY_MODE, DLPROTO_1_0
from .dalipacket import DaliPacket, DaliResponse, DaliException, DaliClosed

class SocketDataLink(DataLink):
    """
    A DataLink over a normal socket.

    This uses a port number often specified in ringservers's conf as a
    DataLinkPort, but can also be specified as a ListenPort as long as it
    includes all or DataLink as the type.
    """
    def __init__(self, host, port, packet_size=-1, dlproto=DLPROTO_1_0, verbose=False):
        super().__init__(packet_size=packet_size, dlproto=dlproto, verbose=verbose)
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def createDaliConnection(self):
        await self.close()
        if self.verbose:
            print(f"connecting {self.host}:{self.port}")
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def send(self, header, data):
        h = header.encode("UTF-8")
        pre = "DL"
        if self.isClosed():
            self._force_close()
            raise DaliClosed("Connection is closed")
        try:
            self.writer.write(pre.encode("UTF-8"))
            lenByte = len(h).to_bytes(1, byteorder="big", signed=False)
            self.writer.write(lenByte)
            self.writer.write(h)
            if data:
                self.writer.write(data)
            out = await self.writer.drain()
            self.updateMode(header)
            return out
        except:
            await self.close()
            raise

    async def parseResponse(self):
        try:
            if self.isClosed():
                raise DaliClosed("Connection is closed")
            pre = await self.reader.readexactly(3)
            # D ==> 68, L ==> 76
            if pre[0] == 68 and pre[1] == 76:
                hSize = pre[2]
            else:
                await self.close()
                raise DaliException(f"did not receive DL from read pre {pre[0]:d}{pre[1]:d}{pre[2]:d}")
            h = await self.reader.readexactly(hSize)
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
                data = await self.reader.readexactly(dSize)
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
                m = await self.reader.readexactly(dSize)
                message = m.decode("utf-8")
                return DaliResponse(packettype, value, message)
            if header == "ENDSTREAM":
                return DaliResponse(header, value, message)
            raise DaliException(
                f"Header does not start with INFO, ID, PACKET, ENDSTREAM, OK or ERROR: {header}"
            )
        except asyncio.exceptions.IncompleteReadError as e:
            self._force_close()
            raise DaliClosed("Connection is closed") from e
        except:
            await self.close()
            raise

    def isClosed(self):
        ans = self.writer is None or self.writer.is_closing() or \
            self.reader is None or self.reader.at_eof()
        if ans:
            # is socket is closed, make sure other state is updated
            self._force_close()
        return ans

    async def close(self):
        if self.writer is not None:
            try:
                self.writer.close()
            except:
                # oh well
                pass
        self._force_close()

    def _force_close(self):
        self.writer = None
        self.reader = None
        self.__mode = QUERY_MODE
