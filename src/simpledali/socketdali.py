from .abstractdali import DataLink, QUERY_MODE, STREAM_MODE
from .dalipacket import DaliPacket, DaliResponse
import asyncio


class SocketDataLink(DataLink):
    def __init__(self, host, port, verbose=False):
        super(SocketDataLink, self).__init__(verbose)
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def createDaliConnection(self):
        await self.close()
        if self.verbose:
            print(f"connect {self.host}:{self.port}")
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def send(self, header, data):
        try:
            h = header.encode("UTF-8")
            pre = "DL"
            if self.isClosed():
                if header == "ENDSTREAM":
                    # no need to reopen conn just to endstream
                    self.updateMode(header)
                    return
                else:
                    await self.reconnect()
            self.writer.write(pre.encode("UTF-8"))
            lenByte = len(h).to_bytes(1, byteorder="big", signed=False)
            self.writer.write(lenByte)
            if self.verbose:
                print(
                    "send pre {} as {}{:d}".format(pre, pre.encode("UTF-8"), lenByte[0])
                )
            self.writer.write(h)
            if self.verbose:
                print("send head {}".format(header))
            if data:
                self.writer.write(data)
                if self.verbose:
                    print("send data of size {:d}".format(len(data)))
            out = await self.writer.drain()
            if self.verbose:
                print("drained")
            self.updateMode(header)
            return out
        except:
            await self.close()
            raise

    async def parseResponse(self):
        try:
            if self.isClosed():
                raise DaliException("Connection is closed")
            pre = await self.reader.readexactly(3)
            # D ==> 68, L ==> 76
            if pre[0] == 68 and pre[1] == 76:
                hSize = pre[2]
            else:
                if self.verbose:
                    print(
                        "did not receive DL from read pre {:d}{:d}{:d}".format(
                            pre[0], pre[1], pre[2]
                        )
                    )
                await self.close()
                raise DaliException("did not receive DL from read pre")
            h = await self.reader.readexactly(hSize)
            header = h.decode("utf-8")
            type = None
            value = None
            message = None
            # if self.verbose: print("parseRespone header: {}".format(h))
            if header.startswith("PACKET "):
                s = header.split(" ")
                type = s[0]
                streamId = s[1]
                packetId = s[2]
                packetTime = s[3]
                dataStartTime = s[4]
                dataEndTime = s[5]
                dSize = int(s[6])
                data = await self.reader.readexactly(dSize)
                return DaliPacket(
                    type,
                    streamId,
                    packetId,
                    packetTime,
                    dataStartTime,
                    dataEndTime,
                    dSize,
                    data,
                )
            elif header.startswith("ID "):
                s = header.split(" ")
                type = s[0]
                value = ""
                message = header[3:]
                return DaliResponse(type, value, message)
            elif (
                header.startswith("INFO ")
                or header.startswith("OK ")
                or header.startswith("ERROR ")
            ):
                s = header.split(" ")
                type = s[0]
                value = s[1]
                dSize = int(s[2])
                m = await self.reader.readexactly(dSize)
                message = m.decode("utf-8")
                return DaliResponse(type, value, message)
            elif header == "ENDSTREAM":
                return DaliResponse(header, value, message)
            else:
                raise DaliException(
                    f"Header does not start with INFO, ID, PACKET, ENDSTREAM, OK or ERROR: {header}"
                )
            return DaliResponse(type, value, message)
        except:
            await self.close()
            raise

    def isClosed(self):
        ans = self.writer is None or self.writer.is_closing() or \
            self.reader is None or self.reader.at_eof()
        if ans:
            # is socket is closed, make sure other state is updated
            self.writer = None
            self.reader = None
            self.__mode = QUERY_MODE
        return ans

    async def close(self):
        if self.writer is not None:
            try:
                self.writer.close()
            except:
                # oh well
                pass
        self.writer = None
        self.reader = None
        self.__mode = QUERY_MODE
