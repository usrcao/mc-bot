import sys
import asyncio
import json
import os
import re
import botpy
from botpy.message import GroupMessage, Message
from mcstatus import JavaServer

# ===== 配置区域（硬编码）=====
QQ_APPID = "0"
QQ_SECRET = "a"
# ============================

def load_servers():
    # 获取 .exe 所在目录
    if getattr(sys, 'frozen', False):
        # 打包成 exe 后，sys.executable 是 exe 的路径
        base_dir = os.path.dirname(sys.executable)
    else:
        # 普通 Python 脚本，使用当前文件所在目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    config_path = os.path.join(base_dir, "servers.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到 servers.json，查找路径: {config_path}")
        return []
    except json.JSONDecodeError:
        print("错误：servers.json 格式不正确")
        return []

def query_server_with_players(host: str, port: int) -> str:
    """查询服务器，优先尝试获取完整玩家列表，失败则降级到基本信息"""
    try:
        server = JavaServer.lookup(f"{host}:{port}")
        # 尝试 Query 协议（获取完整玩家列表）
        query = server.query(timeout=3)
        players = ", ".join(query.players.names) if query.players.names else "无"
        return (
            f"🟢 {host}:{port}\n"
            f"   {query.players.online}/{query.players.max} 人\n"
            f"   玩家: {players}"
        )
    except:
        # Query 失败，降级到 Status 协议（仅人数）
        try:
            status = server.status()
            return (
                f"🟢 {host}:{port}\n"
                f"   {status.players.online}/{status.players.max} 人(无法获取玩家列表)"
            )
        except Exception as e:
            print(f"查询 {host}:{port} 失败: {e}")
            return f"🔴 {host}:{port}\n   离线或无法连接"

def get_fixed_servers_status() -> str:
    servers = load_servers()
    if not servers:
        return "没有配置服务器"
    lines = []
    for s in servers:
        result = query_server_with_players(s['host'], s['port'])
        # 把返回结果中的 IP:端口 替换为 名称 
        lines.append(result.replace(f"{s['host']}:{s['port']}", f"{s['name']} "))
    return "\n\n".join(lines)

def extract_host_port(text: str):
    pattern = r'([a-zA-Z0-9\-\.]+):(\d+)'
    match = re.search(pattern, text.strip())
    if match:
        return match.group(1), int(match.group(2))
    pattern2 = r'([a-zA-Z0-9\-\.]+)'
    match2 = re.search(pattern2, text.strip())
    if match2:
        return match2.group(1), 25565
    return None, None

class MyBot(botpy.Client):
    async def on_c2c_message_create(self, message: Message):
        content = message.content.strip()
        host, port = extract_host_port(content)
        
        if host:
            status = await asyncio.get_event_loop().run_in_executor(None, query_server_with_players, host, port)
            await message.reply(content=f"\n{status}")
        else:
            status = await asyncio.get_event_loop().run_in_executor(None, get_fixed_servers_status)
            await message.reply(content=f"\n📊 服务器状态：\n\n{status}")

    async def on_group_at_message_create(self, message: GroupMessage):
        content = message.content.strip()
        host, port = extract_host_port(content)
        
        if host:
            status = await asyncio.get_event_loop().run_in_executor(None, query_server_with_players, host, port)
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0,
                msg_id=message.id,
                content=f"\n{status}"
            )
        else:
            status = await asyncio.get_event_loop().run_in_executor(None, get_fixed_servers_status)
            await message._api.post_group_message(
                group_openid=message.group_openid,
                msg_type=0,
                msg_id=message.id,
                content=f"\n📊 服务器状态：\n\n{status}"
            )

if __name__ == "__main__":
    intents = botpy.Intents(public_messages=True)
    bot = MyBot(intents=intents)
    print("机器人启动中...")
    bot.run(appid=QQ_APPID, secret=QQ_SECRET)
