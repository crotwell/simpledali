import simpledali
import asyncio
import logging
from datetime import datetime, timedelta
from array import array
import jwt
from threading import Thread

logging.basicConfig(level=logging.DEBUG)

host = "localhost"
port = 15000
uri = f"ws://{host}:{port}/datalink"


async def init_dali(host, port,
        verbose=False,
        programname="simpleDali",
        username="dragrace",
        processid=0,
        architecture="python"):
    dali = simpledali.SocketDataLink(host, port, verbose=verbose)
    #dali = simpledali.WebSocketDataLink(uri, verbose=True)
    serverId = await dali.id(programname, username, processid, architecture)
    print(f"Resp: {serverId}")
    return dali

async def send_test_mseed(dali):
    network = "XX"
    station = "TEST"
    location = "00"
    channel = "HNZ"
    starttime = simpledali.utcnowWithTz()
    numsamples = 100
    sampleRate=200
    shortData = array("h") # shorts
    for i in range(numsamples):
        shortData.append(i)
    msh = simpledali.MiniseedHeader(network, station, location, channel, starttime, numsamples, sampleRate)
    msr = simpledali.MiniseedRecord(msh, shortData)
    print(f"before writeMSeed {starttime.isoformat()}")
    sendResult = await dali.writeMSeed(msr)
    print(f"writemseed resp {sendResult}")


async def main():
    verbose=False
    programname="simpleDali"
    username="dragrace"
    processid=0
    architecture="python"
    dali = simpledali.SocketDataLink(host, port, verbose=verbose)
    # dali = simpledali.WebSocketDataLink(uri, verbose=True)
    serverId = await dali.id(programname, username, processid, architecture)
    print(f"Resp: {serverId}")
    for i in range(1):
        await send_test_mseed(dali)
        await asyncio.sleep(1)
    await dali.close()

debug = False
asyncio.run(main(), debug=debug)
