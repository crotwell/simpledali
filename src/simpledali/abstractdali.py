from abc import ABC, abstractmethod
import asyncio
import json
from datetime import datetime, timedelta, timezone
import defusedxml.ElementTree
from .dalipacket import DaliPacket, DaliResponse

# https://raw.githubusercontent.com/iris-edu/libdali/master/doc/DataLink.protocol

MICROS = 1000000

NO_SOUP = "Write permission not granted, no soup for you!"

class DataLink(ABC):

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.token = None


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

    async def write(self, streamid, hpdatastart, hpdataend, flags, data):
        header = "WRITE {} {:d} {:d} {} {:d}".format(streamid, hpdatastart, hpdataend, flags, len(data))
        r = await self.send(header, data)
        return r

    async def writeAck(self, streamid, hpdatastart, hpdataend, data):
        await self.write(streamid, hpdatastart, hpdataend, 'A', data)
        r = await  self.parseResponse()
        if r.type == 'ERROR' and r.message.startswith("Write permission not granted, no soup for you!"):
            # no write premission to ringserver, it usually closes connection
            await self.close()
        return r

    async def writeMSeed(self, msr):
        streamid = "{}/MSEED".format(msr.codes(sep='_'))
        hpdatastart = int(msr.starttime().timestamp() * MICROS)
        hpdataend = int(msr.endtime().timestamp() * MICROS)
        if self.verbose: print("simpleDali.writeMSeed {} {} {}".format(streamid, hpdatastart, hpdataend))
        r = await self.writeAck(streamid, hpdatastart, hpdataend, msr.pack())
        return r


    async def writeJSON(self, streamid, hpdatastart, hpdataend, jsonMessage):
        if self.verbose: print("simpleDali.writeJSON {} {} {}".format(streamid, hpdatastart, hpdataend))
        jsonAsByteArray = json.dumps(jsonMessage).encode('UTF-8')
        r = await self.writeAck(streamid, hpdatastart, hpdataend, jsonAsByteArray)
        return r

    async def writeCommand(self, command, dataString=None):
        if self.verbose: print("writeCommand: cmd: {} dataStr: {}".format(command, dataString))
        dataBytes = None
        if (dataString):
            dataBytes = dataString.encode('UTF-8')
            header = "{} {}".format(command, len(dataBytes))
        else:
            header = command
        await self.send(header, dataBytes)
        r = await  self.parseResponse()
        return r

    async def auth(self, token):
        self.token = token
        if self.verbose: print("simpleDali.auth {} ".format(token))
        if isinstance(token, str):
            token = token.encode('utf-8')
        header = "AUTHORIZATION {:d}".format(len(token))
        r = await self.send(header, token)
        r = await  self.parseResponse()
        if r.type == 'ERROR' and r.message.startswith("Write permission not granted, no soup for you!"):
            # no write premission to ringserver, it usually closes connection
            await self.close()
        return r

    async def id(self, programname, username, processid, architecture):
        header = "ID {}:{}:{}:{}".format(programname, username, processid, architecture)
        r = await self.writeCommand(header, None)
        return r

    async def info(self, type):
        header = "INFO {}".format(type)
        r = await self.writeCommand(header, None)
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

    async def stream(self):
        header = "STREAM"
        await self.send(header, None)

    async def endStream(self):
        header = "ENDSTREAM"
        await self.send(header, None)

    async def reconnect(self):
        if self.verbose:
            print("reconnecting...")
        await self.close()
        await self.createDaliConnection()
        if self.token:
            await self.auth(self.token)

    def parseInfoStatus(self, infoResponse):
        """ realy simple parsing of info xml, but not using an xml parser"""
        if infoResponse.type != 'INFO' or infoResponse.value != 'STATUS':
            raise Exception("Does not look like INFO STATUS DaliResponse: {} {}".format(infoResponse.type, infoResponse.value))
        xmlTree = defusedxml.ElementTree.fromstring(infoResponse.message)
        out = {}
        for k,v in xmlTree.attrib.items():
            out[k] = v
        out['Status'] = {}
        for k,v in xmlTree.find('Status').attrib.items():
            out['Status'][k] = v
        return out
