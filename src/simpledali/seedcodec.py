
# Philip Crotwell
# University of South Carolina, 2019
# https://www.seis.sc.edu
#/
# converted from Steim2.java in seedCodec
# https:#github.com/crotwell/seedcodec/
# constants for compression types

from array import array
import sys
import struct

from .exception import (
    CodecException,
    UnsupportedCompressionType,
)

# ascii
ASCII: int = 0

# 16 bit integer, or java short
SHORT: int = 1

# 24 bit integer
INT24: int = 2

# 32 bit integer, or java int
INTEGER: int = 3

# ieee float
FLOAT: int = 4

# ieee double
DOUBLE: int = 5

# Steim1 compression
STEIM1: int = 10

# Steim2 compression
STEIM2: int = 11

# CDSN 16 bit gain ranged
CDSN: int = 16

# (A)SRO
SRO: int = 30

# DWWSSN 16 bit
DWWSSN: int = 32

def isFloatCompression(compressionType: int) -> bool:
  if (compressionType == FLOAT or compressionType == DOUBLE):
    return True
  return False

#
# A holder for compressed data independent of the file format.

class EncodedDataSegment:
  compressionType: int
  dataView: bytearray
  numSamples: int
  littleEndian: bool

  def __init__(self,
    compressionType,
    dataView: bytearray,
    numSamples,
    littleEndian: bool
  ):
    self.compressionType = compressionType
    self.dataView = dataView
    self.numSamples = numSamples
    self.littleEndian = littleEndian

  def isFloatCompression() -> bool:
    return isFloatCompression(self.compressionType)

  def decode():
    return decompress(
      self.compressionType,
      self.dataView,
      self.numSamples,
      self.littleEndian,
    )

def compress(compressionType, values):
    littleEndian = True
    if compressionType ==  INTEGER:
        # 32 bit integers
        compCode = 'l'
    elif compressionType ==  SHORT:
        # 16 bit integers
        compCode = 'h'
    elif compressionType ==  FLOAT32:
        # 32 bit float
        compCode = 'f'
    elif compressionType ==  FLOAT64:
        # 64 bit float/double
        compCode = 'd'
    else:
        raise UnsupportedCompressionType(f"type {compressionType} not yet supported for compression")
    dataView = struct.pack(f"<{len(values)}{compCode}", *values)

    return EncodedDataSegment(compressionType,
                                dataView,
                                len(values),
                                littleEndian)

#
#  Decompress the samples from the provided DataView and
#  return an array of the decompressed values.
#  Only 16 bit short, 32 bit int, 32 bit float and 64 bit double
#  along with Steim1 and Steim2 are supported.
#
#  @param compressionType compression format as defined in SEED blockette 1000
#  @param dataView input DataView to be decoded
#  @param numSamples the number of samples that can be decoded from array
#  <b>b</b>
#  @param littleEndian if True, dataView is little-endian (intel byte order) <b>b</b>.
#  @returns array of length <b>numSamples</b>.
#  @throws CodecException fail to decompress.
#  @throws UnsupportedCompressionType unsupported compression type

