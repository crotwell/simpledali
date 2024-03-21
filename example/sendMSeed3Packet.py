import simpledali
from  simplemseed import MSeed3Header, MSeed3Record, FDSNSourceId
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


async def send_test_mseed(dali):
    network = "XX"
    station = "TEST"
    location = "00"
    channel = "HNZ"
    numsamples = 100
    sampleRate = 200
    recordtimerange = timedelta(seconds=(numsamples-1)/sampleRate)
    starttime = simpledali.utcnowWithTz() - recordtimerange
    shortData = array("h")  # shorts
    for i in range(numsamples):
        shortData.append(i)

    header = MSeed3Header()
    header.starttime = starttime
    header.sampleRatePeriod = sampleRate
    identifier = FDSNSourceId.createUnknown(header.sampleRate, sourceCode="XQX")
    ms3record = MSeed3Record(header, identifier, shortData)

    print(f"before writeMSeed3 {ms3record.identifier} {starttime.isoformat()}")
    sendResult = await dali.writeMSeed3(ms3record)
    print(f"writemseed resp {sendResult}")


async def main():
    numSend = 1
    verbose = True
    programname = "simpleDali"
    username = "dragrace"
    processid = 0
    architecture = "python"
    async with simpledali.SocketDataLink(host, port, verbose=verbose) as dali:
    # async with simpledali.WebSocketDataLink(uri, verbose=verbose) as dali:
        serverId = await dali.id(programname, username, processid, architecture)
        print(f"Resp: {serverId}")
        for i in range(numSend):
            await send_test_mseed(dali)
            await asyncio.sleep(1)


debug = False
asyncio.run(main(), debug=debug)
