# simpledali

[![PyPI](https://img.shields.io/pypi/v/simpledali)](https://pypi.org/project/simpledali/)
[![Documentation Status](https://readthedocs.org/projects/simpledali/badge/?version=latest)](https://simpledali.readthedocs.io/en/latest/?badge=latest)

Datalink in pure python.

Read the docs at [readthedocs](https://readthedocs.org/projects/simpledali/)


Datalink is a protocol for near-realtime transfer of seismic data, usually in miniseed, but has flexibility to carry any payload such as JSON. The Protocol is defined at
https://iris-edu.github.io/libdali/datalink-protocol.html

See [ringserver](https://github.com/iris-edu/ringserver) from IRIS
for the most common datalink server instance. The public instance
at [rtserve.iris.washington.edu/](http://rtserve.iris.washington.edu/) allows access to near-realtime streaming seismic data over web sockets at [ws://rtserve.iris.washington.edu/datalink](ws://rtserve.iris.washington.edu/datalink)

For parsing for miniseed2 and
[miniseed3](http://docs.fdsn.org/projects/miniseed3/en/latest/index.html#)
see [simplemseed](https://github.com/crotwell/simplemseed), also in pure python.

Support for both regular sockets and websockets. For example:

```
import asyncio
import simpledali

async def main():
    host = "localhost"
    port = 16000
    uri = f"ws://{host}:{port}/datalink"
    verbose = True

    programname = "simpleDali"
    username = "dragrace"
    processid = 0
    architecture = "python"

    # for regular socket (DataLinkPort)
    async with simpledali.SocketDataLink(host, port, verbose=verbose) as dali:
        serverId = await dali.id(programname, username, processid, architecture)
        print(f"Connect to {host}:{port} via regular socket")
        print(f"Socket Id: {serverId.message}")
    # for web socket (ListenPort)
    async with simpledali.WebSocketDataLink(uri, verbose=verbose) as dali:
        serverId = await dali.id(programname, username, processid, architecture)
        print(f"Connect to {uri} via websocket")
        print(f"WebSocket Id: {serverId.message}")

asyncio.run(main())
```

The dali2jsonl script will archive '/JSON' packets as JSON Lines. This is a similar function to the MSeedWrite configuration on ringserver, but in a separate process and saves JSON packets instead of miniseed. See jsonlines.org for the file format, basically one JSON
value per line.

```
dali2jsonl --help
usage: dali2jsonl [-h] [-v] -c CONF

Archive JSON datalink packets as JSON Lines.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -c CONF, --conf CONF  Configuration as TOML
```

The TOML configuration looks like:
```
[datalink]
# datalink host, defaults to localhost
host='localhost'
# datalink port, defaults to 18000
port=15004
# Match regular expression pattern on stream ids, ex '.*/JSON'
match='.*/JSON'

[jsonl]
# JSONL Write pattern, usage similar to MSeedWrite in ringserver
write='/data/scsn/www/jsonl/%n/%s/%Y/%j/%n.%s.%l.%c.%Y.%j.%H.jsonl'

```

# Example

There are examples of sending and receiving Datalink packets in the
[example directory](https://github.com/crotwell/simplemseed/tree/main/examples).
