# Simple example of sending and receiving Datalink packets

First start up a ringserver, available from:
https://github.com/iris-edu/ringserver/releases

The included `ring.conf` set up datalink on port 16000 for localhost. Start with:
```
ringserver ring.conf
```

`getid.py` will query the server id and then quit. For example:
```
python example/getid.py
Resp: type=ID value= message=DataLink 2020.075 :: DLPROTO:1.0 PACKETSIZE:512 WRITE
```

`readstats.py` will open a datalink connections, do status and streams
and print the results

`readdali.py` will open a datalink connections, stream data and
print a line or two for each packet it receives.

`sendJsonPacket.py` will create a Datalink packet containing JSON and send it.

`sendBzJsonPacket.py` will create a Datalink packet containing JSON, compress it with Bzip2 and send it.

`sendMSeedPacket.py` will create a Datalink packet containing Miniseed and send it.

`sendMSeed2File.py` will read files containing miniseed2, create  Datalink packets containing the Miniseed and send them.

`sendMSeed3Packet.py` will create a Datalink packet containing Miniseed3 and send it.

The output from readdali.py will look something like:

```
example % python readdali.py
connecting ws://localhost:16000/datalink
Websocket connected to ws://localhost:16000/datalink
connecting ws://localhost:16000/datalink
Websocket connected to ws://localhost:16000/datalink
writeCommand: cmd: ID simpleDali:dragrace:0:python dataStr: None
Id: type=ID value= message=DataLink v1.1 (RingServer/4.1.0-RC2.1) :: DLPROTO:1.1 PACKETSIZE:512 WRITE
Match packets: FDSN:XX_.*
writeCommand: cmd: MATCH dataStr: FDSN:XX_.*
Stream
Got Dali packet: PACKET FDSN:XX_TEST_00_H_N_Z/MSEED 10 1750259336643075 1750259336642739 1750259337137739 512
    MSeed: XX.TEST.00.HNZ 2025-06-18 15:08:56.642700+00:00 2025-06-18 15:08:56.642700+00:00 (100 pts)
^CGoodbye...

```

Use control-c to quit.
