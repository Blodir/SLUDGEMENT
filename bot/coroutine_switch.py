import asyncio

# Runs coroutine then returns value: False until coroutine is completed
class CoroutineSwitch:
    def __init__(self, coroutine):
        self.coroutine = coroutine
        self.value = False
        self.executing = False
    
    def getValue(self):
        if self.executing or self.value:
            return self.value
        self.executing = True
        asyncio.ensure_future(self._execute())

    async def _execute(self):
        self.value = await self.coroutine()
        self.executing = False