def decompress(
  compressionType: int,
  dataView: bytearray,
  numSamples: int,
  littleEndian: bool,
):

  # in case of record with no data points, ex detection blockette, which often have compression type
  # set to 0, which messes up the decompresser even though it doesn't matter since there is no data.
  if (numSamples == 0):
    return array('i', [])

  out = None
  offset = 0

  #switch (compressionType):
  if compressionType == SHORT or compressionType == DWWSSN:
      # 16 bit values
      if (len(dataView) < 2 * numSamples):
        raise CodecException(
          f"Not enough bytes for {numSamples} 16 bit data points, only {len(dataView)} bytes.",
        )

      out = array('i', [0]*numSamples)

      for i in range(numSamples):
        out[i] = getInt16(dataView, offset, littleEndian)
        offset += 2

  elif compressionType ==  INTEGER:
      # 32 bit integers
      if (len(dataView) < 4 * numSamples):
        raise CodecException(
          f"Not enough bytes for {numSamples} 32 bit data points, only {len(dataView)} bytes.",
        )

      out = array('l', [0]*numSamples)

      for i in range(numSamples):
        out[i] = getInt32(dataView, offset, littleEndian)
        offset += 4
  elif compressionType == FLOAT:
      # 32 bit floats
      if (len(dataView) < 4 * numSamples):
        raise CodecException(
          f"Not enough bytes for {numSamples} 32 bit data points, only {len(dataView)} bytes.",
        )


      out = array('f', [0]*numSamples)

      for i in range(numSamples):
        out[i] = getFloat32(dataView, offset, littleEndian)
        offset += 4

  elif compressionType == DOUBLE:
      # 64 bit doubles
      if (len(dataView) < 8 * numSamples):
        raise CodecException(
          f"Not enough bytes for {numSamples} 64 bit data points, only {len(dataView)} bytes.",
        )


      out = array('d', [0]*numSamples)

      for i in range(numSamples):
        out[i] = getFloat64(dataView, offset, littleEndian)
        offset += 8

  elif compressionType == STEIM1:
      # steim 1
      out = decodeSteim1(dataView, numSamples, littleEndian, 0)

  elif compressionType == STEIM2:
      # steim 2
      out = decodeSteim2(dataView, numSamples, littleEndian, 0)

  else:
      # unknown format????
      raise UnsupportedCompressionType(
        f"Type {compressionType} is not supported at this time, numsamples: {numSamples}.",
      )

  # end of switch ()
  return out


#
#  Decode the indicated number of samples from the provided byte array and
#  return an integer array of the decompressed values.  Being differencing
#  compression, there may be an offset carried over from a previous data
#  record.  This offset value can be placed in <b>bias</b>, otherwise leave
#  the value as 0.
#
#  @param dataView input DataView to be decoded
#  @param numSamples the number of samples that can be decoded from array
#  <b>b</b>
#  @param littleEndian if True, dataView is little-endian (intel byte order) <b>b</b>.
#  @param bias the first difference value will be computed from this value.
#  If set to 0, the method will attempt to use the X(0) constant instead.
#  @returns int array of length <b>numSamples</b>.
#  @throws CodecException - encoded data length is not multiple of 64
#  bytes.

def decodeSteim1(
  dataView: bytearray,
  numSamples,
  littleEndian: bool,
  bias,
):
  # Decode Steim1 compression format from the provided byte array, which contains numSamples number
  # of samples.  littleEndian is true for little endian byte order.  bias represents
  # a previous value which acts as a starting constant for continuing differences integration.  At the
  # very start, bias is set to 0.
  if (len(dataView) % 64 != 0):
    raise CodecException(
      f"encoded data length is not multiple of 64 bytes ({len(dataView)})",
    )


  samples = array('i', [0]*numSamples)
  numFrames = len(dataView) // 64
  current = 0
  start = 0
  firstData = 0
  lastValue = 0

  for i in range(numFrames):
    tempSamples = extractSteim1Samples(dataView, i * 64, littleEndian) # returns only differences except for frame 0

    firstData = 0 # d(0) is byte 0 by default

    if (i == 0):
      # special case for first frame
      lastValue = bias # assign our X(-1)

      # x0 and xn are in 1 and 2 spots
      start = tempSamples[1] # X(0) is byte 1 for frame 0

      #  end = tempSamples[2]    # X(n) is byte 2 for frame 0
      firstData = 3 # d(0) is byte 3 for frame 0

      # if bias was zero, then we want the first sample to be X(0) constant
      if (bias == 0):
          lastValue = start - tempSamples[3] # X(-1) = X(0) - d(0)


    for j in range(firstData, len(tempSamples)):
      if current >= numSamples:
          break
      samples[current] = lastValue + tempSamples[j] # X(n) = X(n-1) + d(n)

      lastValue = samples[current]
      current+=1



  # end for each frame...
  if (current != numSamples):
    raise CodecException(
      f"Number of samples decompressed doesn't match number in header: {current} != {numSamples}",
    )

  # ignore last sample check???
  #if (end != samples[numSamples-1]):
  #    raise SteimException("Last sample decompressed doesn't match value x(n) value in Steim1 record: "+samples[numSamples-1]+" != "+end)
  #
  return samples

