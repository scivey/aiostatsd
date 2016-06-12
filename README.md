# aiostatsd

An asyncio statsd client for Python >= 3.4.
The underlying protocol is [written in cython](https://github.com/scivey/cystatsd), which we can all admit is pretty cool.

It automatically batches multiple metrics in single UDP packets, with a configurable target packet size of 512 bytes.  The flush interval defaults to 0.5 seconds, but can also be configured.


## Install

```bash
pip install aiostatsd
```

## Example
```python
import asyncio
from aiostatsd.client import StatsdClient

async def go():
    client = statsd
    asyncio.ensure_future(client.run())
    with client.timer("something", rate=0.1):
        pass
    client.incr("x")
    client.decr("y", 5)
    client.send_gauge("queue_depth", 50)
    await client.stop()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(go())
```

## License
MIT
