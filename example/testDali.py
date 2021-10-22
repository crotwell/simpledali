import simpledali
import asyncio
import logging
from datetime import datetime, timedelta
from array import array
import jwt
from threading import Thread

logging.basicConfig(level=logging.DEBUG)

host = "129.252.35.35"
port = 15003
port = 15005
#host = "129.252.35.20"
port = 6383
uri = "ws://eeyore.seis.sc.edu:6382/datalink"

programname="simpleDali"
username="dragrace"
processid=0
architecture="python"


async def doTest(loop):
    #dali = simpledali.SocketDataLink(host, port)
    dali = simpledali.WebSocketDataLink(uri, verbose=True)
    #idTask = loop.create_task(dali.id(programname, username, processid, architecture))
    #loop.run_until_complete(idTask)
    #serverId = idTask.result()
    serverId = await dali.id(programname, username, processid, architecture)
    print("Resp: {}".format(serverId))
    serverInfo = await dali.info("STATUS")
    print("Info: {} ".format(serverInfo.message))
    serverInfo = await dali.info("STREAMS")
    print("Info: {} ".format(serverInfo.message))
    # hptime = "1551313181711158"
    # print("Position after: {}  {:d}".format(hptime, int(hptime)))
    # pafter = yield from dali.positionAfterHPTime(hptime)
    # print("PacketId after: {} {}".format(pafter.type, pafter.value))
    # nextPacket = yield from dali.read(pafter.value)
    # print("next after: {} {} {}".format(nextPacket.type, nextPacket.dataStartTime, nextPacket.dataEndTime))
    # print("hptime round trip: {} {}".format(hptime, simpledali.datetimeToHPTime(simpledali.hptimeToDatetime(int(hptime)))))
    # nowTime = datetime.utcnow()
    # print("hptime now: {} {}".format(hptime, simpledali.datetimeToHPTime(simpledali.hptimeToDatetime(int(hptime)))))

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
#    print("before writeMSeed")
#    sendTask = loop.create_task(dali.writeMSeed(msr))
#    loop.run_until_complete(sendTask)
#    print("writemseed resp {}".format(sendTask.result()))
    #closeTask = loop.create_task(dali.close())
    #loop.run_until_complete(closeTask)
    await dali.close()


loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.run_until_complete(doTest(loop))
loop.close()