def getInt16(dataView, offset, littleEndian):
    endianChar = "<" if littleEndian else ">";
    vals = struct.unpack(endianChar+ "h", dataView[offset : offset + 2])
    return vals[0]

def getInt32(dataView, offset, littleEndian):
    endianChar = "<" if littleEndian else ">";
    vals = struct.unpack(endianChar+ "l", dataView[offset : offset + 4])
    return vals[0]

def getFloat32(dataView, offset, littleEndian):
    endianChar = "<" if littleEndian else ">";
    vals = struct.unpack(endianChar+ "f", dataView[offset : offset + 4])
    return vals[0]

def getFloat64(dataView, offset, littleEndian):
    endianChar = "<" if littleEndian else ">";
    vals = struct.unpack(endianChar+ "d", dataView[offset : offset + 8])
    return vals[0]

def getUint32(dataView, offset, littleEndian):
    endianChar = "<" if littleEndian else ">";
    vals = struct.unpack(endianChar+ "I", dataView[offset : offset + 4])
    return vals[0]

#
# Extracts differences from the next 64 byte frame of the given compressed
# byte array (starting at offset) and returns those differences in an int
# array.
# An offset of 0 means that we are at the first frame, so include the header
# bytes in the returned int array...else, do not include the header bytes
# in the returned array.
#
# @param dataView byte array of compressed data differences
# @param offset index to begin reading compressed bytes for decoding
# @param littleEndian reverse the endian-ness of the compressed bytes being read
# @returns integer array of difference (and constant) values

def extractSteim1Samples(
  dataView: bytearray,
  offset: int,
  littleEndian: bool,
) -> array:
  # get nibbles
  nibbles = getUint32(dataView, offset, littleEndian)
  currNibble = 0
  temp = [] # 4 samples * 16 longwords, can't be more than 64

  currNum = 0

  for i in range(16):
    # i is the word number of the frame starting at 0
    #currNibble = (nibbles >>> (30 - i*2 ) ) & 0x03 # count from top to bottom each nibble in W(0)
    currNibble = (nibbles >> (30 - i * 2)) & 0x03 # count from top to bottom each nibble in W(0)

    # Rule appears to be:
    # only check for byte-swap on actual value-atoms, so a 32-bit word in of itself
    # is not swapped, but two 16-bit short *values* are or a single
    # 32-bit int *value* is, if the flag is set to True.  8-bit values
    # are naturally not swapped.
    # It would seem that the W(0) word is swap-checked, though, which is confusing...
    # maybe it has to do with the reference to high-order bits for c(0)
    #switch (currNibble):
    if currNibble == 0:
        #  ("0 means header info")
        # only include header info if offset is 0
        if (offset == 0):
          temp.append(getInt32(dataView, offset+ i * 4, littleEndian))
          currNum+=1
    elif currNibble ==  1:
        #  ("1 means 4 one byte differences")

        endianChar = "<" if littleEndian else ">";
        temp += struct.unpack(endianChar+ "bbbb", dataView[offset + i * 4: offset+ i * 4 + 4])
        currNum+=4

    elif currNibble ==  2:
        #  ("2 means 2 two byte differences")

        endianChar = "<" if littleEndian else ">";
        temp += struct.unpack(endianChar+ "hh", dataView[offset + i * 4: offset+ i * 4 + 4])
        currNum+=2


    elif currNibble ==  3:
        #  ("3 means 1 four byte difference")
        temp.append(getInt32(dataView, offset + i * 4, littleEndian))
        currNum+=1

    else:
        raise CodecException("unreachable case: " + currNibble)
      #  ("default")



  return temp


