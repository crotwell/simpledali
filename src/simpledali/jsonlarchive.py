#!/usr/bin/env python
"""Archive JSON Datalink records as JSONL."""
import os
import argparse
import asyncio
import pathlib
import re

from .abstractdali import DataLink
from .dalipacket import DaliPacket, DaliResponse
from .jsonencoder import JsonEncoder
from .util import datetimeToHPTime, hptimeToDatetime, utcnowWithTz, encodeAuthToken
from .socketdali import SocketDataLink
from .websocketdali import WebSocketDataLink

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 18000

JSON_SUFFIX = "/JSON"

Allowed_Flags = ["n", "s", "l", "c", "Y", "j", "H"]

class JsonlArchive:
    """Archive JSON Datalink records as JSONL."""
    def __init__(self, match, writePattern, host=DEFAULT_HOST, port=DEFAULT_PORT, verbose=False):
        self.checkPattern(writePattern)
        self.match = match
        self.writePattern = writePattern
        if host is not None:
            self.host = host
        else:
            self.host = DEFAULT_HOST
        if port is not None:
            self.port = port
        else:
            self.port = DEFAULT_PORT
        self.verbose = verbose

        self.programname="simpleDali",
        self.username="jsonlarchive",
        self.processid=0,
        self.architecture="python"
        if self.verbose:
            print(f"Connect to {self.host}:{self.port}, write to {self.writePattern}")
    async def run(self):
        if self.verbose:
            print(f"Running...")
        self.dali = SocketDataLink(self.host, self.port, verbose=self.verbose)
        await self.dali.createDaliConnection()
        # very good idea to call id at start, both for logging on server
        # side and to get capabilities like packet size or write ability
        serverId = await self.dali.id(self.programname, self.username, self.processid, self.architecture)
        print(f"Id: {serverId}")

        await self.dali.match(self.match)
        await self.stream_data()

        await self.dali.close()
        if self.verbose:
            print(f"Done.")
        return 0

    async def stream_data(self):
        await self.dali.stream()
        if self.verbose:
            print(f"Stream")
        try:
            while not self.dali.isClosed():
                daliPacket = await self.dali.parseResponse()
                if self.verbose:
                    print(f"Got Dali packet: {daliPacket}")
                if daliPacket.streamId.endswith("/JSON"):
                    if self.verbose:
                        print(f"    JSON: {daliPacket.data.decode('utf-8')}")
                    self.saveToJSONL(daliPacket)
        except asyncio.exceptions.CancelledError:
            if self.verbose:
                print(f"Dali task cancelled")
            return

    def saveToJSONL(self, daliPacket):
        start = hptimeToDatetime(daliPacket.dataStartTime)
        codesStr = daliPacket.streamId
        if daliPacket.streamId.endswith(JSON_SUFFIX):
            codesStr = daliPacket.streamId[:-5]
        codes = codesStr.split('_')
        chan = ""
        loc = ""
        sta = ""
        net = ""
        if len(codes) > 3:
            chan = codes[3]
        if len(codes) > 2:
            loc = codes[2]
        if len(codes) > 1:
            sta = codes[1]
        net = codes[0]
        outfile = self.fileFromPattern(net, sta, loc, chan, start)
        outfile.parent.mkdir(parents=True, exist_ok=True)
        with open(outfile, 'a') as out:
            out.write(daliPacket.data.decode('utf-8')+'\n')

    def fileFromPattern(self, net, sta, loc, chan, time):
        outfile = self.fillBasePattern(net, sta, loc, chan)
        outfile = self.fillTimePattern(outfile, time)
        return pathlib.Path(outfile)
    def fillBasePattern(self, net, sta, loc, chan):
        return self.writePattern.replace('%n', net).replace('%s', sta)\
            .replace('%l', loc).replace('%c', chan)
    def fillTimePattern(self, base, time):
        return base\
            .replace('%Y',str(time.year))\
            .replace('%j',str(time.timetuple().tm_yday))\
            .replace('%H',str(time.hour))
    def checkPattern(self, p):
        """
           checks pattern for allowed flags as not all that are supported
           by ringserver are supported here. Must only include:
           * n network code, white space removed
           * s station code, white space removed
           * l  location code, white space removed
           * c  channel code, white space removed
           * Y  year, 4 digits
           * j  day of year, 3 digits zero padded
           * H  hour, 2 digits zero padded

           @param p mseed archive pattern string
           @returns true if all flags are allowed

        """

        if len(p) == 0:
            raise ValueError(f"write pattern is empty '{p}'")
        regexp = re.compile('%[a-zA-Z]');
        allFlags = regexp.findall(p);
        for f in allFlags:
            flag = f[1]
            if flag not in Allowed_Flags:
                raise ValueError(f"directory value {f} not allowed in write pattern {p}")
        return True;


def do_parseargs():
    parser = argparse.ArgumentParser(description='Archive JSON datalink packets as JSONL.')
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
    parser.add_argument("-m", "--match", required=True, help="Match regular expression pattern, ex '.*/JSON'")
    parser.add_argument("-w", "--write", required=True, help="JSONL Write pattern, usage similar to MSeedWrite in ringserver")
    parser.add_argument("-d", "--dalihost",
                        help="datalink host, defaults to localhost",
                        default=DEFAULT_HOST)
    parser.add_argument("-p", "--daliport",
                        help="datalink port, defaults to 18000",
                        default=DEFAULT_PORT)
    return parser.parse_args()


def main():
    import sys
    args = do_parseargs()
    c = JsonlArchive(args.match, args.write, host=args.dalihost, port=args.daliport, verbose=args.verbose)

    try:
        debug = False
        asyncio.run(c.run())
    except KeyboardInterrupt:
        # cntrl-c
        print("Goodbye...")
    sys.exit(0)


if __name__ == '__main__':
    main()
