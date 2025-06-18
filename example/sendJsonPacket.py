import simpledali
from simplemseed import FDSNSourceId
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


async def send_test_json(dali):
    network = "XX"
    station = "TEST"
    starttime = simpledali.utcnowWithTz()
    print(f"before writeJSON {starttime}")
    if dali.dlproto == simpledali.DLPROTO_1_0:
        # old style
        streamid = f"{network}_{station}_00_SOH/JSON"
    else:
        sid = FDSNSourceId.fromNslc(network, station,"00","SOH")
        streamid = simpledali.fdsnSourceIdToStreamId(sid, simpledali.JSON_TYPE)
    hpdatastart = simpledali.datetimeToHPTime(starttime)
    hpdataend = hpdatastart
    jsonMessage = {
        "from": "json",
        "to": "you",
        "msg": "howdy",
        "when": starttime.isoformat(),
    }
    sendResult = await dali.writeJSON(streamid, hpdatastart, hpdataend, jsonMessage)
    print(f"writeJSON {streamid} response: {sendResult}")


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
        print(f"Id: {serverId}")
        for i in range(numSend):
            await send_test_json(dali)
            await asyncio.sleep(1)


debug = False
asyncio.run(main(), debug=debug)
