# main.py
import os
import asyncio
import threading
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv
import botpy
from bot import MyClient

# 加载环境变量
load_dotenv()

# --- FastAPI Web 应用 ---
app = FastAPI()

@app.get("/")
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "QQ Bot"}

# --- 机器人启动函数 ---
def run_bot():
    """在独立线程中运行机器人"""
    appid = os.getenv("QQ_APPID")
    secret = os.getenv("QQ_SECRET")
    
    if not appid or not secret:
        print("❌ 错误：请设置 QQ_APPID 和 QQ_SECRET 环境变量")
        return
    
    # 关键修复：在新线程中创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    intents = botpy.Intents(public_messages=True)
    client = MyClient(intents=intents)
    print(" 机器人启动中...")
    
    try:
        client.run(appid=appid, secret=secret)
    except Exception as e:
        print(f"❌ 机器人运行出错: {e}")
    finally:
        loop.close()

# --- 主入口 ---
if __name__ == "__main__":
    # 在后台线程中启动机器人
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("✅ 机器人线程已启动")
    
    # 启动 Web 服务器
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Web 服务器启动在端口 {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
