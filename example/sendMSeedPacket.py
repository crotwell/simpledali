import simpledali
import simplemseed
import asyncio
import logging
from datetime import datetime, timedelta
from array import array
import jwt
from threading import Thread
import numpy as np

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
    sendResult = await dali.writeMSeed(msr, 1001)
    print(f"writemseed resp {sendResult}")


async def send_steim_mseed(dali, component, encoding, pktid=None):
    network = "XX"
    station = "TEST"
    location = "00"
    channel = f"HN{component}"
    starttime = simpledali.utcnowWithTz()
    numsamples = 100
    sampleRate = 200
    data = np.zeros(numsamples, dtype=np.int32)
    for i in range(len(data)):
        data[i] = i
    if encoding == simplemseed.seedcodec.STEIM1:
        encData = simplemseed.EncodedDataSegment(
            simplemseed.seedcodec.STEIM1,
            simplemseed.encodeSteim1(data, frames=7), # 7 frames => 512 byte record
            numsamples,
            True)
    elif encoding == simplemseed.seedcodec.STEIM2:
        encData = simplemseed.EncodedDataSegment(
            simplemseed.seedcodec.STEIM2,
            simplemseed.encodeSteim2(data, frames=7), # 7 frames => 512 byte record
            numsamples,
            True)
    else:
        # primitive type, guess based on numpy array dtype
        encData = simplemseed.encode(data)
    print(f"enc data: {len(encData.dataBytes)}")
    msh = simplemseed.MiniseedHeader(
        network, station, location, channel, starttime, numsamples, sampleRate
    )
    msr = simplemseed.MiniseedRecord(msh, data=encData)
    print(f"before writeMSeed {starttime.isoformat()} {msr.codes()} bytes: {len(msr.pack())} {msr.header.encoding} {pktid}")
    sendResult = await dali.writeMSeed(msr, pktid)
    print(f"writemseed resp {sendResult}")

async def send_several(dali, numSend, encoding=-1):
    pktid=1001
    for i in range(numSend):
        for component in ['X', 'Y', 'Z']:
            #await send_test_mseed(dali, component)
            await send_steim_mseed(dali, component, encoding, pktid)
            pktid+=1
        await asyncio.sleep(1)

async def main():
    numSend = 3
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

        #await send_steim_mseed(dali, "Z", 2)
        await send_several(dali, numSend, simplemseed.seedcodec.STEIM2)


debug = False
asyncio.run(main(), debug=debug)
