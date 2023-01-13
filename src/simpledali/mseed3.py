import struct
from array import array
from collections import namedtuple
from datetime import datetime, timedelta, timezone
import math
import sys


MICRO = 1000000

EMPTY_SEQ = "      ".encode("UTF-8")
ENC_SHORT = 1
ENC_INT = 3

BIG_ENDIAN = 1
LITTLE_ENDIAN = 0

HEADER_SIZE = 48
B1000_SIZE = 8
MAX_INT_PER_512 = (512 - HEADER_SIZE - B1000_SIZE) // 4
MAX_SHORT_PER_512 = (512 - HEADER_SIZE - B1000_SIZE) // 2

MINISEED_THREE_MIME = "application/vnd.fdsn.mseed3";

# const for unknown data version, 0 */
UNKNOWN_DATA_VERSION = 0;

# const for offset to crc in record, 28 */
CRC_OFFSET = 28;

# const for size of fixed header part of record, 40 */
FIXED_HEADER_SIZE = 40;

# const for fdsn prefix for extra headers, FDSN */
FDSN_PREFIX = "FDSN";

# const for little endian, true */
LITTLE_ENDIAN = true;

# const for big endian, false */
BIG_ENDIAN = false;


class MSeed3Header:
    def __init__(
        self,
        sourceId,
        starttime,
        numsamples,
        sampleRate,
        encoding=ENC_INT,
        byteorder=BIG_ENDIAN,
        sampRateFactor=0,
        sampRateMult=0,
        actFlag=0,
        ioFlag=0,
        qualFlag=0,
        numBlockettes=0,
        timeCorr=0,
        dataOffset=0,
        blocketteOffset=0,
    ):
        # empty construction
        self.recordIndicator = "MS";
        self.formatVersion = 3;
        self.flags = 0;
        self.nanosecond = 0;
        self.year = 1970;
        self.dayOfYear = 1;
        self.hour = 0;
        self.minute = 0;
        self.second = 0;
        self.encoding = 3; // 32 bit ints

        self.sampleRatePeriod = 1;
        self.numSamples = 0;
        self.crc = 0;
        self.publicationVersion = UNKNOWN_DATA_VERSION;
        self.identifierLength = 0;
        self.extraHeadersLength = 2;
        self.identifier = "";
        self.extraHeaders = {};
        self.dataLength = 0;
        self.setStartTime(starttime)  # Record start time, corrected (first sample) */

    def pack(self):
        header = bytearray(48)
        net = self.network.ljust(2).encode("UTF-8")
        sta = self.station.ljust(5).encode("UTF-8")
        loc = self.location.ljust(2).encode("UTF-8")
        chan = self.channel.ljust(3).encode("UTF-8")
        struct.pack_into(
            self.endianChar + "6scc5s2s3s2s",
            header,
            0,
            EMPTY_SEQ,
            b"D",
            b" ",
            sta,
            loc,
            chan,
            net,
        )
        self.packBTime(header, self.starttime)
        tempsampRateFactor = self.sampRateFactor
        tempsampRateMult = self.sampRateMult
        if self.sampleRate != 0 and self.sampRateFactor == 0 and self.sampRateMult == 0:
            tempsampRateFactor, tempsampRateMult = self.calcSeedMultipilerFactor()
        struct.pack_into(
            self.endianChar + "Hhh",
            header,
            30,
            self.numsamples,
            tempsampRateFactor,
            tempsampRateMult,
        )
        return header


    def setStartTime(self, starttime):
        if type(starttime).__name__ == "datetime":
            # make sure timezone aware
            if not starttime.tzinfo:
                self.starttime = starttime.replace(tzinfo=timezone.utc)
            else:
                self.starttime = starttime.astimezone(timezone.utc)
            tt = self.starttime.timetuple()
            self.year = tt.tm_year
            self.dayOfYear = tt.tm_yday
            self.hour = tt.tm_hour
            self.minute = tt.tm_min
            self.second = tt.tm_sec
            self.nanosecond = starttime.microsecond * 1000
            )
        elif type(starttime).__name__ == "str":
            fixTZ = starttime.replace("Z", "+00:00")
            self.setStartTime(datetime.fromisoformat(fixTZ))
        else:
            raise MiniseedException(f"unknown type of starttime {type(starttime)}")


