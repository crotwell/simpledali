# Simple example of sending and receiving Datalink packets

First start up a ringserver, available from:
https://github.com/iris-edu/ringserver/releases

The included `ring.conf` set up datalink on port 18000 for localhost.

`readdali.py` will open a datalink connections and
print a line or two for each packet it receives.

`sendJsonPacket.py` will create a Datalink packet containing JSON and send it.

`sendMSeedPacket.py` will create a Datalink packet containing Miniseed and send it.

The output from readdali.py will look something like:
```
python3 readdali.py
DEBUG:asyncio:Using selector: KqueueSelector
Resp: type=ID value= message=DataLink 2020.075 :: DLPROTO:1.0 PACKETSIZE:512 WRITE
Info Status: <DataLink Version="2020.075" ServerID="Localhost testing Ring Server" Capabilities="DLPROTO:1.0 PACKETSIZE:512 WRITE"><Status StartTime="2021-10-25 18:59:25" RingVersion="1" RingSize="1048576" PacketSize="512" MaximumPacketID="16777215" MaximumPackets="1633" MemoryMappedRing="FALSE" VolatileRing="FALSE" TotalConnections="1" TotalStreams="2" TXPacketRate="0.0" TXByteRate="0.0" RXPacketRate="0.0" RXByteRate="0.0" EarliestPacketID="1" EarliestPacketCreationTime="2021-10-25 14:02:04.060701" EarliestPacketDataStartTime="2021-10-25 14:02:04.060115" EarliestPacketDataEndTime="2021-10-25 14:02:04.555115" LatestPacketID="186" LatestPacketCreationTime="2021-10-25 21:34:21.529357" LatestPacketDataStartTime="2021-10-25 21:34:21.528639" LatestPacketDataEndTime="2021-10-25 21:34:21.528639" /><ServerThreads TotalServerThreads="2"><Thread Flags=" ACTIVE" Type="IPv4: DataLink SeedLink HTTP" Port="18000" /><Thread Flags=" ACTIVE" Type="IPv6: DataLink SeedLink HTTP" Port="18000" /></ServerThreads></DataLink>
Info Streams: <DataLink Version="2020.075" ServerID="Localhost testing Ring Server" Capabilities="DLPROTO:1.0 PACKETSIZE:512 WRITE"><Status StartTime="2021-10-25 18:59:25" RingVersion="1" RingSize="1048576" PacketSize="512" MaximumPacketID="16777215" MaximumPackets="1633" MemoryMappedRing="FALSE" VolatileRing="FALSE" TotalConnections="1" TotalStreams="2" TXPacketRate="0.0" TXByteRate="0.0" RXPacketRate="0.0" RXByteRate="0.0" EarliestPacketID="1" EarliestPacketCreationTime="2021-10-25 14:02:04.060701" EarliestPacketDataStartTime="2021-10-25 14:02:04.060115" EarliestPacketDataEndTime="2021-10-25 14:02:04.555115" LatestPacketID="186" LatestPacketCreationTime="2021-10-25 21:34:21.529357" LatestPacketDataStartTime="2021-10-25 21:34:21.528639" LatestPacketDataEndTime="2021-10-25 21:34:21.528639" /><StreamList TotalStreams="2" SelectedStreams="2"><Stream Name="XX_TEST_00_HNZ/MSEED" EarliestPacketID="1" EarliestPacketDataStartTime="2021-10-25 14:02:04.060115" EarliestPacketDataEndTime="2021-10-25 14:02:04.555115" LatestPacketID="183" LatestPacketDataStartTime="2021-10-25 21:33:59.743608" LatestPacketDataEndTime="2021-10-25 21:34:00.238608" DataLatency="199.5" /><Stream Name="XX_TEST_SOH/JSON" EarliestPacketID="56" EarliestPacketDataStartTime="2021-10-25 18:15:19.392161" EarliestPacketDataEndTime="2021-10-25 18:15:19.392161" LatestPacketID="186" LatestPacketDataStartTime="2021-10-25 21:34:21.528639" LatestPacketDataEndTime="2021-10-25 21:34:21.528639" DataLatency="178.2" /></StreamList></DataLink>
First Dali packet: PACKET XX_TEST_00_HNZ/MSEED 1 1635170524060701 1635170524060115 1635170524555115 512
Last Dali packet: PACKET XX_TEST_SOH/JSON 186 1635197661529357 1635197661528639 1635197661528639 89
Stream
Got Dali packet: PACKET XX_TEST_00_HNZ/MSEED 187 1635197902629344 1635197902628971 1635197903123971 512
    MSeed: XX.TEST.00.HNZ 2021-10-25 21:38:22.628900+00:00 2021-10-25 21:38:22.628900+00:00
Got Dali packet: PACKET XX_TEST_SOH/JSON 188 1635197907632964 1635197907632763 1635197907632763 89
    JSON: {"from": "json", "to": "you", "msg": "howdy", "when": "2021-10-25T21:38:27.632763+00:00"}
^CDali task cancelled
Closing datalink
Goodbye...
```

Use control-c to quit.
