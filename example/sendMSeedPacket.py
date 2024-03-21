import simpledali
import simplemseed
import asyncio
import logging
from datetime import datetime, timedelta
from array import array
import jwt
from threading import Thread

logging.basicConfig(level=logging.DEBUG)

host = "localhost"
port = 16000
uri = f"ws://{host}:{port}/datalink"


async def init_dali(
    host,
    port,
    verbose=False,
    programname="simpleDali",
    username="dragrace",
    processid=0,
    architecture="python",
):
    dali = simpledali.SocketDataLink(host, port, verbose=verbose)
    # dali = simpledali.WebSocketDataLink(uri, verbose=True)
    serverId = await dali.id(programname, username, processid, architecture)
    print(f"Resp: {serverId}")
    return dali


async def send_test_mseed(dali, component):
    network = "XX"
    station = "TEST"
    location = "00"
    channel = f"HN{component}"
    starttime = simpledali.utcnowWithTz()
    numsamples = 100
    sampleRate = 200
    shortData = array("h")  # shorts
    for i in range(numsamples):
        shortData.append(i)
    msh = simplemseed.MiniseedHeader(
        network, station, location, channel, starttime, numsamples, sampleRate
    )
    msr = simplemseed.MiniseedRecord(msh, shortData)
    print(f"before writeMSeed {starttime.isoformat()} {msr.codes()}")
    sendResult = await dali.writeMSeed(msr)
    print(f"writemseed resp {sendResult}")


async def main():
    numSend = 3
    verbose = False
    programname = "simpleDali"
    username = "dragrace"
    processid = 0
    architecture = "python"
    async with simpledali.SocketDataLink(host, port, verbose=verbose) as dali:
    # async with simpledali.WebSocketDataLink(uri, verbose=verbose) as dali:
        serverId = await dali.id(programname, username, processid, architecture)
        print(f"Resp: {serverId}")
        for i in range(numSend):
            for component in ['X', 'Y', 'Z']:
                await send_test_mseed(dali, component)
            await asyncio.sleep(1)


debug = False
asyncio.run(main(), debug=debug)
