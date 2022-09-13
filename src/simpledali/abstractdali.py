from abc import ABC, abstractmethod
import asyncio
import json
from datetime import datetime, timedelta, timezone
import defusedxml.ElementTree
from .dalipacket import DaliPacket, DaliResponse, DaliException
from .util import datetimeToHPTime, optional_date

# https://iris-edu.github.io/libdali/datalink-protocol.html

NO_SOUP = "Write permission not granted, no soup for you!"

QUERY_MODE="query"
STREAM_MODE="stream"

class DataLink(ABC):
    def __init__(self, packet_size=-1, verbose=False):
        """init DataLink. Packet_size can be set, or can be acquired from the
        server by calling either parsedInfoStatus() or info("STATUS")
        """
        self.__mode = QUERY_MODE
        self.packet_size = packet_size
        self.verbose = verbose
        self.token = None
        self.int_types = [
            "RingSize",
            "PacketSize",
            "MaximumPacketID",
            "MaximumPackets",
            "TotalConnections",
            "SelectedConnections",
            "TotalStreams",
            "EarliestPacketID",
            "LatestPacketID",
            "Port",
            "StreamCount",
            "RXByteCount",
            "TotalStreams",
            "SelectedStreams",
            "TotalServerThreads",
        ]
        self.float_types = [
            "TXPacketRate",
            "TXByteRate",
            "RXPacketRate",
            "RXByteRate",
            "DataLatency",
            "Latency",
        ]
        self.date_types = [
            "StartTime",
            "EarliestPacketCreationTime",
            "EarliestPacketDataStartTime",
            "EarliestPacketDataEndTime",
            "LatestPacketCreationTime",
            "LatestPacketDataStartTime",
            "LatestPacketDataEndTime",
            "ConnectionTime",
            "PacketCreationTime",
            "PacketDataStartTime",
            "PacketDataEndTime",
        ]

    async def __aenter__(self):
        await self.createDaliConnection()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    @abstractmethod
    async def createDaliConnection(self):
        pass

    @abstractmethod
    async def send(self, header, data):
        pass

    @abstractmethod
    async def parseResponse(self):
        pass

    @abstractmethod
    def isClosed(self):
        pass

    @abstractmethod
    async def close(self):
        pass

    def isQueryMode(self):
        return not self.isStreamMode()

    def isStreamMode(self):
        return self.__mode == STREAM_MODE

    def updateMode(self, header):
        if header == "ENDSTREAM":
            self.__mode = QUERY_MODE
        elif header == "STREAM":
            self.__mode = STREAM_MODE
        # otherwise leave as is

    async def write(self, streamid, hpdatastart, hpdataend, flags, data):
        if self.packet_size > 0 and len(data) > self.packet_size:
            raise DaliException(
                f"Data larger than configured max packet_size, {len(data)}>{self.packet_size}",
            )
        header = "WRITE {} {:d} {:d} {} {:d}".format(
            streamid, hpdatastart, hpdataend, flags, len(data)
        )
        r = await self.send(header, data)
        return r

    async def writeAck(self, streamid, hpdatastart, hpdataend, data):
        await self.write(streamid, hpdatastart, hpdataend, "A", data)
        r = await self.parseResponse()
        if r.type == "ERROR" and r.message.startswith(
            "Write permission not granted, no soup for you!"
        ):
            # no write premission to ringserver, it usually closes connection
            await self.close()
        return r

    async def writeMSeed(self, msr):
        streamid = "{}/MSEED".format(msr.codes(sep="_"))
        hpdatastart = datetimeToHPTime(msr.starttime())
        hpdataend = datetimeToHPTime(msr.endtime())
        if self.verbose:
            print(
                "simpleDali.writeMSeed {} {} {}".format(
                    streamid, hpdatastart, hpdataend
                )
            )
        r = await self.writeAck(streamid, hpdatastart, hpdataend, msr.pack())
        return r

    async def writeJSON(self, streamid, hpdatastart, hpdataend, jsonMessage):
        if self.verbose:
            print(
                "simpleDali.writeJSON {} {} {}".format(streamid, hpdatastart, hpdataend)
            )
        jsonAsByteArray = json.dumps(jsonMessage).encode("UTF-8")
        r = await self.writeAck(streamid, hpdatastart, hpdataend, jsonAsByteArray)
        return r

    async def writeCommand(self, command, dataString=None):
        if self.verbose:
            print("writeCommand: cmd: {} dataStr: {}".format(command, dataString))
        dataBytes = None
        if dataString:
            dataBytes = dataString.encode("UTF-8")
            header = "{} {}".format(command, len(dataBytes))
        else:
            header = command
        await self.send(header, dataBytes)
        r = await self.parseResponse()
        if r.type == "ERROR":
            if self.isClosed():
                self.__mode = QUERY_MODE
            raise DaliException(f"Write {command} failed", r)
        else:
            return r

    async def auth(self, token):
        """
        Sends an AUTHORIZATION command. Note this is not part
        of the official DataLink protocol yet. See util.encodeAuthToken()
        and util.decodeAuthToken().
        """
        self.token = token
        if self.verbose:
            print("simpleDali.auth {} ".format(token))
        if isinstance(token, str):
            token = token.encode("utf-8")
        header = "AUTHORIZATION {:d}".format(len(token))
        r = await self.send(header, token)
        r = await self.parseResponse()
        if r.type == "ERROR" and r.message.startswith(
            "Write permission not granted, no soup for you!"
        ):
            # no write premission to ringserver, it usually closes connection
            await self.close()
        return r

    async def id(self, programname, username, processid, architecture):
        header = "ID {}:{}:{}:{}".format(programname, username, processid, architecture)
        r = await self.writeCommand(header, None)
        if "::" in r.message:
            # sets packet_size
            self.parse_capabilities(r.message.split("::")[1].strip())
        return r

    async def info(self, type):
        header = "INFO {}".format(type)
        r = await self.writeCommand(header, None)
        return r

    async def positionEarliest(self):
        r = await self.writeCommand("POSITION SET EARLIEST", None)
        return r

    async def positionLatest(self):
        r = await self.writeCommand("POSITION SET LATEST", None)
        return r

    async def positionAfter(self, time):
        hpdatastart = int(time.timestamp() * MICROS)
        r = await self.positionAfterHPTime(hpdatastart)
        return r

    async def positionAfterHPTime(self, hpdatastart):
        r = await self.writeCommand("POSITION AFTER {}".format(hpdatastart), None)
        return r

    async def match(self, pattern):
        r = await self.writeCommand("MATCH", pattern)
        return r

    async def reject(self, pattern):
        r = await self.writeCommand("REJECT", pattern)
        return r

    async def read(self, packetId):
        r = await self.writeCommand("READ {}".format(packetId), None)
        return r

    async def readEarliest(self):
        # maybe one day can
        # return await self.read("EARLIEST")
        r = await self.positionEarliest()
        if r.type == "OK":
            return await self.read(r.value)
        else:
            print(f"position did not return OK: {r}")
            return r

    async def readLatest(self):
        # maybe one day can
        # return await self.read("LATEST")
        r = await self.positionLatest()
        if r.type == "OK":
            return await self.read(r.value)
        else:
            return r

    async def stream(self):
        if not self.isStreamMode():
            await self.startStream()
        try:
            while not self.isClosed() and self.isStreamMode():
                daliPacket = await self.parseResponse()
                yield daliPacket
        finally:
            if not self.isClosed():
                await self.endStream()

    async def startStream(self):
        header = "STREAM"
        await self.send(header, None)

    async def endStream(self):
        header = "ENDSTREAM"
        await self.send(header, None)

    async def reconnect(self):
        if True or self.verbose:
            print("reconnecting...")
        await self.close()
        await self.createDaliConnection()
        if self.token:
            await self.auth(self.token)

    async def parsedInfoStatus(self):
        """realy simple parsing of info status xml into dict"""
        infoResponse = await self.info("STATUS")
        if infoResponse.type != "INFO" or infoResponse.value != "STATUS":
            raise DaliException(
                f"Does not look like INFO STATUS DaliResponse: {infoResponse.type} {infoResponse.value}",
                infoResponse
            )
        xmlTree = defusedxml.ElementTree.fromstring(infoResponse.message)
        out = {}
        for k, v in xmlTree.attrib.items():
            out[k] = self.info_typed(k, v)
        statusEl = xmlTree.find("Status")
        if statusEl is not None:
            out["Status"] = self.status_xml_to_dict(statusEl)
        return out

    def parse_capabilities(self, cap):
        items = cap.split()
        out = {}
        for i in items:
            if ":" in i:
                spliti = i.split(":")
                out[spliti[0]] = spliti[1]
                if spliti[0] == "PACKETSIZE":
                    self.packet_size = int(spliti[1])
        return out

    def status_xml_to_dict(self, statusEl):
        out = {}
        for k, v in statusEl.attrib.items():
            out[k] = self.info_typed(k, v)
        if "PacketSize" in out:
            self.packet_size = out["PacketSize"]
        return out

    async def parsedInfoStreams(self):
        """realy simple parsing of info streams xml into dict"""
        streamsResponse = await self.info("STREAMS")
        if streamsResponse.type != "INFO" or streamsResponse.value != "STREAMS":
            raise DaliException(
                f"Does not look like INFO STREAMS DaliResponse: {streamsResponse.type} {streamsResponse.value}",
                streamsResponse
            )
        xmlTree = defusedxml.ElementTree.fromstring(streamsResponse.message)
        out = {}
        for c in xmlTree:
            out[c.tag] = {}
            for k, v in c.attrib.items():
                out[c.tag][k] = self.info_typed(k, v)
            if c.tag == "Status":
                out["Status"] = self.status_xml_to_dict(c)
            elif c.tag.endswith("List"):
                sublist = []
                out[c.tag][c.tag[: len(c.tag) - 4]] = sublist
                for subc in c:
                    streamDict = {}
                    sublist.append(streamDict)
                    for k, v in subc.attrib.items():
                        streamDict[k] = self.info_typed(k, v)
            else:
                out[c.tag] = {}
                for k, v in c.attrib.items():
                    out[c.tag][k] = self.info_typed(k, v)

                else:
                    for subc in c:
                        out[c.tag][subc.tag] = {}
                        for k, v in subc.attrib.items():
                            out[c.tag][subc.tag][k] = self.info_typed(k, v)
        return out

    def info_typed(self, k, v):
        try:
            if k in self.int_types:
                return int(v)
            elif k in self.float_types:
                return float(v)
            elif k in self.date_types:
                return optional_date(v)
            else:
                return v
        except:
            if self.verbose:
                print(f"info_typed can't parse {k} {v}")
            return v
