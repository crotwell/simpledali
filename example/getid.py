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
