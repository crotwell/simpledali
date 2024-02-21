#!/usr/bin/env python3
#
import array
import json
array.array('i')
from simpledali import MSeed3Header, Mseed3Record
import simpledali
import struct
output_file = 'output.mseed'


def crcAsHex(crc):
    return "0x{:08X}".format(crc)

eh = {
        "bag": {
            "y": {
                "proc": "raw",
                "si": "count"
            },
            "st": {
                "la": 34.65,
                "lo": -80.46
           },
           "ev": {
               "origin": {
                   "time": "2024-02-06T11:30:03Z",
                   "la": 34.17,
                   "lo": -80.70,
                   "dp": 1.68,
               },
               "mag": {
                   "val": 1.74,
                   "type": "md"
               }
            }
        }
    }


data = array.array('i',( (i%99-49) for i in range(0,1000) ))
#data = [(i%99-49) for i in range(0,1000)]
header = simpledali.MSeed3Header()
header.starttime = "2024-01-01T15:13:55.123456Z"
identifier = "FDSN:XX_FAKE__H_H_Z"
header.encoding = simpledali.seedcodec.INTEGER
header.sampleRatePeriod = 40
header.numSamples = len(data)
encodedData = simpledali.compress(header.encoding, data).dataView
header.dataLength = len(encodedData)
ms3record = simpledali.Mseed3Record(header, identifier, encodedData, extraHeaders=eh)

ms3filename = "test.ms3"
with open(ms3filename, "wb") as of:
    of.write(ms3record.pack())
    print(f"  save: {ms3record.details()} ")
    print(f"    to: {ms3filename} ")
    print(f"   crc: {crcAsHex(ms3record.header.crc)}")

print()
print()
with open(ms3filename, "rb") as infile:
    readms3record = simpledali.readMSeed3Record(infile)
    print(f"  extract: {readms3record.details()} ")
    print(f"     from: {ms3filename} ")
    print(f"      crc: {crcAsHex(readms3record.header.crc)}")