class Mseed3Record:
    def __init__(self, header, data, encodedData=None):
        self.header = header
        self.__data = data
        self.encodedData=encodedData

    def decompressed(self):
        if self.__data is not None:
            return self.__data
        elif self.encodedData is not None:
            self.__data = decompressEncodedData(self.header.encoding, self.header.byteorder, self.header.numsamples, self.encodedData)
        return self.__data

    def starttime(self):
        return self.header.starttime

    def endtime(self):
        return self.starttime() + self.header.sampPeriod * (self.header.numsamples - 1)

    def clone(self):
        return unpackMiniseedRecord(self.pack())

    def pack(self):
        recordBytes = bytearray(self.header.recordLength)
        recordBytes[0:48] = self.header.pack()

        offset = 48
        struct.pack_into(self.header.endianChar + "H", recordBytes, 46, offset)
        if len(self.blockettes) == 0:
            recordBytes[39] = 1  #  one blockette, b1000
            offset = self.packB1000(recordBytes, offset, self.createB1000())
        else:
            recordBytes[39] = len(self.blockettes)
            for b in self.blockettes:
                offset = self.packBlockette(recordBytes, offset, b)
        # set offset to data in header
        # if offset < 64:
        #    offset = 64
        struct.pack_into(self.header.endianChar + "H", recordBytes, 44, offset)
        self.packData(recordBytes, offset, self.__data)
        return recordBytes

    def packBlockette(self, recordBytes, offset, b):
        if type(b).__name__ == "Blockette1000":
            return self.packB1000(recordBytes, offset, b)
        elif type(b).__name__ == "BlocketteUnknown":
            return self.packBlocketteUnknown(recordBytes, offset, b)

    def packBlocketteUnknown(self, recordBytes, offset, bUnk):
        struct.pack_into(
            self.header.endianChar + "HH",
            recordBytes,
            offset,
            bUnk.blocketteNum,
            offset + len(bUnk.rawBytes),
        )
        recordBytes[offset + 4 : offset + len(bUnk.rawBytes) - 4] = bUnk.rawBytes[4:]
        return offset + len(bUnk.rawBytes)

    def packB1000(self, recordBytes, offset, b):
        struct.pack_into(
            self.header.endianChar + "HHBBBx",
            recordBytes,
            offset,
            b.blocketteNum,
            b.nextOffset,
            self.header.encoding,
            self.header.byteorder,
            self.header.recordLengthExp,
        )
        return offset + 8

    def createB1000(self):
        return Blockette1000(
            1000,
            0,
            self.header.encoding,
            self.header.byteorder,
            self.header.recordLengthExp,
        )

    def packData(self, recordBytes, offset, data):
        if self.header.encoding == ENC_SHORT:
            if len(recordBytes) < offset + 2 * len(data):
                raise MiniseedException(
                    "not enough bytes in record to fit data: byte:{:d} offset: {:d} len(data): {:d}  enc:{:d}".format(
                        len(recordBytes), offset, len(data), self.header.encoding
                    )
                )
            for d in data:
                struct.pack_into(self.header.endianChar + "h", recordBytes, offset, d)
                # record[offset:offset+4] = d.to_bytes(4, byteorder='big')
                offset += 2
        elif self.header.encoding == ENC_INT:
            if len(recordBytes) < offset + 4 * len(data):
                raise MiniseedException(
                    "not enough bytes in record to fit data: byte:{:d} offset: {:d} len(data): {:d}  enc:{:d}".format(
                        len(recordBytes), offset, len(data), self.header.encoding
                    )
                )
            for d in data:
                struct.pack_into(self.header.endianChar + "i", recordBytes, offset, d)
                offset += 4
        else:
            raise MiniseedException(
                "Encoding type {} not supported.".format(self.header.encoding)
            )

    def __str__(self):
        return f"{self.codes()} {self.starttime()} {self.endtime()}"


def unpackMiniseedHeader(recordBytes, endianChar=">"):
    if len(recordBytes) < 48:
        raise MiniseedException("Not enough bytes for header: {:d}".format(len(recordBytes)))
    (
        seq,
        qualityChar,
        reserved,
        sta,
        loc,
        chan,
        net,
        year,
        yday,
        hour,
        min,
        sec,
        tenthMilli,
        numsamples,
        sampRateFactor,
        sampRateMult,
        actFlag,
        ioFlag,
        qualFlag,
        numBlockettes,
        timeCorr,
        dataOffset,
        blocketteOffset,
    ) = struct.unpack(endianChar + "6scc5s2s3s2sHHBBBxHHHHBBBBiHH", recordBytes[0:48])
    if endianChar == ">":
        byteorder = BIG_ENDIAN
    else:
        byteorder = LITTLE_ENDIAN
    net = net.decode("utf-8").strip()
    sta = sta.decode("utf-8").strip()
    loc = loc.decode("utf-8").strip()
    chan = chan.decode("utf-8").strip()
    starttime = BTime(year, yday, hour, min, sec, tenthMilli)
    sampleRate = 0  # recalc in constructor
    encoding = -1  # reset on read b1000
    return MiniseedHeader(
        net,
        sta,
        loc,
        chan,
        starttime,
        numsamples,
        sampleRate,
        encoding=encoding,
        byteorder=byteorder,
        sampRateFactor=sampRateFactor,
        sampRateMult=sampRateMult,
        actFlag=actFlag,
        ioFlag=ioFlag,
        qualFlag=qualFlag,
        numBlockettes=numBlockettes,
        timeCorr=timeCorr,
        dataOffset=dataOffset,
        blocketteOffset=blocketteOffset,
    )


