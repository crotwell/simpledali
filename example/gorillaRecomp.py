import simpledali
import sys
import argparse
import gorillacompression as gc

# grab example data like:
# curl -o casee.mseed3 'https://service.iris.edu/fdsnws/dataselect/1/query?net=CO&sta=CASEE&loc=00&cha=HHZ&starttime=2023-06-17T04:53:54.468&endtime=2023-06-17T04:55:00&format=miniseed3&nodata=404'
#
# run like:
# python3 example/gorillaRecomp.py -f casee_more.mseed3
#

def do_parseargs():
    parser = argparse.ArgumentParser(description='Gorilla recompress miniseed.')
    parser.add_argument(
    "-f",
    "--file",
    required=True,
    help="Miniseed3 file",
    )
    return parser.parse_args()

def processRecord(rec):
    data = rec.decompress()
    gorillaBins = [0,0,0,0,0]
    prev = 0
    prevdelta = 0
    for d in data:
        delta = d - prev
        dd = d - prev - ( prevdelta)
        if dd == 0:
            gorillaBins[0] += 1
        elif dd >= -63 and dd <= 64:
            gorillaBins[1] += 1
        elif dd >= -255 and dd <= 256:
            gorillaBins[2] += 1
        elif dd >= -2047 and dd <= 2048:
            gorillaBins[3] += 1
        else:
            gorillaBins[4] += 1
        #prevdelta = delta
        prev = d
        #print(f" {d} {delta} {dd}")
    #print()
    #print(f" {gorillaBins[0]} {gorillaBins[1]} {gorillaBins[2]} {gorillaBins[3]} {gorillaBins[4]}")

    encoder = gc.TimestampsEncoder(min_timestamp_delta=-2147483646)
    for d in data:
        encoder.encode_next(d)
    compressed = encoder.get_encoded()
    # compressed = gc.TimestampsEncoder.encode_all(data )
    re_decomp = gc.TimestampsDecoder.decode_all(compressed)
    if len(data)  != len(re_decomp):
        print(f" recomp not same length: {len(data)}  != {len(re_decomp)}")
    print(f" orig: type={rec.header.encoding} {rec.header.dataLength} bytes ->  {len(compressed['encoded'])} gorilla bytes for {len(data)} points")



def processRecordFloat(rec):
    data = rec.decompress()
    gain = 5.0431188410000354E8
    gain_data = list(map(lambda x: x/gain, data))
    compressed = gc.ValuesEncoder.encode_all(gain_data, float_format='f32')
    re_decomp = gc.ValuesDecoder.decode_all(compressed)
    if len(data)  != len(re_decomp):
        print(f" recomp not same length: {len(data)}  != {len(re_decomp)}")
    print(f" orig: type={rec.header.encoding} {rec.header.dataLength}, {4*len(data)} float bytes ->  {len(compressed['encoded'])} gorilla bytes for {len(data)} points")


def main():
    args = do_parseargs()
    rec = None
    recNum=0
    with open(args.file, 'rb') as f:
        rec_bytes = f.read()
        offset=0
        rec = simpledali.mseed3.unpackMSeed3Record(rec_bytes)
        while (recNum < 10):
            offset += rec.header.recordSize()
            rec = simpledali.mseed3.unpackMSeed3Record(rec_bytes[offset:])
            processRecord(rec)
            #processRecordFloat(rec)
            recNum += 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
