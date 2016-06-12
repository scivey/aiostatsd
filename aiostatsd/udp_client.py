import asyncio

async def queue_get(async_queue, timeout=None):
    result = async_queue.get()
    if timeout is None:
        return (await result)
    return (await asyncio.wait_for(result, timeout=timeout))

async def queue_maybe_get(async_queue, timeout=0.1):
    try:
        return (await queue_get(async_queue))
    except asyncio.TimeoutError:
        return None


class ClientProto(asyncio.Protocol):
    def __init__(self, msg_queue, loop):
        self.msg_queue = msg_queue
        self.loop = loop
        self.transport = None
        self.on_connected = asyncio.Future()
        self.on_disconnect = asyncio.Future()
        self._connected = False

    async def run_loop(self):
        while self._connected:
            msg = await queue_maybe_get(self.msg_queue)
            if msg is not None:
                self.transport.sendto(msg)

    def connection_made(self, transport):
        self.transport = transport
        self.on_connected.set_result(True)
        self._connected = True
        self._loop_future = asyncio.ensure_future(self.run_loop())

    def disconnect(self):
        self._connected = False
        self._loop_future.cancel()
        self.transport.close()

    def connection_lost(self, exc):
        self.on_disconnect.set_result(exc)

    def error_received(self, err):
        print('err', err)


class UDPClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.conn = None
        self._pending = asyncio.Queue()
        self._running = False
        self._stop = asyncio.Future()
        self._join = asyncio.Future()

    async def run(self):
        self._running = True
        loop = asyncio.get_event_loop()
        ctx = {}
        def make_client():
            client = ClientProto(self._pending, loop)
            ctx['client'] = client
            return client

        self.conn = loop.create_datagram_endpoint(
            make_client,
            remote_addr=(self.host, self.port)
        )
        async def wait_for_stop():
            await self._stop
            ctx['client'].disconnect()
            await ctx['client'].on_disconnect

        await asyncio.gather(self.conn, wait_for_stop())
        self._join.set_result(True)

    async def stop(self):
        self._stop.set_result(True)
        await self._join

    def send_nowait(self, msg):
        self._pending.put_nowait(msg)
