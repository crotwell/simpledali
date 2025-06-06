#!/usr/bin/env python
"""Archive JSON Datalink records as JSON Lines."""

import argparse
import bz2
import asyncio
import pathlib
import re
import sys

# tomllib is std in python > 3.11 so do conditional import
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from .dalipacket import JSON_TYPE, BZ2_JSON_TYPE
from .socketdali import SocketDataLink
from .websocketdali import WebSocketDataLink
from .util import hptimeToDatetime
from . import __version__
from simplemseed import FDSNSourceId, FDSN_PREFIX

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 16000

Allowed_Flags = ["n", "s", "l", "c", "Y", "j", "H"]


class Dali2Jsonl:
    """
    Archive JSON Datalink records as JSONL.
    """

    def __init__(
        self, match, writePattern, host=DEFAULT_HOST, port=DEFAULT_PORT, websocketurl=None, verbose=False
    ):
        self.checkPattern(writePattern)
        self.do_earliest = False
        self.match = match
        self.writePattern = writePattern
        self.websocketurl = websocketurl

        if host is not None:
            self.host = host
        else:
            self.host = DEFAULT_HOST
        if port is not None:
            self.port = port
        else:
            self.port = DEFAULT_PORT
        self.verbose = verbose

        self.programname = "simpleDali"
        self.username = "Dali2Jsonl"
        self.processid = 0
        self.architecture = "python"
        if self.verbose:
            print(f"Connect to {self.host}:{self.port},")
            print(f"match {self.match}")
            print(f" write to {self.writePattern}")

    @classmethod
    def from_config(cls, conf, verbose=False):
        """
        Configured Dali2Jsonl using dict, eg from .toml config file.
        """
        cls.configure_defaults(conf)
        return cls(
            conf["datalink"]["match"],
            conf["jsonl"]["write"],
            host=conf["datalink"]["host"],
            port=conf["datalink"]["port"],
            websocketurl=conf["datalink"]["websocket"],
            verbose=verbose,
        )

    async def run(self):
        if self.websocketurl:
            async with WebSocketDataLink(self.websocketurl, verbose=self.verbose) as dali:
                await self.do_dali(dali)
        else:
            async with SocketDataLink(self.host, self.port, verbose=self.verbose) as dali:
                await self.do_dali(dali)
        return 0

    async def do_dali(self, dali):
        if self.verbose:
            print("Running...")
        # very good idea to call id at start, both for logging on server
        # side and to get capabilities like packet size or write ability
        serverId = await dali.id(
            self.programname, self.username, self.processid, self.architecture
        )
        if self.verbose:
            print(f"Id: {serverId}")

        await dali.match(self.match)
        if self.do_earliest:
            await dali.positionEarliest()
        await self.stream_data(dali)

        if self.verbose:
            print("Done.")

    async def stream_data(self, dali):
        if self.verbose:
            print("Stream")
        try:
            async for daliPacket in dali.stream():
                if self.verbose:
                    print(f"Got Dali packet: {daliPacket}")
                if daliPacket.streamIdType() == JSON_TYPE:
                    if self.verbose:
                        print(f"    JSON: {daliPacket.data.decode('utf-8')}")
                    self.saveToJSONL(daliPacket)
                elif daliPacket.streamIdType() == BZ2_JSON_TYPE:
                    daliPacket.data = bz2.decompress(daliPacket.data)
                    daliPacket.dSize = len(daliPacket.data)
                    if self.verbose:
                        print(f"    BZ2 JSON: {daliPacket.data.decode('utf-8')}")
                    self.saveToJSONL(daliPacket)
                else:
                    if self.verbose:
                        print(f"    Not JSON packet: {daliPacket.streamIdType()}")
        except asyncio.exceptions.CancelledError:
            if self.verbose:
                print("Dali task cancelled")
            return

    def saveToJSONL(self, daliPacket):
        start = hptimeToDatetime(daliPacket.dataStartTime)
        codesStr = daliPacket.streamId
        # remove "type" like /JSON
        codesStr = daliPacket.streamIdChannel()
        sid = None
        if (codesStr.startswith(FDSN_PREFIX)):
            sid = FDSNSourceId.parse(codesStr)
        elif len(codesStr.split('_')) == 4:
            sid = FDSNSourceId.parseNslc(codesStr, '_')
        if sid is not None:
            outfile = self.fileFromSidPattern(sid, start)
            outfile.parent.mkdir(parents=True, exist_ok=True)
            with open(outfile, "a", encoding="utf-8") as out:
                out.write(daliPacket.data.decode("utf-8") + "\n")
                if self.verbose:
                    print(f"   write to {outfile}")
        else:
            if self.verbose:
                print(f"   unable to parse stream id {codesStr}, skipping")

    def fileFromSidPattern(self, sid: FDSNSourceId, time):
        outfile = self.fillBaseSidPattern(sid)
        outfile = self.fillTimePattern(outfile, time)
        return pathlib.Path(outfile)

    def fillBaseSidPattern(self, sid: FDSNSourceId):
        return (
            self.writePattern.replace("%n", sid.networkCode)
            .replace("%s", sid.stationCode)
            .replace("%l", sid.locationCode)
            .replace("%c", sid.shortChannelCode())
        )

    def fillTimePattern(self, base, time):
        return (
            base.replace("%Y", str(time.year).zfill(4))
            .replace("%j", str(time.timetuple().tm_yday).zfill(3))
            .replace("%H", str(time.hour).zfill(2))
        )

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
        regexp = re.compile("%[a-zA-Z]")
        allFlags = regexp.findall(p)
        for f in allFlags:
            flag = f[1]
            if flag not in Allowed_Flags:
                raise ValueError(
                    f"directory value {f} not allowed in write pattern {p}"
                )
        return True

    @staticmethod
    def configure_defaults(conf):
        if "datalink" not in conf:
            raise ValueError("[datalink] is required in configuration toml")
        dali_conf = conf["datalink"]
        if "programname" not in dali_conf:
            dali_conf["programname"] = "dali2jsonl"
        if "username" not in dali_conf:
            dali_conf["username"] = "simpleDali"
        if "processid" not in dali_conf:
            dali_conf["processid"] = 0
        if "architecture" not in dali_conf:
            dali_conf["architecture"] = "python"
        if "match" not in dali_conf:
            raise ValueError("match is required in configuration toml")
        if "websocket" not in dali_conf:
            dali_conf["websocket"] = None
            if "host" not in dali_conf:
                dali_conf["host"] = DEFAULT_HOST
            if "port" not in dali_conf:
                dali_conf["port"] = DEFAULT_PORT
        else:
            dali_conf["host"] = None
            dali_conf["port"] = None
        if "jsonl" not in conf:
            raise ValueError("[jsonl] is required in configuration toml")
        jsonl_conf = conf["jsonl"]
        if "write" not in jsonl_conf:
            raise ValueError("write is required in configuration [jsonl] toml")


def do_parseargs():
    parser = argparse.ArgumentParser(
        description=f"""
        Archive JSON datalink packets as JSON Lines.
        Version={__version__}"""
    )
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    parser.add_argument(
        "-c",
        "--conf",
        required=True,
        help="Configuration as TOML",
        type=argparse.FileType("rb"),
    )
    parser.add_argument(
        "--earliest", help="start at earliest packet in server", action="store_true"
    )
    return parser.parse_args()


def main():

    args = do_parseargs()
    conf = tomllib.load(args.conf)
    args.conf.close()
    c = Dali2Jsonl.from_config(conf, verbose=args.verbose)
    if args.earliest:
        c.do_earliest = True
    try:
        debug = False
        asyncio.run(c.run())
    except KeyboardInterrupt:
        # cntrl-c
        print("Goodbye...")
    sys.exit(0)


if __name__ == "__main__":
    main()
