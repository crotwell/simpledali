#!/usr/bin/env python
"""Archive JSON Datalink records as JSON Lines."""
import os
import argparse
import asyncio
import pathlib
import re

# tomllib is std in python > 3.11 so do conditional import
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from .abstractdali import DataLink
from .dalipacket import DaliPacket, DaliResponse
from .jsonencoder import JsonEncoder
from .util import datetimeToHPTime, hptimeToDatetime, utcnowWithTz, encodeAuthToken
from .socketdali import SocketDataLink
from .websocketdali import WebSocketDataLink

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 16000

JSON_SUFFIX = "/JSON"

Allowed_Flags = ["n", "s", "l", "c", "Y", "j", "H"]


class Dali2Jsonl:
    """Archive JSON Datalink records as JSONL."""

    def __init__(
        self, match, writePattern, host=DEFAULT_HOST, port=DEFAULT_PORT, verbose=False
    ):
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

        self.programname = "simpleDali"
        self.username = "Dali2Jsonl"
        self.processid = 0
        self.architecture = "python"
        if self.verbose:
            print(f"Connect to {self.host}:{self.port}, write to {self.writePattern}")

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
            verbose=verbose,
        )

    async def run(self):
        if self.verbose:
            print(f"Running...")
        async with SocketDataLink(self.host, self.port, verbose=self.verbose) as dali:
            # very good idea to call id at start, both for logging on server
            # side and to get capabilities like packet size or write ability
            serverId = await self.dali.id(
                self.programname, self.username, self.processid, self.architecture
            )
            print(f"Id: {serverId}")

            await self.dali.match(self.match)
            await self.stream_data()

        if self.verbose:
            print(f"Done.")
        return 0

    async def stream_data(self):
        await self.dali.stream()
        if self.verbose:
            print(f"Stream")
        try:
            async for daliPacket in self.dali.stream():
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
        # remove "type" like /JSON
        codesStr = codesStr.split("/")[0]
        codes = codesStr.split("_")
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
        with open(outfile, "a") as out:
            out.write(daliPacket.data.decode("utf-8") + "\n")

    def fileFromPattern(self, net, sta, loc, chan, time):
        outfile = self.fillBasePattern(net, sta, loc, chan)
        outfile = self.fillTimePattern(outfile, time)
        return pathlib.Path(outfile)

    def fillBasePattern(self, net, sta, loc, chan):
        return (
            self.writePattern.replace("%n", net)
            .replace("%s", sta)
            .replace("%l", loc)
            .replace("%c", chan)
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
        else:
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
            if "host" not in dali_conf:
                dali_conf["host"] = DEFAULT_HOST
            if "port" not in dali_conf:
                dali_conf["port"] = DEFAULT_PORT
        if "jsonl" not in conf:
            raise ValueError("[jsonl] is required in configuration toml")
            jsonl_conf = conf["jsonl"]
            if "write" not in jsonl_conf:
                raise ValueError("write is required in configuration toml")


def do_parseargs():
    parser = argparse.ArgumentParser(
        description="Archive JSON datalink packets as JSON Lines."
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
    return parser.parse_args()


def main():
    import sys

    args = do_parseargs()
    conf = tomllib.load(args.conf)
    args.conf.close()
    c = Dali2Jsonl.from_config(conf, verbose=args.verbose)
    try:
        debug = False
        asyncio.run(c.run())
    except KeyboardInterrupt:
        # cntrl-c
        print("Goodbye...")
    sys.exit(0)


if __name__ == "__main__":
    main()
