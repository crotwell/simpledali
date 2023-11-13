import struct
from array import array
from collections import namedtuple
from datetime import datetime, timedelta, timezone
import math
import sys

from .miniseed import MiniseedException
from .seedcodec import decompress, STEIM1, STEIM2


MINISEED_THREE_MIME = "application/vnd.fdsn.mseed3"

# const for unknown data version, 0 */
UNKNOWN_DATA_VERSION = 0

# const for offset to crc in record, 28 */
CRC_OFFSET = 28

# const for size of fixed header part of record, 40 */
FIXED_HEADER_SIZE = 40

# const for fdsn prefix for extra headers, FDSN */
FDSN_PREFIX = "FDSN"

# const for little endian, true */
#LITTLE_ENDIAN = True
ENDIAN = "<"

# const for big endian, false */
#BIG_ENDIAN = False;


BIG_ENDIAN = 1
LITTLE_ENDIAN = 0

HEADER_PACK_FORMAT = "<ccBBIHHBBBBdIIBBHI"

class MSeed3Header:
    recordIndicator: str;
    formatVersion: int;
    flags: int;
    nanosecond: int;
    year: int;
    dayOfYear: int;
    hour: int;
    minute: int;
    second: int;
    encoding: int;
    sampleRatePeriod: float;
    numSamples: int;
    crc: int;
    publicationVersion: int;
    identifierLength: int;
    extraHeadersLength: int;
    identifier: str;
    extraHeaders: str;
    dataLength: int;
    def __init__(self):
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
        self.encoding = 3; # 32 bit ints

        self.sampleRatePeriod = 1;
        self.numSamples = 0;
        self.crc = 0;
        self.publicationVersion = UNKNOWN_DATA_VERSION;
        self.identifierLength = 0;
        self.extraHeadersLength = 2;
        self.identifier = "";
        self.extraHeaders = {};
        self.dataLength = 0;

    def crcAsHex(self):
        return "0x{:08X}".format(self.crc)
    def sampleRate(self):
        return self.sampleRatePeriod if self.sampleRatePeriod > 0 else -1/self.sampleRatePeriod

    def pack(self):
        header = bytearray(FIXED_HEADER_SIZE)
        struct.pack_into(
            HEADER_PACK_FORMAT,
            header,
            'M', 'S', 3,
            self.flags,
            self.nanosecond,
            self.year,
            self.dayOfYear,
            self.hour,
            self.minute,
            self.second,
            self.encoding,
            self.sampleRatePeriod,
            self.numSamples,
            self.crc,
            self.publicationVersion,
            self.identifierLength,
            self.extraHeadersLength,
            self.dataLength
        )
        return header

    def recordSize(self):
        return FIXED_HEADER_SIZE+self.identifierLength+self.extraHeadersLength+self.dataLength

    @property
    def starttime(self):
        st = datetime.datetime(self.year, 1, 1,
                               hour=self.hour, minute=self.minute,second=self.second,
                               microsecond=self.nanosecond/1000,
                               tzinfo=timezone.utc)
        doy = datetime.timedelta(days=self.dayofyear)
        return st+doy


    @starttime.setter
    def starttime(self, stime):
        if type(stime).__name__ == "datetime":
            # make sure timezone aware
            st = None
            if not stime.tzinfo:
                st = stime.replace(tzinfo=timezone.utc)
            else:
                st = stime.astimezone(timezone.utc)
            tt = st.timetuple()
            self.year = tt.tm_year
            self.dayOfYear = tt.tm_yday
            self.hour = tt.tm_hour
            self.minute = tt.tm_min
            self.second = tt.tm_sec
            self.nanosecond = st.microsecond * 1000

        elif type(stime).__name__ == "str":
            fixTZ = stime.replace("Z", "+00:00")
            self.setStartTime(datetime.fromisoformat(fixTZ))
        else:
            raise MiniseedException(f"unknown type of starttime {type(stime)}")


class Mseed3Record:
    def __init__(self, header, encodedData):
        self.header = header
        self.encodedData=encodedData

    def decompress(self):
        data = None
        if self.encodedData is not None:
            data = decompressEncodedData(self.header.encoding, self.header.numSamples, self.encodedData)
        return data

    def starttime(self):
        return self.header.starttime

    def endtime(self):
        return self.starttime + self.header.sampPeriod * (self.header.numSamples - 1)

    def clone(self):
        return unpackMiniseedRecord(self.pack())

    def pack(self):
        rec_size = FIXED_HEADER_SIZE+self.header.identifierLength+self.header.extraHeadersLength+self.header.dataLength

        recordBytes = bytearray(self.header.recordSize())
        recordBytes[0:FIXED_HEADER_SIZE] = self.header.pack()
        offset = FIXED_HEADER_SIZE
        recordBytes[offset:offset+self.header.identifierLength] = self.header.identifier.encode("UTF-8")
        offset += self.header.identifierLength
        recordBytes[offset:offset+self.header.extraHeadersLength] = self.header.extraHeaders.encode("UTF-8")
        offset += self.header.extraHeadersLength
        recordBytes[offset:offset+self.header.dataLength] = self.encodedData
        return recordBytes

    def __str__(self):
        return f"{self.header.identifier} {self.starttime()} {self.endtime()}"


def unpackMSeed3Header(recordBytes, endianChar=">"):
    if len(recordBytes) < FIXED_HEADER_SIZE:
        raise MiniseedException("Not enough bytes for header: {:d}".format(len(recordBytes)))
    ms3header = MSeed3Header()

    (
        recordIndicatorM,recordIndicatorS,
        formatVersion,
        ms3header.flags,
        ms3header.nanosecond,
        ms3header.year,
        ms3header.dayOfYear,
        ms3header.hour,
        ms3header.minute,
        ms3header.second,
        ms3header.encoding,
        ms3header.sampleRatePeriod,
        ms3header.numSamples,
        ms3header.crc,
        ms3header.publicationVersion,
        ms3header.identifierLength,
        ms3header.extraHeadersLength,
        ms3header.dataLength
    ) = struct.unpack(HEADER_PACK_FORMAT, recordBytes[0:FIXED_HEADER_SIZE])
    if recordIndicatorM != b'M' or recordIndicatorS != b'S':
        raise MiniseedException(f"expected record start to be MS but was {recordIndicatorM}{recordIndicatorS}")
    offset = FIXED_HEADER_SIZE
    ms3header.identifier = recordBytes[offset:offset+ms3header.identifierLength].decode("utf-8")
    offset += ms3header.identifierLength
    ms3header.extraHeaders = recordBytes[offset:offset+ms3header.extraHeadersLength].decode("utf-8")
    offset += ms3header.extraHeadersLength
    return ms3header

def unpackMSeed3Record(recordBytes):
    ms3header = unpackMSeed3Header(recordBytes)
    offset = FIXED_HEADER_SIZE  + ms3header.identifierLength + ms3header.extraHeadersLength
    encodedData = recordBytes[offset:offset+ms3header.dataLength]
    return Mseed3Record(ms3header, encodedData=encodedData )


def decompressEncodedData(encoding, numsamples, recordBytes):
    byteOrder = LITTLE_ENDIAN
    if (encoding == STEIM1 or encoding == STEIM2):
        byteOrder = BIG_ENDIAN
    needSwap = (byteOrder == BIG_ENDIAN and sys.byteorder == "little") or (
                byteOrder == LITTLE_ENDIAN and sys.byteorder == "big")

    data = decompress(encoding, recordBytes, numsamples, byteOrder == LITTLE_ENDIAN)
    return data
