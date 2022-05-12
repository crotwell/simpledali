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

`readdali.py` will open a datalink connections, do status and streams and
print a line or two for each packet it receives.

`sendJsonPacket.py` will create a Datalink packet containing JSON and send it.

`sendMSeedPacket.py` will create a Datalink packet containing Miniseed and send it.

The output from readdali.py will look something like:
```
python3 readdali.py
DEBUG:asyncio:Using selector: KqueueSelector
Id: type=ID value= message=DataLink 2020.075 :: DLPROTO:1.0 PACKETSIZE:512 WRITE
Info Status: {
    "Capabilities": "DLPROTO:1.0 PACKETSIZE:512 WRITE",
    "ServerID": "Localhost testing Ring Server",
    "Status": {
        "EarliestPacketCreationTime": "2021-10-25T14:02:04.060701Z",
        "EarliestPacketDataEndTime": "2021-10-25T14:02:04.555115Z",
        "EarliestPacketDataStartTime": "2021-10-25T14:02:04.060115Z",
        "EarliestPacketID": 1,
        "LatestPacketCreationTime": "2021-10-26T19:16:58.812817Z",
        "LatestPacketDataEndTime": "2021-10-26T19:16:59.307422Z",
        "LatestPacketDataStartTime": "2021-10-26T19:16:58.812422Z",
        "LatestPacketID": 194,
        "MaximumPacketID": 16777215,
        "MaximumPackets": 1633,
        "MemoryMappedRing": "FALSE",
        "PacketSize": 512,
        "RXByteRate": 0.0,
        "RXPacketRate": 0.0,
        "RingSize": 1048576,
        "RingVersion": "1",
        "StartTime": "2021-10-25T18:59:25Z",
        "TXByteRate": 0.0,
        "TXPacketRate": 0.0,
        "TotalConnections": 1,
        "TotalStreams": 2,
        "VolatileRing": "FALSE"
    },
    "Version": "2020.075"
}
Info Streams: {
    "Status": {
        "EarliestPacketCreationTime": "2021-10-25T14:02:04.060701Z",
        "EarliestPacketDataEndTime": "2021-10-25T14:02:04.555115Z",
        "EarliestPacketDataStartTime": "2021-10-25T14:02:04.060115Z",
        "EarliestPacketID": 1,
        "LatestPacketCreationTime": "2021-10-26T19:16:58.812817Z",
        "LatestPacketDataEndTime": "2021-10-26T19:16:59.307422Z",
        "LatestPacketDataStartTime": "2021-10-26T19:16:58.812422Z",
        "LatestPacketID": 194,
        "MaximumPacketID": 16777215,
        "MaximumPackets": 1633,
        "MemoryMappedRing": "FALSE",
        "PacketSize": 512,
        "RXByteRate": 0.0,
        "RXPacketRate": 0.0,
        "RingSize": 1048576,
        "RingVersion": "1",
        "StartTime": "2021-10-25T18:59:25Z",
        "TXByteRate": 0.0,
        "TXPacketRate": 0.0,
        "TotalConnections": 1,
        "TotalStreams": 2,
        "VolatileRing": "FALSE"
    },
    "StreamList": {
        "SelectedStreams": 2,
        "Stream": [
            {
                "DataLatency": 32.6,
                "EarliestPacketDataEndTime": "2021-10-25T14:02:04.555115Z",
                "EarliestPacketDataStartTime": "2021-10-25T14:02:04.060115Z",
                "EarliestPacketID": 1,
                "LatestPacketDataEndTime": "2021-10-26T19:16:59.307422Z",
                "LatestPacketDataStartTime": "2021-10-26T19:16:58.812422Z",
                "LatestPacketID": 194,
                "Name": "XX_TEST_00_HNZ/MSEED"
            },
            {
                "DataLatency": 37.6,
                "EarliestPacketDataEndTime": "2021-10-25T18:15:19.392161Z",
                "EarliestPacketDataStartTime": "2021-10-25T18:15:19.392161Z",
                "EarliestPacketID": 56,
                "LatestPacketDataEndTime": "2021-10-26T19:16:54.297198Z",
                "LatestPacketDataStartTime": "2021-10-26T19:16:54.297198Z",
                "LatestPacketID": 193,
                "Name": "XX_TEST_SOH/JSON"
            }
        ],
        "TotalStreams": 2
    }
}

<?xml version="1.0" ?>
<DataLink Version="2020.075" ServerID="Localhost testing Ring Server" Capabilities="DLPROTO:1.0 PACKETSIZE:512 WRITE">
	<Status StartTime="2021-10-25 18:59:25" RingVersion="1" RingSize="1048576" PacketSize="512" MaximumPacketID="16777215" MaximumPackets="1633" MemoryMappedRing="FALSE" VolatileRing="FALSE" TotalConnections="1" TotalStreams="2" TXPacketRate="0.0" TXByteRate="0.0" RXPacketRate="0.0" RXByteRate="0.0" EarliestPacketID="1" EarliestPacketCreationTime="2021-10-25 14:02:04.060701" EarliestPacketDataStartTime="2021-10-25 14:02:04.060115" EarliestPacketDataEndTime="2021-10-25 14:02:04.555115" LatestPacketID="194" LatestPacketCreationTime="2021-10-26 19:16:58.812817" LatestPacketDataStartTime="2021-10-26 19:16:58.812422" LatestPacketDataEndTime="2021-10-26 19:16:59.307422"/>
	<ServerThreads TotalServerThreads="2">
		<Thread Flags=" ACTIVE" Type="IPv4: DataLink SeedLink HTTP" Port="18000"/>
		<Thread Flags=" ACTIVE" Type="IPv6: DataLink SeedLink HTTP" Port="18000"/>
	</ServerThreads>
</DataLink>



<?xml version="1.0" ?>
<DataLink Version="2020.075" ServerID="Localhost testing Ring Server" Capabilities="DLPROTO:1.0 PACKETSIZE:512 WRITE">
	<Status StartTime="2021-10-25 18:59:25" RingVersion="1" RingSize="1048576" PacketSize="512" MaximumPacketID="16777215" MaximumPackets="1633" MemoryMappedRing="FALSE" VolatileRing="FALSE" TotalConnections="1" TotalStreams="2" TXPacketRate="0.0" TXByteRate="0.0" RXPacketRate="0.0" RXByteRate="0.0" EarliestPacketID="1" EarliestPacketCreationTime="2021-10-25 14:02:04.060701" EarliestPacketDataStartTime="2021-10-25 14:02:04.060115" EarliestPacketDataEndTime="2021-10-25 14:02:04.555115" LatestPacketID="194" LatestPacketCreationTime="2021-10-26 19:16:58.812817" LatestPacketDataStartTime="2021-10-26 19:16:58.812422" LatestPacketDataEndTime="2021-10-26 19:16:59.307422"/>
	<StreamList TotalStreams="2" SelectedStreams="2">
		<Stream Name="XX_TEST_00_HNZ/MSEED" EarliestPacketID="1" EarliestPacketDataStartTime="2021-10-25 14:02:04.060115" EarliestPacketDataEndTime="2021-10-25 14:02:04.555115" LatestPacketID="194" LatestPacketDataStartTime="2021-10-26 19:16:58.812422" LatestPacketDataEndTime="2021-10-26 19:16:59.307422" DataLatency="32.6"/>
		<Stream Name="XX_TEST_SOH/JSON" EarliestPacketID="56" EarliestPacketDataStartTime="2021-10-25 18:15:19.392161" EarliestPacketDataEndTime="2021-10-25 18:15:19.392161" LatestPacketID="193" LatestPacketDataStartTime="2021-10-26 19:16:54.297198" LatestPacketDataEndTime="2021-10-26 19:16:54.297198" DataLatency="37.6"/>
	</StreamList>
</DataLink>



<?xml version="1.0" ?>
<DataLink Version="2020.075" ServerID="Localhost testing Ring Server" Capabilities="DLPROTO:1.0 PACKETSIZE:512 WRITE">
	<Status StartTime="2021-10-25 18:59:25" RingVersion="1" RingSize="1048576" PacketSize="512" MaximumPacketID="16777215" MaximumPackets="1633" MemoryMappedRing="FALSE" VolatileRing="FALSE" TotalConnections="1" TotalStreams="2" TXPacketRate="0.0" TXByteRate="0.0" RXPacketRate="0.0" RXByteRate="0.0" EarliestPacketID="1" EarliestPacketCreationTime="2021-10-25 14:02:04.060701" EarliestPacketDataStartTime="2021-10-25 14:02:04.060115" EarliestPacketDataEndTime="2021-10-25 14:02:04.555115" LatestPacketID="194" LatestPacketCreationTime="2021-10-26 19:16:58.812817" LatestPacketDataStartTime="2021-10-26 19:16:58.812422" LatestPacketDataEndTime="2021-10-26 19:16:59.307422"/>
	<ConnectionList TotalConnections="1" SelectedConnections="1">
		<Connection Type="DataLink" Host="localhost" IP="::1" Port="56510" ClientID="('simpleDali',):('dragrace',):(0,):python" ConnectionTime="2021-10-26 19:17:31.858551" Match="" Reject="" StreamCount="0" PacketID="0" PacketCreationTime="-" PacketDataStartTime="-" PacketDataEndTime="-" TXPacketCount="0" TXPacketRate="0.0" TXByteCount="0" TXByteRate="0.0" RXPacketCount="0" RXPacketRate="0.0" RXByteCount="0" RXByteRate="0.0" Latency="0.0" PercentLag="-"/>
	</ConnectionList>
</DataLink>


First Dali packet: PACKET XX_TEST_00_HNZ/MSEED 1 1635170524060701 1635170524060115 1635170524555115 512
Last Dali packet: PACKET XX_TEST_00_HNZ/MSEED 194 1635275818812817 1635275818812422 1635275819307422 512
Stream
Got Dali packet: PACKET XX_TEST_00_HNZ/MSEED 195 1635275855383884 1635275855383621 1635275855878621 512
    MSeed: XX.TEST.00.HNZ 2021-10-26 19:17:35.383600+00:00 2021-10-26 19:17:35.383600+00:00
Got Dali packet: PACKET XX_TEST_SOH/JSON 196 1635275858530529 1635275858530271 1635275858530271 89
    JSON: {"from": "json", "to": "you", "msg": "howdy", "when": "2021-10-26T19:17:38.530271+00:00"}^CDali task cancelled
Closing datalink
Goodbye...
```

Use control-c to quit.
