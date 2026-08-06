from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.rule import Rule
import httpx
import asyncio
from datetime import datetime

from config import SERVERS, ALLOWED_GROUP_ID

def is_allowed(event) -> bool:
    if event.detail_type == "private":
        return True
    if event.detail_type == "group":
        return event.group_id == ALLOWED_GROUP_ID and event.to_me
    return False

mc_status = on_message(rule=Rule(is_allowed), priority=5)

@mc_status.handle()
async def handle_mc_status(bot: Bot, event: Event):
    await mc_status.finish(await get_all_servers_status())

async def get_all_servers_status():
    tasks = [query_server(server) for server in SERVERS]
    results = await asyncio.gather(*tasks)
    
    reply = "🎮 服务器状态汇总\n" + "━" * 20 + "\n"
    for i, server in enumerate(SERVERS):
        reply += f"【{server['name']}】 {server['host']}:{server['port']}\n"
        reply += results[i] + "\n"
    reply += "━" * 20 + "\n"
    reply += f"⏰ {datetime.now().strftime('%H:%M:%S')} 更新"
    return reply

async def query_server(server):
    host, port = server["host"], server["port"]
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(f"https://api.mcapi.us/server/status/{host}/{port}")
            data = resp.json()
        if data.get("status") != "success":
            return "❌ 服务器离线"
        players = data.get("server", {}).get("players", {})
        online, max_players = players.get("online", 0), players.get("max", 0)
        sample = players.get("sample", [])
        line = f"👥 在线: {online}/{max_players}\n"
        if online > 0 and sample:
            names = [p.get("name", "?") for p in sample if p.get("name")]
            if len(names) > 20:
                names = names[:20] + [f"... 还有{len(names)-20}人"]
            line += "📋 " + ", ".join(names)
        else:
            line += "🧙 当前没有玩家在线"
        return line
    except httpx.TimeoutException:
        return "⏱️ 连接超时"
    except Exception as e:
        return f"⚠️ 查询失败: {str(e)[:30]}"
