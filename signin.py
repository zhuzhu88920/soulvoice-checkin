#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import requests
from lxml import etree
from random import randint

# 禁用 SSL 警告（可选）
requests.packages.urllib3.disable_warnings()


def pt_signin(cookie, signin_url):
    """
    PT 站点签到函数
    """
    session = requests.Session()
    headers = {
        'cookie': cookie,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
    }
    
    try:
        res = session.get(signin_url, headers=headers, timeout=30)
        res.encoding = 'utf-8'
        html = etree.HTML(res.text)
        
        # 获取签到结果信息
        msg_list = html.xpath(
            '//td[@class="embedded"]/h2/text()|'
            '//td[@class="embedded"]//p//text()|'
            '//*[@class="embedded"]//*[@class="text"]//text()'
        )
        
        # 如果列表为空，尝试其他xpath路径
        if not msg_list:
            msg_list = html.xpath('//*[@id="outer"]//text()|//body//text()')
            # 过滤空字符串和无关内容
            msg_list = [m.strip() for m in msg_list if m.strip() and '签到' in m]
        
        # 如果仍然为空，返回错误信息
        if not msg_list:
            return "签到失败：无法获取页面信息", None
        
        # 构建消息
        msg = msg_list[0]
        if len(msg_list) > 1:
            msg += ',' + ''.join(msg_list[1:])
        msg += '\n'
        
        # 尝试获取连续签到天数
        days = None
        try:
            msg1_list = html.xpath('//*[@id="outer"]//a/font/text()|//*[@id="outer"]//a/font/span/text()')
            if msg1_list:
                msg1 = ''.join(msg1_list)
                if "未" in msg1:
                    msg += msg1
                # 尝试提取天数
                day_match = re.search(r'(\d+)\s*天', msg1)
                if day_match:
                    days = day_match.group(1)
        except:
            pass
        
        # 检查是否签到成功
        is_success = False
        if '签到成功' in msg or '重复' in msg or '已连续签到' in msg:
            is_success = True
            # 如果前面没提取到天数，再尝试从整个文本提取
            if not days:
                day_match = re.search(r'已连续签到\s*(\d+)\s*天', msg)
                if day_match:
                    days = day_match.group(1)
        
        return msg.strip(), is_success, days
        
    except Exception as e:
        return f"签到异常：{str(e)}", False, None


def send_bark(title, content, bark_push_url):
    """
    通过 Bark 推送消息
    """
    if not bark_push_url:
        print("Bark 推送地址未设置，跳过推送")
        return False
    
    try:
        # 处理 URL，确保格式正确
        bark_url = bark_push_url.rstrip('/')
        # 如果 URL 已经包含 / 结尾，直接拼接，否则添加 /
        full_url = f"{bark_url}/{title}/{content}"
        
        response = requests.get(full_url, timeout=10)
        result = response.json()
        
        if result.get('code') == 200:
            print("Bark 推送成功！")
            return True
        else:
            print(f"Bark 推送失败：{result}")
            return False
    except Exception as e:
        print(f"Bark 推送异常：{str(e)}")
        return False


def main():
    """
    主函数
    """
    # 从环境变量读取配置
    cookie = os.getenv('COOKIE', '')
    bark_push = os.getenv('BARK_PUSH', '')
    signin_url = os.getenv('SIGNIN_URL', 'https://pt.soulvoice.club/attendance.php')
    site_name = os.getenv('SITE_NAME', '聆音')
    
    # 检查必要配置
    if not cookie:
        print("错误：未设置 COOKIE 环境变量")
        print("请在 GitHub Actions Secrets 中添加 COOKIE")
        exit(1)
    
    print(f"开始执行 {site_name} 签到任务...")
    print(f"签到地址：{signin_url}")
    
    # 执行签到
    msg, is_success, days = pt_signin(cookie, signin_url)
    
    # 输出结果到控制台
    print(f"签到结果：{msg}")
    
    # 如果签到成功或重复签到，发送 Bark 推送
    if bark_push and is_success:
        # 构建推送标题和内容
        if days:
            title = f"{site_name}签到-连续{days}天"
            content = f"🎉 签到成功！已连续签到 {days} 天"
        else:
            title = f"{site_name}签到成功"
            content = msg
        
        # 发送推送
        send_bark(title, content, bark_push)
    elif bark_push and not is_success:
        # 签到失败也推送通知
        title = f"{site_name}签到失败"
        content = f"❌ {msg}"
        send_bark(title, content, bark_push)
    else:
        print("未配置 Bark 推送地址，跳过推送")


if __name__ == '__main__':
    # 随机延迟 0-60 秒，避免请求过于集中
    delay = randint(0, 60)
    print(f"随机延迟 {delay} 秒后执行...")
    time.sleep(delay)
    
    main()