def unpackBlockette(recordBytes, offset, endianChar):
    blocketteNum, nextOffset = struct.unpack(
        endianChar + "HH", recordBytes[offset : offset + 4]
    )
    #  I do not think I should have to convert to int, but it did not work if I did not convert -- tjo
    bnum = int(blocketteNum)
    #    print ("Blockette Number in unpackBlockette:", blocketteNum," ",bnum)
    if bnum == 1000:
        return unpackBlockette1000(recordBytes, offset, endianChar)
    else:
        return BlocketteUnknown(
            blocketteNum, nextOffset, recordBytes[offset:nextOffset]
        )


def unpackBlockette1000(recordBytes, offset, endianChar):
    """named Tuple of blocketteNum, nextOffset, encoding, byteorder, recLength"""
    blocketteNum, nextOffset, encoding, byteorder, recLength = struct.unpack(
        endianChar + "HHBBBx", recordBytes[offset : offset + 8]
    )
    return Blockette1000(blocketteNum, nextOffset, encoding, byteorder, recLength)


def unpackMiniseedRecord(recordBytes):
    byteOrder = BIG_ENDIAN
    endianChar = ">"
    # 0x0708 = 1800 and 0x0807 = 2055
    if (
        recordBytes[20] == 7
        or recordBytes[20] == 8
        and not (recordBytes[21] == 7 or recordBytes[21] == 8)
    ):
        # print("big endian {:d} {:d}".format(recordBytes[20], recordBytes[21]))
        byteOrder = BIG_ENDIAN
        endianChar = ">"
    elif (recordBytes[21] == 7 or recordBytes[21] == 8) and not (
        recordBytes[20] == 7 or recordBytes[20] == 8
    ):
        # print("little endian {:d} {:d}".format(recordBytes[20], recordBytes[21]))
        byteOrder = LITTLE_ENDIAN
        endianChar = "<"
    else:
        raise MiniseedException(
            "unable to determine byte order from year bytes: {:d} {:d}".format(
                recordBytes[21], recordBytes[22]
            )
        )
    header = unpackMiniseedHeader(recordBytes, endianChar)
    header.byteOrder = byteOrder # in case no b1000
    blockettes = []
    if header.numBlockettes > 0:
        nextBOffset = header.blocketteOffset
        # print("Next Byte Offset",nextBOffset)
        while nextBOffset > 0:
            try:
                b = unpackBlockette(recordBytes, nextBOffset, endianChar)
                blockettes.append(b)
                if type(b).__name__ == "Blockette1000":
                    header.encoding = b.encoding
                    header.byteOrder = b.byteorder
                nextBOffset = b.nextOffset
            except struct.error as e:
                print(
                    "Unable to unpack blockette, fail codes: {} start: {} {}".format(
                        header.codes(), header.starttime, e
                    )
                )
                raise
    encodedData = recordBytes[header.dataOffset : ]
    if header.encoding == ENC_SHORT or header.encoding == ENC_INT:
        data = decompressEncodedData(header.encoding, header.byteOrder, header.numsamples, encodedData)
    else:
        data = None
    return MiniseedRecord(header, data, encodedData=encodedData, blockettes=blockettes)

def decompressEncodedData(encoding, byteOrder, numsamples, recordBytes):
        if encoding == ENC_SHORT:
            data = array("h", recordBytes[ : 2 * numsamples],)
        elif encoding == ENC_INT:
            data = array("i", recordBytes[ : 4 * numsamples],)
        else:
            data = None
        if (data is not None and
            byteOrder == BIG_ENDIAN and sys.byteorder == "little") or (
            byteOrder == LITTLE_ENDIAN and sys.byteorder == "big"
        ):
            data.byteswap()
        return data

class MiniseedException(Exception):
    pass
