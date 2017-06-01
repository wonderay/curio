# bridge.py
#
# Support for running asyncio coroutines from within curio.
# The curio->asyncio bridge runs a separate asyncio event loop in a different thread,
# which has coroutines submitted to it over the course of the kernel's lifetime.

__all__ = [ 'AsyncioLoop' ]

# -- Standard library

import asyncio
import threading

# -- Curio

from .traps import _get_kernel, _future_wait
from .sync import Event
from . import task
from . import workers

class AsyncioLoop(object):
    '''
    A curio interface to an asyncio event loop.   It allows asyncio coroutines
    to be submitted to asyncio and executed in a backrgound thread.   Only
    one method is provided, run_asyncio().
    '''
    
    def __init__(self, event_loop=None):
        self.loop = event_loop if event_loop else asyncio.new_event_loop()
        self._thread = None
        self._shutdown = Event()
        
    def _asyncio_thread(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _asyncio_task(self):
        # A curio supervisor task for the background asyncio loop.  It doesn't
        # really do anything except sit around and wait for cancellation.
        # When cancelled, it shuts the asyncio thread down.
        try:
            await self._shutdown.wait()
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)
            await workers.run_in_thread(self._thread.join)
            self._thread = None

    async def run_asyncio(self, corofunc, *args):
        '''
        Run an asyncio compatible coroutine corofunc(*args) to completion, 
        returning its result
        '''
        if self._thread is None:
            self._thread = threading.Thread(target=self._asyncio_thread)
            self._thread.start()
            await task.spawn(self._asyncio_task, daemon=True)

        fut  = asyncio.run_coroutine_threadsafe(corofunc(*args), self.loop)
        await _future_wait(fut)
        return fut.result()

    async def shutdown(self):
        await self._shutdown.set()
        
    async def __aenter__(self):
        return self

    async def __aexit__(self, ty, val, tb):
        await self.shutdown()

    
    
        
        

            
            
        
        
