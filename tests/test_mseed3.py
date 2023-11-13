import pytest
import json
import os
import simpledali
from datetime import datetime

from pathlib import Path

TEST_DIR =  Path(__file__).parent

githubUrl = "git clone https://github.com/FDSN/miniSEED3.git"

# ref data from https://github.com/FDSN/miniSEED3
ref_data_dir = f"{TEST_DIR}/miniSEED3/reference-data"
ref_data_list = [
  f"{ref_data_dir}/reference-detectiononly.mseed3",
  f"{ref_data_dir}/reference-sinusoid-FDSN-All.mseed3",
  f"{ref_data_dir}/reference-sinusoid-FDSN-Other.mseed3",
  f"{ref_data_dir}/reference-sinusoid-TQ-TC-ED.mseed3",
  f"{ref_data_dir}/reference-sinusoid-float32.mseed3",
  f"{ref_data_dir}/reference-sinusoid-float64.mseed3",
  f"{ref_data_dir}/reference-sinusoid-int16.mseed3",
  f"{ref_data_dir}/reference-sinusoid-int32.mseed3",
  f"{ref_data_dir}/reference-sinusoid-steim1.mseed3",
  f"{ref_data_dir}/reference-sinusoid-steim2.mseed3",
  f"{ref_data_dir}/reference-text.mseed3",
]


# mseed3 via
# https://service.iris.edu/fdsnws/dataselect/1/query?net=CO&sta=CASEE&loc=00&cha=HHZ&starttime=2023-06-17T04:53:54.468&endtime=2023-06-17T04:55:00&format=miniseed3&nodata=404
#


class TestMseed3:
    def test_read(self):
        msi_data = [89, 67, 53, 71, 86, 89,
            97, 96, 81, 90, 94, 73,
            73, 79, 87, 100, 91, 107,
           105, 102, 112, 93, 106, 101,
            92, 100, 84, 99, 97, 108,
           151, 130, 114, 124, 116, 116,
           102, 108, 130, 121, 127, 131,
           129, 134, 109, 112, 123, 121,
           139, 132, 153, 157, 128, 140,
           129, 140, 150, 138, 158, 141,
           132, 137, 131, 149, 159, 156,
           142, 140, 158, 154, 149, 141,
           135, 152, 152, 157, 168, 162,
           158, 151, 144, 148, 137, 133,
           147, 150, 155, 139, 134, 154,
           149, 156, 152, 137, 142, 145,
           147, 142, 138, 143, 136, 140,
           143, 137]
        with open(TEST_DIR /"casee.mseed3", "rb") as f:
          rec_bytes = f.read()
          assert len(rec_bytes) == 285
          rec = simpledali.mseed3.unpackMSeed3Record(rec_bytes)
          data = rec.decompress()
          assert len(msi_data) == len(data)
          for i in range(len(msi_data)):
              assert msi_data[i] == data[i], f"{i} msi:{msi_data[i]} != {data[i]} "

    def test_ref_data(self):
        for filename in ref_data_list:
            if not os.path.exists(filename):
                assert False, f"load reference data for {filename} from {githubUrl}"
            with open(filename, 'rb') as infile:
                rec_bytes = infile.read()
                rec = simpledali.mseed3.unpackMSeed3Record(rec_bytes)
                if rec.header.encoding != 0:
                    # encoding == 0 is Text, with no structure, so cannot decompress
                    data = rec.decompress()
                    assert len(data) > 0, filename
                    jsonfilename = filename.replace(".mseed3", ".json")
                    with open(jsonfilename, 'r') as injson:
                        jsonrec = json.load(injson)[0]
                        assert jsonrec["FormatVersion"] == rec.header.formatVersion
                        assert jsonrec["EncodingFormat"] == rec.header.encoding
                        assert jsonrec["SampleRate"] == rec.header.sampleRate(), f"{jsonrec['SampleRate']} != {rec.header.sampleRate()}"
                        assert jsonrec["SampleCount"] == rec.header.numSamples
                        assert jsonrec["CRC"] == rec.header.crcAsHex(), f"{jsonrec['CRC']} {rec.header.crcAsHex()}"
                        assert jsonrec["PublicationVersion"] == rec.header.publicationVersion
                        assert jsonrec["SID"] == rec.header.identifier
                        jsondata = jsonrec["Data"]
                        assert len(jsondata) == len(data)
                        for i in range(len(jsondata)):
                            assert jsondata[i] == data[i], f"{i}  {jsondata[i]} != {data[i]}"


if __name__ == "__main__":
    TestMseed3().test_ref_data()
