# simpledali

[![PyPI](https://img.shields.io/pypi/v/simpledali)](https://pypi.org/project/simpledali/)

Datalink in pure python.

Datalink is a protocol for near-realtime transfer of seismic data, usually in miniseed, but has flexibility to carry any payload such as JSON. The Protocol is defined at
https://iris-edu.github.io/libdali/datalink-protocol.html

See [ringserver](https://github.com/iris-edu/ringserver) from IRIS
for the most common datalink server instance. The public instance
at [rtserve.iris.washington.edu/](http://rtserve.iris.washington.edu/) allows access to near-realtime streaming seismic data over web sockets at [ws://rtserve.iris.washington.edu/datalink](ws://rtserve.iris.washington.edu/datalink)

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

There are examples of sending and receiving Datalink packets in the example directory.
