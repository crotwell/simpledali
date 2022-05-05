# simple-dali
Datalink in pure python.

Protocol is defined at
https://iris-edu.github.io/libdali/datalink-protocol.html

Client jsonlarchive will archive /JSON packets as JSONL.

```
jsonlarchive -h
usage: jsonlarchive [-h] [-v] -m MATCH -w WRITE [-d DALIHOST] [-p DALIPORT]

Archive JSON datalink packets as JSONL.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -m MATCH, --match MATCH
                        Match regular expression pattern, ex '.*/JSON'
  -w WRITE, --write WRITE
                        JSONL Write pattern, usage similar to MSeedWrite in
                        ringserver
  -d DALIHOST, --dalihost DALIHOST
                        datalink host, defaults to localhost
  -p DALIPORT, --daliport DALIPORT
                        datalink port, defaults to 18000
```

# Example

Example of sending and receiving Datalink packets in the example directory.

# build/release
```
conda create -n simpledali python=3.9
conda activate simpledali
python3 -m pip install --upgrade build
python3 -m build
pip install dist/simpledali-0.0.1-py3-none-any.whl --force-reinstall
```

# maybe one day conda package:
```
conda install conda-build
```
