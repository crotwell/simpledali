import struct
from array import array
from collections import namedtuple
from datetime import datetime, timedelta, timezone
import json
import math
import sys
import crc32c

from .miniseed import MiniseedException
from .seedcodec import (
    decompress,
    compress,
    STEIM1, STEIM2,
    EncodedDataSegment
    )


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
    extraHeadersStr: str;
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
        self.extraHeadersStr = "{}";
        self.dataLength = 0;

    def crcAsHex(self):
        return "0x{:08X}".format(self.crc)
    @property
    def sampleRate(self):
        return self.sampleRatePeriod if self.sampleRatePeriod > 0 else -1.0/self.sampleRatePeriod
    @property
    def samplePeriod(self):
        return -1*self.sampleRatePeriod if self.sampleRatePeriod < 0 else 1.0/self.sampleRatePeriod

    def pack(self):
        header = bytearray(FIXED_HEADER_SIZE)
        OFFSET=0
        struct.pack_into(
            HEADER_PACK_FORMAT,
            header,
            OFFSET,
            b'M', b'S', 3,
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
        st = datetime(self.year, 1, 1,
                       hour=self.hour, minute=self.minute,second=self.second,
                       microsecond=int(self.nanosecond/1000),
                       tzinfo=timezone.utc)
        doy = timedelta(days=self.dayOfYear)
        return st+doy


    @starttime.setter
    def starttime(self, stime):
        dt = None
        if type(stime).__name__ == "datetime":
            dt = stime
        elif type(stime).__name__ == "str":
            fixTZ = stime.replace("Z", "+00:00")
            dt = datetime.fromisoformat(fixTZ)
        else:
            raise MiniseedException(f"unknown type of starttime {type(stime)}")

        # make sure timezone aware
        st = None
        if not dt.tzinfo:
            st = dt.replace(tzinfo=timezone.utc)
        else:
            st = dt.astimezone(timezone.utc)
        tt = st.timetuple()
        self.year = tt.tm_year
        self.dayOfYear = tt.tm_yday
        self.hour = tt.tm_hour
        self.minute = tt.tm_min
        self.second = tt.tm_sec
        self.nanosecond = st.microsecond * 1000

    @property
    def endtime(self):
        return self.starttime + timedelta(seconds=self.samplePeriod * (self.numSamples - 1))


class Mseed3Record:
    def __init__(self, header, identifier, data, extraHeaders=None):
        self.header = header
        self._eh = extraHeaders
        self.identifier = identifier
        if isinstance(data, EncodedDataSegment):
            self.encodedData=data
        elif isinstance(data, bytes) or isinstance(data, bytearray):
            self.encodedData = EncodedDataSegment(header.encoding,
                                           data,
                                           header.numSamples,
                                           True),
        else:
            # try to compress with given type?
            self.encodedData = compress(self.header.encoding, data)
        # header encoding from actual data, consistency
        self.header.encoding = self.encodedData.compressionType
        self.header.numSamples = self.encodedData.numSamples

    @property
    def eh(self):
        if self._eh is not None and isinstance(self._eh, str):
            self._eh = json.loads(self._eh)
        return self._eh

    @eh.setter
    def eh(self, ehDict):
        self._eh = ehDict

    @eh.deleter
    def eh(self):
        del self._eh


    def decompress(self):
        data = None
        if self.encodedData is not None:
            data = decompressEncodedData(self.header.encoding, self.header.numSamples, self.encodedData.dataBytes)
        return data

    @property
    def starttime(self):
        return self.header.starttime

    @property
    def endtime(self):
        return self.header.endtime

    def clone(self):
        return unpackMiniseedRecord(self.pack())

    def getSize(self):
        return FIXED_HEADER_SIZE+self.header.identifierLength+self.header.extraHeadersLength+self.header.dataLength


    def pack(self):
        self.header.crc = 0
        # string to bytes
        identifierBytes = self.identifier.encode("UTF-8")
        self.header.identifierLength = len(identifierBytes)
        if self._eh is not None:
            extraHeadersStr = ""
        elif isinstance(self._eh, dict):
            extraHeadersStr = json.dumps(self._eh)
        elif isinstance(self._eh, str):
            extraHeadersStr = self._eh
        else:
            extraHeadersStr = ""
        extraHeadersBytes = extraHeadersStr.encode("UTF-8")
        self.header.extraHeadersLength = len(extraHeadersBytes)
        self.header.dataLength = len(self.encodedData.dataBytes)
        rec_size = FIXED_HEADER_SIZE+self.header.identifierLength+self.header.extraHeadersLength+self.header.dataLength

        recordBytes = bytearray(rec_size)
        recordBytes[0:FIXED_HEADER_SIZE] = self.header.pack()
        offset = FIXED_HEADER_SIZE
        recordBytes[offset:offset+self.header.identifierLength] = identifierBytes
        offset += self.header.identifierLength
        recordBytes[offset:offset+self.header.extraHeadersLength] = extraHeadersBytes
        offset += self.header.extraHeadersLength
        recordBytes[offset:offset+self.header.dataLength] = self.encodedData.dataBytes

        struct.pack_into("<I", recordBytes, CRC_OFFSET, 0);
        crc = crc32c.crc32c(recordBytes)
        struct.pack_into("<I", recordBytes, CRC_OFFSET, crc);
        return recordBytes

    def __str__(self):
        return f"{self.identifier} {self.header.starttime} {self.header.endtime}"

    def encodingName(self):
        encode_name = f"unknown ({self.header.encoding})"
        if self.header.encoding == 0:
          encode_name = "Text"
        elif self.header.encoding == 1:
            encode_name = "16-bit integer"
        elif self.header.encoding == 3:
            encode_name = "32-bit integer"
        elif self.header.encoding == 4:
            encode_name = "32-bit floats"
        elif self.header.encoding == 5:
            encode_name = "64-bit floats"
        elif self.header.encoding == 11:
            encode_name = "STEIM-2 integer compression"
        elif self.header.encoding == 10:
            encode_name = "STEIM-1 integer compression"
        elif self.header.encoding == 19:
            encode_name = "STEIM-3 integer compression"
        elif self.header.encoding == 100:
            encode_name = "Opaque data"
        return encode_name

    def details(self):

        encode_name = self.encodingName()

        bitFlagStr = ""
        if (self.header.flags & 0x01):
          bitFlagStr = f"""{bitFlagStr}
                             [Bit 0] Calibration signals present"""
        if (self.header.flags & 0x02):
          bitFlagStr = f"""{bitFlagStr}
                             [Bit 1] Time tag is questionable"""
        if (self.header.flags & 0x04):
          bitFlagStr = f"""{bitFlagStr}
                             [Bit 2] Clock locked"""
        if (self.header.flags & 0x08):
          bitFlagStr = f"""{bitFlagStr}
                             [Bit 3] Undefined bit set"""
        if (self.header.flags & 0x10):
          bitFlagStr = f"""{bitFlagStr}
                             [Bit 4] Undefined bit set"""
        if (self.header.flags & 0x20):
          bitFlagStr = f"""{bitFlagStr}
                             [Bit 5] Undefined bit set"""
        if (self.header.flags & 0x40):
          bitFlagStr = f"""{bitFlagStr}
                             [Bit 6] Undefined bit set"""
        if (self.header.flags & 0x80):
          bitFlagStr = f"""{bitFlagStr}
                             [Bit 7] Undefined bit set"""
        ehLines = json.dumps(self.eh, indent=2).split("\n")
        indentLines = "\n          ".join(ehLines);
        return f"""
          {self.identifier}, version {self.header.publicationVersion}, {self.getSize() + self.header.dataLength + self.header.extraHeadersLength} bytes (format: {self.header.formatVersion})
                       start time: {self.starttime} ({self.header.dayOfYear:03})
                number of samples: {self.header.numSamples}
                 sample rate (Hz): {self.header.sampleRate}
                            flags: [{self.header.flags:>08b}] 8 bits${bitFlagStr}
                              CRC: {crcAsHex(self.header.crc)}
              extra header length: {self.header.extraHeadersLength} bytes
              data payload length: {self.header.dataLength} bytes
                 payload encoding: {encode_name} (val: {self.header.encoding})
                    extra headers: {indentLines}
"""

def unpackMSeed3FixedHeader(recordBytes):
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
    return ms3header

def unpackMSeed3Record(recordBytes, check_crc=True):
    crc = 0
    ms3header = unpackMSeed3FixedHeader(recordBytes)
    if check_crc:
        tempBytes = bytearray(recordBytes[:FIXED_HEADER_SIZE])
        struct.pack_into("<I", tempBytes, CRC_OFFSET, 0);
        crc = crc32c.crc32c(tempBytes)
    offset = FIXED_HEADER_SIZE
    idBytes = recordBytes[offset:offset+ms3header.identifierLength]
    if check_crc:
        crc = crc32c.crc32c(idBytes, crc)
    identifier = idBytes.decode("utf-8")
    offset += ms3header.identifierLength
    ehBytes = recordBytes[offset:offset+ms3header.extraHeadersLength]
    if check_crc:
        crc = crc32c.crc32c(ehBytes, crc)
    extraHeadersStr = ehBytes.decode("utf-8")
    offset += ms3header.extraHeadersLength

    encodedDataBytes = recordBytes[offset:offset+ms3header.dataLength]
    if check_crc:
        crc = crc32c.crc32c(encodedDataBytes, crc)
    offset += ms3header.dataLength
    if check_crc and ms3header.crc != crc:
        raise MiniseedException(f"crc fail:  Calc: {crc}  Header: {ms3header.crc}")
    encodedData=EncodedDataSegment(ms3header.encoding,
                                   encodedDataBytes,
                                   ms3header.numSamples,
                                   True)
    ms3Rec = Mseed3Record(ms3header,
                          identifier,
                          encodedData,
                          extraHeaders=extraHeadersStr )
    return ms3Rec

def nextMSeed3Record(fileptr, check_crc=True):
    headBytes = fileptr.read(FIXED_HEADER_SIZE)
    ms3header = unpackMSeed3FixedHeader(headBytes)
    crc = 0
    if check_crc:
        crcHeadBytes = bytearray(headBytes)
        struct.pack_into("<I", crcHeadBytes, CRC_OFFSET, 0);
        crc = crc32c.crc32c(crcHeadBytes)
    identifierBytes = fileptr.read(ms3header.identifierLength)
    crc = crc32c.crc32c(identifierBytes, crc)
    identifier = identifierBytes.decode("utf-8")
    ehBytes = fileptr.read(ms3header.extraHeadersLength)
    crc = crc32c.crc32c(ehBytes, crc)
    extraHeadersStr = ehBytes.decode("utf-8")
    encodedDataBytes = fileptr.read(ms3header.dataLength)
    crc = crc32c.crc32c(encodedDataBytes, crc)
    if check_crc and ms3header.crc != crc:
        raise MiniseedException(f"crc fail:  Calc: {crc}  Header: {ms3header.crc}")

    encodedData=EncodedDataSegment(ms3header.encoding,
                                   encodedDataBytes,
                                   ms3header.numSamples,
                                   True)
    return Mseed3Record(ms3header, identifier, encodedData, extraHeaders=extraHeadersStr )


def decompressEncodedData(encoding, numSamples, recordBytes):
    byteOrder = LITTLE_ENDIAN
    if (encoding == STEIM1 or encoding == STEIM2):
        byteOrder = BIG_ENDIAN
    needSwap = (byteOrder == BIG_ENDIAN and sys.byteorder == "little") or (
                byteOrder == LITTLE_ENDIAN and sys.byteorder == "big")
    data = decompress(encoding, recordBytes, numSamples, byteOrder == LITTLE_ENDIAN)
    return data

def crcAsHex(crc):
    return "0x{:08X}".format(crc)
