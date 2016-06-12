import asyncio
from aiostatsd.client import StatsdClient
import unittest


class ServerProto(asyncio.Protocol):
    def __init__(self, received_queue):
        self.received_queue = received_queue

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.received_queue.put_nowait(data)

    def disconnect(self):
        self.transport.close()


class Server(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.incoming = asyncio.Queue()
        self._stop = asyncio.Future()
        self._done = asyncio.Future()

    async def run(self):
        loop = asyncio.get_event_loop()
        ctx = {}
        def make_proto():
            proto = ServerProto(self.incoming)
            ctx['proto'] = proto
            return proto
        conn = loop.create_datagram_endpoint(
            make_proto, local_addr=(self.host, self.port)
        )

        async def listen_for_stop():
            await self._stop
            ctx['proto'].disconnect()

        await asyncio.gather(conn, listen_for_stop())
        self._done.set_result(True)

    def flush(self):
        out = []
        while not self.incoming.empty():
            out.append(self.incoming.get_nowait())
        return out

    async def stop(self):
        self._stop.set_result(True)
        await self._done





class TestClient(unittest.TestCase):
    def test_client(self):
        counters = []
        expected_set = set()
        for i in range(100):
            counter_name = 'counter-%s' % i
            val = i * 10
            counters.append((counter_name, val, 1.0))
            formatted = "%s:%i|c" % (counter_name, val)
            expected_set.add(formatted.encode('utf-8'))

        async def go():
            server = Server('127.0.0.1', 9999)
            async def run_client():
                await asyncio.sleep(1.0)
                client = StatsdClient('127.0.0.1', 9999, flush_interval=0.05)
                async def sender():
                    for name, val, rate in counters:
                        await asyncio.sleep(0.01)
                        client.send_counter(name, val, rate)
                    await asyncio.sleep(0.2)
                    print('stopping')
                    await client.stop()
                    print('stopped')

                await asyncio.gather(client.run(), sender())
                await server.stop()

            await asyncio.gather(run_client(), server.run())
            return server.flush()

        loop = asyncio.get_event_loop()
        received = loop.run_until_complete(go())
        actual = set()
        for batch in received:
            batch = batch.decode('utf-8')
            for message in batch.split('\n'):
                actual.add(message.encode('utf-8'))
        self.assertEqual(expected_set, actual)

