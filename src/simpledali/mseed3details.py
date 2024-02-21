
import argparse
from .mseed3 import MSeed3Record, readMSeed3Record

def do_parseargs():
    parser = argparse.ArgumentParser(
        description="Simple conversion of miniseed 2 to 3."
    )
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    parser.add_argument(
        "--eh", help="display extra headers", action="store_true"
    )
    parser.add_argument(
        "--summary", help="one line summary per record", action="store_true"
    )
    parser.add_argument(
        'ms3files',
        metavar='ms3file',
        nargs='+',
        help='mseed3 files to print')
    return parser.parse_args()

def main():
    import sys
    args = do_parseargs()
    for ms3file in args.ms3files:
        with open(ms3file, "rb") as inms3file:
            ms3 = readMSeed3Record(inms3file)
            while ms3 is not None:
                if args.summary:
                    print(ms3)
                else:
                    print(ms3.details(showExtraHeaders=args.eh))
                ms3 = readMSeed3Record(inms3file)

if __name__ == "__main__":
    main()
