# -*- coding: utf-8 -*-
import os
import re
import requests
from bs4 import BeautifulSoup

COOKIE = os.environ.get("COOKIE", "").strip()
BARK_KEY = os.environ.get("BARK_KEY", "").strip()

def send_bark(title: str, content: str):
    """仅在最后统一推送一次 Bark"""
    if not BARK_KEY:
        print("未配置 BARK_KEY，跳过推送")
        return
    try:
        url = "https://api.day.app/push"
        payload = {
            "device_key": BARK_KEY,
            "title": title,
            "body": content,
        }
        res = requests.post(url, json=payload, timeout=10)
        print("Bark 推送状态:", res.status_code)
    except Exception as e:
        print("Bark 推送失败:", e)

def checkin() -> str:
    if not COOKIE:
        return "❌ 未找到 COOKIE，请检查 Secrets 配置"

    url = "https://pt.soulvoice.club/attendance.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": COOKIE,
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.encoding = resp.apparent_encoding or "utf-8"

        if "login.php" in resp.url or "未登录" in resp.text:
            return "❌ Cookie 已失效，请重新获取"

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text()

        if "这是您的第" in text or "签到成功" in text:
            match = re.search(r"(这是您的第\s*\d+\s*次签到.*?魔力值)", text)
            return f"🎉 签到成功！{match.group(1) if match else ''}"
        elif "已经签到" in text:
            return "💡 今日已签到，无需重复签到"
        else:
            return f"✅ 请求已发送（状态码 {resp.status_code}）"

    except Exception as e:
        return f"❌ 签到请求异常: {e}"

if __name__ == "__main__":
    # 1. 执行签到
    msg = checkin()
    print(msg)
    
    # 2. 仅在此处触发 1 次 Bark 推送
    send_bark("SoulVoice 签到", msg)
