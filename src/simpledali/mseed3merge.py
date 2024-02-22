
import argparse
from .mseed3 import MSeed3Record, readMSeed3Record, merge

def do_parseargs():
    parser = argparse.ArgumentParser(
        description="Simple merging of miniseed 3 records."
    )
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    parser.add_argument(
        '-o',
        '--outfile',
        help='mseed3 file to output merged records')
    parser.add_argument(
        'ms3file',
        help='mseed3 file to merge records')
    return parser.parse_args()

def main():
    import sys
    args = do_parseargs()
    with open(args.outfile, "wb") as outms3file:
        with open(args.ms3file, "rb") as inms3file:
            prevms3 = None
            ms3 = readMSeed3Record(inms3file)
            while ms3 is not None:
                if prevms3 is not None:
                    merged = merge(prevms3, ms3)
                    if len(merged) == 2:
                        outms3file.write(merged[0].pack())
                        prevms3 = merged[1]
                    else:
                        prevms3 = merged[0]
                else:
                    prevms3 = ms3
                ms3 = readMSeed3Record(inms3file)
            if prevms3 is not None:
                outms3file.write(prevms3.pack())

if __name__ == "__main__":
    main()
