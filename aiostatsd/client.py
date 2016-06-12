import asyncio
import time
import contextlib
from cystatsd import MetricCollector
from .udp_client import UDPClient
import random

class LowLevelStatsdClient(object):
    def __init__(self, host, port, packet_size=512, flush_interval=0.5):
        self.host = host
        self.port = port
        self.collector = MetricCollector(packet_size)
        self._udp_client = None
        self._running = False
        self._done = asyncio.Future()
        self.flush_interval = flush_interval

    def send_timer(self, name, value, rate):
        self.collector.push_timer(name, value, rate)

    def send_gauge(self, name, value, rate):
        self.collector.push_gauge(name, value, rate)

    def send_counter(self, name, value, rate):
        self.collector.push_counter(name, value, rate)

    async def run(self):
        self._udp_client = UDPClient(self.host, self.port)
        work = [self._udp_client.run()]
        self._running = True
        async def ticker():
            while self._running:
                await asyncio.sleep(self.flush_interval)
                messages = self.collector.flush()
                for msg in messages:
                    self._udp_client.send_nowait(msg)
        work.append(ticker())
        await asyncio.gather(*work)
        self._done.set_result(True)

    async def stop(self):
        self._running = False
        await self._udp_client.stop()
        await self._done


class StatsdClient(object):
    def __init__(self, host, port, packet_size=512, flush_interval=0.5):
        self.client = LowLevelStatsdClient(
            host=host, port=port,
            packet_size=packet_size,
            flush_interval=flush_interval
        )

    def send_counter(self, name, value, rate=1.0):
        if rate >= 1.0 or random.uniform(0, 1.) <= rate:
            self.client.send_counter(name, value, rate)

    def send_timer(self, name, value, rate=1.0):
        if rate >= 1.0 or random.uniform(0, 1.) <= rate:
            self.client.send_timer(name, value, rate)

    def send_gauge(self, name, value, rate=1.0):
        if rate >= 1.0 or random.uniform(0, 1.) <= rate:
            self.client.send_gauge(name, value, rate)

    def incr(self, name, value=1, rate=1.0):
        self.send_counter(name, value, rate)

    def decr(self, name, value=1, rate=1.0):
        value = -abs(value)
        self.send_counter(name, value, rate)

    @contextlib.contextmanager
    def timer(self, name, rate=1.0):
        start = time.time()
        try:
            yield
        finally:
            duration_sec = time.time() - start
            # time.time() returns seconds; we need msec
            duration_msec = int(round(duration_sec * 1000))
            self.send_timer(name, duration_msec, rate=rate)

    def run(self):
        return self.client.run()

    def stop(self):
        return self.client.stop()
