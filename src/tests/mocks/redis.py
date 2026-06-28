
import asyncio 

class RedisMock:
    database = {}

    
    async def get(self, name):
        await asyncio.sleep(0.1)
        return RedisMock.database.get(str(name), None)

    async def set(self, name, value, ex):
        
        RedisMock.database[str(name)] = value
        await asyncio.sleep(0.1)
        return True

    async def ttl(self, name):
        return 100

    async def delete(self, name):
        await asyncio.sleep(0.1)
        RedisMock.database.pop(str(name), None)
