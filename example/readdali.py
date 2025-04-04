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
        # side and to get capabilities like packet size or write ability
        serverId = await dali.id(programname, username, processid, architecture)
        print(f"Id: {serverId}")
        # can get status, stream, connections parsed into a dict
        infoStatus = await dali.parsedInfoStatus()
        print(
            f"Info Status: {json.dumps(infoStatus, indent=4, sort_keys=True, cls=simpledali.JsonEncoder)} "
        )

        # set regex match pattern, really important on high volume server
        # to avoid getting way to much data and too many info streams
        # older ringserver (DLPROTO 1.0) uses N_S_L_C style
        # ringserver4 (DLPROTO 1.1) uses FDSN SourceIds and autopromotes /MSEED
        # packets ids to FDSN:
        if dali.dlproto == simpledali.DLPROTO_1_0:
            # old style
            matchPat = "^XX_.*"
        else:
            # new style
            matchPat = "^FDSN:XX_.*"
        await dali.match(matchPat)

        infoStreams = await dali.parsedInfoStreams()
        print(
            f"Info Streams: {json.dumps(infoStreams, indent=4, sort_keys=True, cls=simpledali.JsonEncoder)} "
        )
        # or can get status, streams and connections as xml
        status_xml = await dali.info("STATUS")
        parsed_xml = xml.dom.minidom.parseString(status_xml.message)
        print()
        print(parsed_xml.toprettyxml())
        print()
        streams_xml = await dali.info("STREAMS")
        parsed_xml = xml.dom.minidom.parseString(streams_xml.message)
        print()
        print(parsed_xml.toprettyxml())
        print()
        try:
            streams_xml = await dali.info("CONNECTIONS")
            print(f"   {streams_xml.type}")
            print(f"   {streams_xml}")
            parsed_xml = xml.dom.minidom.parseString(streams_xml.message)
            print()
            print(parsed_xml.toprettyxml())
            print()
        except simpledali.DaliException as err:
            print(f"Unable to query CONNECTIONS: {err}")
            # ringserver closes connection on CONNECTIONS when no
            # permission, check and reconnect
            try:
                serverId = await dali.id(programname, username, processid, architecture)
            except ConnectionClosed:
                dali.reconnect()


        # try to read earliest packet, note this might fail on a high volume
        # server as it requires two transactions and the packet might fall
        # out of the ring before it can be requested
        try:
            daliPacket = await dali.readEarliest()
            print(f"First Dali packet: {daliPacket}")
        except simpledali.DaliException as err:
            print(f"Oops, first packet fell out of ring before we could grab it")
            print(F"  {err}")
        try:
            daliPacket = await dali.readLatest()
            print(f"Last Dali packet: {daliPacket}")
        except simpledali.DaliException as err:
            print(f"Oops, no last packet, maybe an empty ring?")
            print(F"  {err}")

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
