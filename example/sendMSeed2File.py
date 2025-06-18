import simpledali
import simplemseed
import asyncio
import logging
import argparse


logging.basicConfig(level=logging.DEBUG)

host = "localhost"
port = 16000
uri = f"ws://{host}:{port}/datalink"

def do_parseargs():
    parser = argparse.ArgumentParser(
        description="Send contents of miniseed 2 file via datalink."
    )
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    parser.add_argument(
        "--summary", help="one line summary per record", action="store_true"
    )
    parser.add_argument(
        "--match",
        help="regular expression to match the identifier",
    )
    parser.add_argument(
        "ms2files", metavar="ms2file", nargs="+", help="mseed2 files to print"
    )
    return parser.parse_args()


async def main():

    args = do_parseargs()
    verbose = False
    programname = "simpleDali"
    username = "dragrace"
    processid = 0
    architecture = "python"
    async with simpledali.SocketDataLink(host, port, verbose=verbose) as dali:
    # async with simpledali.WebSocketDataLink(uri, verbose=verbose) as dali:
        # very good idea to call id at start, both for logging on server
        # side and to get capabilities like packet size, dlproto or write ability
        serverId = await dali.id(programname, username, processid, architecture)
        print(f"Resp: {serverId}")

        for ms2file in args.ms2files:
            with open(ms2file, "rb") as inms2file:
                for msr in simplemseed.readMiniseed2Records(inms2file, matchsid=args.match):
                    print(f"before writeMSeed {msr.starttime().isoformat()} {msr.codes()} bytes: {len(msr.pack())} {msr.header.encoding}")
                    sendResult = await dali.writeMSeed(msr)
                    print(f"writemseed resp {sendResult}")


debug = False
asyncio.run(main(), debug=debug)
