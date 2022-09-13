import simpledali
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
    streamid = f"{network}_{station}_00_SOH/JSON"
    hpdatastart = simpledali.datetimeToHPTime(starttime)
    hpdataend = hpdatastart
    jsonMessage = {
        "from": "json",
        "to": "you",
        "msg": "howdy",
        "when": starttime.isoformat(),
    }
    sendResult = await dali.writeJSON(streamid, hpdatastart, hpdataend, jsonMessage)
    print(f"writeJSON resp {sendResult}")


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
        print(f"Id: {serverId}")
        for i in range(numSend):
            await send_test_json(dali)
            await asyncio.sleep(1)


debug = False
asyncio.run(main(), debug=debug)
