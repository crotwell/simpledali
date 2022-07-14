import asyncio
import simpledali

host = "localhost"
port = 16000
uri = f"ws://{host}:{port}/datalink"
verbose = True


async def main():
    verbose = False
    programname = "simpleDali"
    username = "dragrace"
    processid = 0
    architecture = "python"
    dali = simpledali.SocketDataLink(host, port, verbose=verbose)
    # dali = simpledali.WebSocketDataLink(uri, verbose=True)
    serverId = await dali.id(programname, username, processid, architecture)
    print(f"Resp: {serverId}")
    await dali.close()


asyncio.run(main())
