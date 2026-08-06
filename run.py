import nonebot
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init()
driver = nonebot.get_driver()
driver.register_adapter(Adapter)
nonebot.load_plugins(".")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(nonebot.get_asgi(), host="0.0.0.0", port=8080)
