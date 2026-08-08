import os           
from dotenv import load_dotenv  
import asyncio
import botpy
from botpy.message import GroupMessage, Message
from mcstatus import JavaServer
from config import SERVER_LIST

load_dotenv()

APPID = os.getenv("QQ_APPID")
SECRET = os.getenv("QQ_SECRET")

def get_all_status_sync() -> str:
    """同步方式查询所有服务器"""
    results = []
    for server in SERVER_LIST:
        host, port, name = server["host"], server["port"], server["name"]
        try:
            # 使用测试成功的写法：lookup + status() 不传 timeout
            srv = JavaServer.lookup(f"{host}:{port}")
            status = srv.status()
            results.append(
                f"🟢 {name} ："
                f"   {status.players.online}/{status.players.max} 人"
                f"   {round(status.latency, 1)}ms"
            )
        except Exception as e:
            print(f"查询 {name} 失败: {e}")  # 控制台看具体错误
            results.append(f"🔴 {name} ：   离线或无法连接")
    
    return "\n\n".join(results)

class MyClient(botpy.Client):
    async def on_c2c_message_create(self, message: Message):
        # 在独立线程执行同步查询，避免阻塞事件循环
        status = await asyncio.get_event_loop().run_in_executor(None, get_all_status_sync)
        await message.reply(content=f"\n📊 服务器状态：\n\n{status}")

    async def on_group_at_message_create(self, message: GroupMessage):
        status = await asyncio.get_event_loop().run_in_executor(None, get_all_status_sync)
        await message._api.post_group_message(
            group_openid=message.group_openid,
            msg_type=0,
            msg_id=message.id,
            content=f"\n📊 服务器状态：\n\n{status}"
        )

if __name__ == "__main__":
    intents = botpy.Intents(public_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=APPID, secret=SECRET)
