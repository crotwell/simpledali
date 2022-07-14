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
    verbose = False
    programname = "simpleDali"
    username = "dragrace"
    processid = 0
    architecture = "python"
    dali = simpledali.SocketDataLink(host, port, verbose=verbose)
    # dali = simpledali.WebSocketDataLink(uri, verbose=verbose)
    serverId = await dali.id(programname, username, processid, architecture)
    print(f"Resp: {serverId}")
    for i in range(1):
        await send_test_json(dali)
        await asyncio.sleep(1)
    await dali.close()


debug = False
asyncio.run(main(), debug=debug)