#
#  Decode the indicated number of samples from the provided byte array and
#  return an integer array of the decompressed values.  Being differencing
#  compression, there may be an offset carried over from a previous data
#  record.  This offset value can be placed in <b>bias</b>, otherwise leave
#  the value as 0.
#
#  @param dataView input byte array to be decoded
#  @param numSamples the number of samples that can be decoded from array
#  @param littleEndian if True, endian-ness is little
#  @param bias the first difference value will be computed from this value.
#  If set to 0, the method will attempt to use the X(0) constant instead.
#  @returns int array of length <b>numSamples</b>.
#  @throws SteimException - encoded data length is not multiple of 64
#  bytes.

def decodeSteim2(
  dataView: bytearray,
  numSamples: int,
  littleEndian: bool,
  bias: int,
):
  if (len(dataView) % 64 != 0):
    raise CodecException(
      f"encoded data length is not multiple of 64 bytes ({len(dataView)})",
    )

  samples = array('i', [0]*numSamples)

  numFrames = len(dataView) // 64
  current = 0
  start = 0
  firstData = 0
  lastValue = 0

  for i in range(numFrames):
    tempSamples = extractSteim2Samples(dataView, i * 64, False) # returns only differences except for frame 0

    firstData = 0 # d(0) is byte 0 by default

    if (i == 0):
      # special case for first frame
      lastValue = bias # assign our X(-1)

      # x0 and xn are in 1 and 2 spots
      start = tempSamples[1] # X(0) is byte 1 for frame 0

      # end = tempSamples[2]    # X(n) is byte 2 for frame 0
      firstData = 3 # d(0) is byte 3 for frame 0

      # if bias was zero, then we want the first sample to be X(0) constant
      if (bias == 0):
          lastValue = start - tempSamples[3] # X(-1) = X(0) - d(0)


    for j in range(firstData, len(tempSamples)):
        if current >= numSamples:
            break
        samples[current] = lastValue + tempSamples[j] # X(n) = X(n-1) + d(n)

        lastValue = samples[current]
        current+=1
  # end for each frame...

  if (current != numSamples):
    raise CodecException(
      f"Number of samples decompressed doesn't match number in header: {current} != {numSamples}")


  # ignore last sample check???
  #if (end != samples[numSamples-1]):
  #    raise SteimException("Last sample decompressed doesn't match value x(n) value in Steim2 record: "+samples[numSamples-1]+" != "+end)
  #
  return samples


#
# Extracts differences from the next 64 byte frame of the given compressed
# byte array (starting at offset) and returns those differences in an int
# array.
# An offset of 0 means that we are at the first frame, so include the header
# bytes in the returned int array...else, do not include the header bytes
# in the returned array.
#
# @param dataView byte array of compressed data differences
# @param offset index to begin reading compressed bytes for decoding
# @param littleEndian  the endian-ness of the compressed bytes being read
# @returns integer array of difference (and constant) values

