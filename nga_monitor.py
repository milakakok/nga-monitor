import requests
import re
import json
import os

# ====================== 只改这里 ======================
WATCH_UIDS = ["66662897", "557398"，"150058"，"26529713"]  # 监控的用户UID
NGA_COOKIE = "ngacn0comUserInfo=%25D3%25EA%25C2%25E4%25C7%25E0%25C9%25BD%09%25E9%259B%25A8%25E8%2590%25BD%25E9%259D%2592%25E5%25B1%25B1%0939%0939%09%0910%0910400%094%090%090%0961_5%2C39_30%2C87_15; __ad_cookie_mapping_tck_731=09371410aea4c684abbd3c9ed2d889dc; ngaPassportUid=41085401; ngaPassportUrlencodedUname=%25D3%25EA%25C2%25E4%25C7%25E0%25C9%25BD; ngaPassportCid=X9htfm15jqnes8bd33hfiipem0hbmaenllt9ie21; ngacn0comUserInfoCheck=bb6f89d844061915299b2929d7e2fceb; ngacn0comInfoCheckTime=1772636233; Hm_lvt_6933ef97905336bef84f9609785bcc3d=1772586354,1772600547,1772632124,1772715978; HMACCOUNT=CE51ACA11DEACE73; lastvisit=1772720444; lastpath=/read.php?tid=45502551&page=467; bbsmisccookies=%7B%22uisetting%22%3A%7B0%3A1%2C1%3A1773199973%7D%2C%22pv_count_for_insad%22%3A%7B0%3A-186%2C1%3A1772730074%7D%2C%22insad_views%22%3A%7B0%3A2%2C1%3A1772730074%7D%7D; Hm_lpvt_6933ef97905336bef84f9609785bcc3d=1772720690"         # 从Edge复制的Cookie
DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=1985f68a2fc3fc59d343a563747dc79088375b00c694a6f4267154f24c972da0"
# ======================================================

def get_username(uid, headers):
    """根据UID获取NGA用户名（增强版匹配规则）"""
    try:
        url = f"https://bbs.nga.cn/nuke.php?func=ucp&uid={uid}"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        
        # 调试：打印页面标题（方便排查匹配问题）
        title_match = re.search(r"<title>(.*?)</title>", resp.text)
        if title_match:
            page_title = title_match.group(1)
            print(f"🔍 用户{uid}的页面标题：{page_title}")
        else:
            print(f"❌ 用户{uid}未匹配到页面标题")
            return f"用户{uid}"

        # 规则1：匹配 [用户名]的个人主页（原规则）
        name_rule1 = re.search(r"\[(.*?)\]的个人主页", resp.text)
        # 规则2：匹配 用户名 - 个人主页（兼容其他格式）
        name_rule2 = re.search(r"(.+?) - 个人主页", resp.text)
        # 规则3：匹配页面内的用户名（最强兜底）
        name_rule3 = re.search(r'<meta name="author" content="(.*?)"', resp.text)

        if name_rule1:
            return name_rule1.group(1)
        elif name_rule2:
            return name_rule2.group(1)
        elif name_rule3:
            return name_rule3.group(1)
        else:
            print(f"❌ 用户{uid}所有规则均匹配不到用户名")
            return f"用户{uid}"
    except Exception as e:
        print(f"❌ 获取用户{uid}名称失败: {str(e)}")
        return f"用户{uid}"

def send_dingtalk(username, uid, tid):
    """发送监控消息到钉钉群（显示用户名）"""
    try:
        headers = {"Content-Type": "application/json;charset=utf-8"}
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"{username}有新发言",
                "text": f"### [NGA监控] {username}（UID：{uid}）发布新内容\n> 新帖链接：[点击查看](https://bbs.nga.cn/read.php?tid={tid})"
            }
        }
        resp = requests.post(DINGTALK_WEBHOOK, data=json.dumps(data), headers=headers, timeout=10)
        if resp.json()["errcode"] == 0:
            print(f"✅ 钉钉推送成功：{username}（UID：{uid}）")
        else:
            print(f"❌ 钉钉推送失败：{resp.text}")
    except Exception as e:
        print(f"❌ 推送出错：{str(e)}")

def main():
    """主监控逻辑"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": NGA_COOKIE,
        "Referer": "https://bbs.nga.cn/"
    }

    # 从文件读取上次TID
    last_tid_file = "last_tid.json"
    if os.path.exists(last_tid_file):
        with open(last_tid_file, "r") as f:
            last_tid = json.load(f)
    else:
        last_tid = {}

    for uid in WATCH_UIDS:
        # 先获取用户名
        username = get_username(uid, headers)
        
        try:
            url = f"https://bbs.nga.cn/nuke.php?func=ucp&uid={uid}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = "utf-8"
            matches = re.findall(r'href="read\.php\?tid=(\d+)"', resp.text)
            if not matches:
                print(f"⚠️ {username}（UID：{uid}）暂无发言")
                continue
            latest_tid = max(matches)
            
            # 对比并推送
            if uid not in last_tid or latest_tid > last_tid[uid]:
                send_dingtalk(username, uid, latest_tid)
                last_tid[uid] = latest_tid
                print(f"🔔 {username}（UID：{uid}）有新发言: {latest_tid}")
            else:
                print(f"ℹ️ {username}（UID：{uid}）无新发言")
        except Exception as e:
            print(f"❌ 处理{username}（UID：{uid}）出错: {str(e)}")
    
    # 保存最新TID到文件
    with open(last_tid_file, "w") as f:
        json.dump(last_tid, f)

if __name__ == "__main__":
    main()
