import simpledali
import asyncio
import logging
from datetime import datetime, timedelta
from array import array
import jwt
from threading import Thread
import sys

logging.basicConfig(level=logging.DEBUG)

host = "localhost"
port = 18000
uri = f"ws://{host}:{port}/datalink"

async def init_dali(host, port, verbose=False,
        programname="simpleDali",
        username="dragrace",
        processid=0,
        architecture="python"):
    dali = simpledali.SocketDataLink(host, port, verbose=verbose)
    #dali = simpledali.WebSocketDataLink(uri, verbose=True)
    serverId = await dali.id(programname, username, processid, architecture)
    print(f"Resp: {serverId}")
    serverInfo = await dali.info("STATUS")
    print(f"Info Status: {serverInfo.message} ")
    serverInfo = await dali.info("STREAMS")
    print(f"Info Streams: {serverInfo.message} ")
    return dali

async def stream_data(dali):
    await dali.stream()
    print(f"Stream")
    try:
        while not dali.isClosed():
            daliPacket = await dali.parseResponse()
            print(f"Got Dali packet: {daliPacket}")
            if daliPacket.streamId.endswith("/MSEED"):
                msr = simpledali.miniseed.unpackMiniseedRecord(daliPacket.data)
                print(f"    MSeed: {msr}")
            elif daliPacket.streamId.endswith("/JSON"):
                print(f"    JSON: {daliPacket.data.decode('utf-8')}")
    except asyncio.exceptions.CancelledError:
        print(f"Dali task cancelled")
        return

async def main():
    dali = await init_dali(host, port, verbose=False, programname="readdali")
    await dali.createDaliConnection()
    daliPacket = await dali.readEarliest()
    print(f"First Dali packet: {daliPacket}")
    daliPacket = await dali.readLatest()
    print(f"Last Dali packet: {daliPacket}")
    await stream_data(dali)
    print(f"Closing datalink")
    await dali.close()


try:
    debug = False
    asyncio.run(main(), debug=debug)
except KeyboardInterrupt:
    # cntrl-c
    print("Goodbye...")
