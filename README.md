# simpledali

[![PyPI](https://img.shields.io/pypi/v/simpledali)](https://pypi.org/project/simpledali/)

Datalink in pure python.

Protocol is defined at
https://iris-edu.github.io/libdali/datalink-protocol.html

See [ringserver](https://github.com/iris-edu/ringserver) from IRIS
for the most common datalink server instance.

Support for both regular sockets and websockets. For example:

```
import asyncio
import simpledali
host = "localhost"
port = 18000
uri = f"ws://{host}:{port}/datalink"
verbose = True

async def main():
    verbose=False
    programname="simpleDali"
    username="dragrace"
    processid=0
    architecture="python"
    dali = simpledali.SocketDataLink(host, port, verbose=verbose)
    # dali = simpledali.WebSocketDataLink(uri, verbose=True)
    serverId = await dali.id(programname, username, processid, architecture)
    print(f"Resp: {serverId}")
    await dali.close()

asyncio.run(main())
```

The jsonlarchive script will archive '/JSON' packets as JSONL. This is a similar function to the MSeedWrite configuration on ringserver, but in a separate process and saves JSON packets instead of miniseed.

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

There are examples of sending and receiving Datalink packets in the example directory.