def extractSteim2Samples(
  dataView: bytearray,
  offset: int,
  littleEndian: bool,
) -> array:
  # get nibbles
  nibbles = getUint32(dataView, offset, False) # steim always big endian for nibbles
  currNibble = 0
  dnib = 0
  temp = array('i', [0]*106) #max 106 = 7 samples * 15 long words + 1 nibble int

  currNum = 0
  diffCount = 0 # number of differences

  bitSize = 0 # bit size

  headerSize = 0 # number of header/unused bits at top

  headNib = (nibbles >> 30) & 0x03
  if headNib != 0:
      raise CodecException(f"nibble bytes must start with 00, but was {headNib:02b}")

  for i in range(16):
    currNibble = (nibbles >> (30 - i * 2)) & 0x03

    #switch (currNibble):
    if  currNibble == 0:
        # "0 means header info"
        # only include header info if offset is 0
        if (offset == 0):
            temp[currNum] = getInt32(dataView, offset + i * 4, False)
            currNum+=1

    elif  currNibble ==  1:

        endianChar = "<" if littleEndian else ">";
        vals = struct.unpack(endianChar+ "bbbb", dataView[offset + i * 4: offset+ i * 4 + 4])
        # print(f"1 means 4 one byte differences {currNum} {vals}")
        for k in range(4):
            temp[currNum+k] = vals[k]
        currNum+=4

    elif  currNibble == 2:
        tempInt = getUint32(dataView, offset + i * 4, False)
        dnib = (tempInt >> 30) & 0x03

        #switch (dnib):
        if dnib == 1:
            headerSize = 2
            diffCount = 1
            bitSize = 30
            dnibVals = extractDnibValues(tempInt, headerSize, diffCount, bitSize)
            temp[currNum] = dnibVals[0]
            currNum+=diffCount
            # print(f"2,1 means 1 thirty bit difference {dnibVals}")

        elif dnib == 2:
            headerSize = 2
            diffCount = 2
            bitSize = 15
            dnibVals = extractDnibValues(tempInt, headerSize, diffCount, bitSize)
            temp[currNum] = dnibVals[0]
            temp[currNum+1] = dnibVals[1]
            currNum+=diffCount
            # print(f"2,2 means 2 fifteen bit differences {dnibVals}")

        elif dnib == 3:
            headerSize = 2
            diffCount = 3
            bitSize = 10
            dnibVals = extractDnibValues(tempInt, headerSize, diffCount, bitSize)
            temp[currNum] = dnibVals[0]
            temp[currNum+1] = dnibVals[1]
            temp[currNum+2] = dnibVals[2]
            currNum+=diffCount
            # print(f"2,3 means 3 ten bit differences {tempInt:032b} {dnibVals}")

        else:
            raise CodecException(
              f"Unknown case currNibble={currNibble} dnib={dnib} for chunk {i} offset {offset}, nibbles: {nibbles}",
            )


    elif  currNibble == 3:
        tempInt = getUint32(dataView, offset + i * 4, False)
        dnib = (tempInt >> 30) & 0x03
        # for case 3, we are going to use a for-loop formulation that
        # accomplishes the same thing as case 2, just less verbose.
        diffCount = 0 # number of differences
        bitSize = 0 # bit size
        headerSize = 0 # number of header/unused bits at top

        #switch (dnib):
        if dnib == 0:
            # print(f"3,0 means 5 six bit differences: {tempInt:032b}")
            headerSize = 2
            diffCount = 5
            bitSize = 6

        elif dnib == 1:
            # print(f"3,1 means 6 five bit differences")
            headerSize = 2
            diffCount = 6
            bitSize = 5

        elif dnib == 2:
            # print(f"3,2 means 7 four bit differences, with 2 unused bits")
            headerSize = 4
            diffCount = 7
            bitSize = 4

        else:
            raise CodecException(
              f"Steim2 Unknown case currNibble={currNibble} dnib={dnib} for chunk {i} offset {offset}, nibbles: {nibbles:032b} int:{tempInt:032b}",
            )


        if (diffCount > 0):
          for d in range(diffCount):
            # for-loop formulation
            val = (tempInt << (headerSize + d * bitSize)) & 0xFFFFFFFF
            val = val - (1<<32) if val >= (1<<31) else val
            temp[currNum] = val >>  ((diffCount - 1) * bitSize + headerSize)
            currNum+=1

    else:
        raise CodecException(f"Unknown case currNibble={currNibble}")



  return temp[0:currNum]

def extractDnibValues(tempInt, headerSize, diffCount, bitSize):
    out = [0]*diffCount
    if (diffCount > 0):
      for d in range(diffCount):
        # for-loop formulation
        val = (tempInt << (headerSize + d * bitSize)) & 0xFFFFFFFF
        val = val - (1<<32) if val >= (1<<31) else val
        out[d] = val >>  ((diffCount - 1) * bitSize + headerSize)
    return out
