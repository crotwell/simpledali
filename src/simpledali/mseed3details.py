
from .mseed3 import MSeed3Record, readMSeed3Record

def main():
    import sys
    for a in sys.argv[1:]:
        with open(a, "rb") as inms3file:
            ms3 = readMSeed3Record(inms3file)
            while ms3 is not None:
                print(ms3.details())
                ms3 = readMSeed3Record(inms3file)

if __name__ == "__main__":
    main()
