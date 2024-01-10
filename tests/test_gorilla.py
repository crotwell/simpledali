import pytest
import json
import os
import simpledali
from datetime import datetime
import gorillacompression as gc


from pathlib import Path

TEST_DIR =  Path(__file__).parent


class TestGorilla:
    def test_roundtrip(self):
        values = [3.2, 1.5, 16.6, 2000]
        timestamps = [1628164645, 1628164649, 1628164656, 1628164669]
        pairs = list(zip(timestamps, values))
        content = gc.PairsEncoder.encode_all(pairs)
        encodedData = content['encoded']
        header = simpledali.MSeed3Header()
        header.dataLength = len(encodedData)
        header.numSamples = len(values)
        header.encoding = simpledali.gorilla.GORILLA_F64
        header.sampleRatePeriod = (timestamps[-1] - timestamps[0])/(header.dataLength-1)
        record = simpledali.Mseed3Record(header, encodedData)
        recordBytes = record.pack()
        outRecord = simpledali.unpackMSeed3Record(recordBytes)
        decomp_data = outRecord.decompress()
        print(decomp_data)
        assert len(decomp_data) == len(pairs)
        for i in range(len(decomp_data)):
            assert decomp_data[i][0] == timestamps[i], f"{i} msi:{decomp_data[i]} != {timestamps[i]} "
            assert decomp_data[i][1] == values[i], f"{i} msi:{decomp_data[i]} != {values[i]} "
