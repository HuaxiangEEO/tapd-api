#!/usr/bin/env python3
"""查询今天创建的 TAPD 缺陷并生成总结报告"""

import json
import urllib.parse
import urllib.request
from base64 import b64encode
from datetime import datetime

# TAPD 配置
CLIENT_ID = "tapd-app-ee7f40"
CLIENT_SECRET = "21F9478D-45EA-93AD-135A-A98AAC5CD40D"
WORKSPACE_ID = "49394349"

def get_access_token():
    """获取 OAuth access_token"""
    url = "https://api.tapd.cn/tokens/request_token"
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_b64 = b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
    
    if result.get("status") != 1:
        raise Exception(f"获取 access_token 失败：{result.get('info')}")
    
    return result["data"]["access_token"]

def get_today_bugs(access_token):
    """获取今天创建的缺陷"""
    today = datetime.now()
    start = datetime(today.year, today.month, today.day, 0, 0, 0)
    end = datetime(today.year, today.month, today.day, 23, 59, 59)
    
    start_ts = int(start.timestamp())
    end_ts = int(end.timestamp())
    
    url = f"https://api.tapd.cn/bugs?workspace_id={WORKSPACE_ID}&limit=100&created={start_ts}-{end_ts}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
    
    if result.get("status") != 1:
        raise Exception(f"API 请求失败：{result.get('info')}")
    
    data = result.get("data", [])
    return [item["Bug"] for item in data] if isinstance(data, list) else []

def main():
    # 获取 token
    token = get_access_token()
    
    # 获取今天的缺陷
    bugs = get_today_bugs(token)
    
    # 状态分类
    status_map = {
        'new': '新表单',
        'resolved': '研发处理中',
        'verified': '其他',
        'closed': '其他',
        'postponed': '其他',
        'unconfirmed': '其他'
    }
    
    # 统计
    status_counts = {'新表单': 0, '研发处理中': 0, '其他': 0}
    priority_counts = {'urgent': 0, 'low': 0}
    
    for bug in bugs:
        status = bug.get('status', 'new')
        status_name = status_map.get(status, '其他')
        status_counts[status_name] = status_counts.get(status_name, 0) + 1
        
        priority = bug.get('priority', 'low')
        if priority in priority_counts:
            priority_counts[priority] += 1
    
    # 生成报告
    today_str = datetime.now().strftime('%Y-%m-%d')
    total = sum(status_counts.values())
    
    print(f"📊 今天创建的缺陷总结（{today_str}）\n")
    
    print("一、按状态分类")
    print(f"- 新表单：{status_counts['新表单']} 个")
    print(f"- 研发处理中：{status_counts['研发处理中']} 个")
    print(f"- 其他：{status_counts['其他']} 个")
    print(f"- 总计：{total} 个\n")
    
    print("二、按优先级分类")
    print(f"- urgent：{priority_counts['urgent']} 个")
    print(f"- low：{priority_counts['low']} 个\n")
    
    print("三、缺陷汇总表")
    print("| 状态 | 标题 | 优先级 | 负责人 |")
    print("|------|------|--------|--------|")
    
    # 按状态分组输出
    status_order = ['新表单', '研发处理中', '其他']
    for status_name in status_order:
        status_bugs = [b for b in bugs if status_map.get(b.get('status', 'new'), '其他') == status_name]
        for bug in status_bugs:
            title = bug.get('title', '无标题')[:30]
            priority = bug.get('priority', 'low')
            owner = bug.get('owner', '未分配')
            print(f"| {status_name} | {title} | {priority} | {owner} |")
    
    if total == 0:
        print("| - | 今天没有新增缺陷 | - | - |")
    
    print(f"\n（共 {total} 个缺陷）")

if __name__ == "__main__":
    main()
