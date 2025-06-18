import simpledali
import simplemseed
import asyncio
import bz2
import json
import logging
from datetime import datetime, timedelta
from array import array
from threading import Thread
import sys
import xml.dom.minidom
from websockets import ConnectionClosed


host = "localhost"
port = 16000
# ping_interval=5
ping_interval = None  # to disable ping-pong until ringserver supports, this is default

async def stream_data(dali, max=0):
    print(f"Stream")
    count = 0
    async for daliPacket in dali.stream():
        count += 1
        print(f"Got Dali packet: {daliPacket}")
        if daliPacket.streamIdType() == simpledali.MSEED_TYPE:
            msr = simplemseed.unpackMiniseedRecord(daliPacket.data)
            print(f"    MSeed: {msr}")
        elif daliPacket.streamIdType() == simpledali.MSEED3_TYPE:
            ms3 = simplemseed.unpackMSeed3Record(daliPacket.data)
            print(f"    MSeed3: {ms3}")
        elif daliPacket.streamIdType() == simpledali.JSON_TYPE:
            print(f"    JSON: {daliPacket.data.decode('utf-8')}")
        elif daliPacket.streamIdType() == simpledali.BZ2_JSON_TYPE:
            daliPacket.data = bz2.decompress(daliPacket.data)
            print(f"    BZ2 JSON: {daliPacket.data.decode('utf-8')}")
        else:
            print(f"    Unknown type")
        if max > 0 and count >= max:
            print(f"End Stream: {count}>={max}")
            await dali.close()

async def main(host, port, verbose=False):
    # these all have defaults
    programname = "simpleDali"
    username = "dragrace"
    processid = 0
    architecture = "python"
    # async with  simpledali.SocketDataLink(host, port, verbose=verbose) as dali:
    # or can use websockets if the server implements
    uri = f"ws://{host}:{port}/datalink"
    async with simpledali.WebSocketDataLink(
        uri, verbose=verbose, ping_interval=ping_interval
    ) as dali:
        # this is not required, connection will be created on first use
        await dali.createDaliConnection()
        # very good idea to call id at start, both for logging on server
        # side and to get capabilities like packet size, dlproto or write ability
        serverId = await dali.id(programname, username, processid, architecture)
        print(f"Id: {serverId}")

        # set regex match pattern, really important on high volume server
        # to avoid getting way to much data
        # format for older ringserver (dlproto 1.0) is NN_SSSSS_LL_CCC/MSEED
        # and for new v4 ringserver (dlproto 1.1) is FDSN:NN_SSSS_LL_B_S_S/MSEED
        # Here just limit to a single network, but station/channel codes
        # could also be added
        networkCode = "XX"
        if dali.dlproto == simpledali.DLPROTO_1_0:
            matchPattern = f"^{networkCode}_.*"
        else:
            matchPattern = f"FDSN:{networkCode}_.*"
        print(f"Match packets: {matchPattern}")
        await dali.match(matchPattern)
        # stream data
        try:
            await stream_data(dali, max=5)
            # dali will be closed automatically here by "async with"
        except simpledali.DaliClosed as e:
            print(f"Dali connection closed by server: {e.message}")

try:
    debug = False
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()
    asyncio.run(main(host, port, verbose=True), debug=debug)
except KeyboardInterrupt:
    # cntrl-c
    print("Goodbye...")
