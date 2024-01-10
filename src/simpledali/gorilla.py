
import gorillacompression as gc

from .exception import (
    CodecException,
    UnsupportedCompressionType,
)

# 32 bit int, double delta
GORILLA_I32: int = 250
# 32 bit float values, xor compression
GORILLA_F32: int = 251
# 64 bit float values, xor compression
GORILLA_F64: int = 252



def isGorilla(encoding):
    return encoding == GORILLA_F32 or encoding == GORILLA_F64


def decompressGorilla(
  compressionType: int,
  dataView: bytearray,
  numSamples: int,
):

    gorilla_floattype = ""
    if compressionType == GORILLA_I32:
        # double-delta "timestamp" compression
        content = {
            'encoded': dataView,
            'nb_timestamps': numSamples,
        }
        return gc.TimestampsDecoder.decode_all(content)

    elif compressionType == GORILLA_F32:
        gorilla_floattype = 'f32'
    elif compressionType == GORILLA_F64:
        gorilla_floattype = 'f64'
    else:
        raise UnsupportedCompressionType(
          f"Type {compressionType} is not supported at this time, numsamples: {numSamples}.",
        )
    content = {
        'encoded': dataView,
        'nb_pairs': numSamples,
        'float_format': gorilla_floattype,
    }
    return gc.PairsDecoder.decode_all(content)
