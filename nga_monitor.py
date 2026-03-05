import requests
import re
import json
import os
from requests.exceptions import RequestException

# ====================== 只改这里 ======================
WATCH_UIDS = ["66662897", "557398", "150058", "26529713"]  # 监控的用户UID
NGA_COOKIE = "ngacn0comUserInfo=%25D3%25EA%25C2%25E4%25C7%25E0%25C9%25BD%09%25E9%259B%25A8%25E8%2590%25BD%25E9%259D%2592%25E5%25B1%25B1%0939%0939%09%0910%0910400%094%090%090%0961_5%2C39_30%2C87_15; __ad_cookie_mapping_tck_731=09371410aea4c684abbd3c9ed2d889dc; ngaPassportUid=41085401; ngaPassportUrlencodedUname=%25D3%25EA%25C2%25E4%25C7%25E0%25C9%25BD; ngaPassportCid=X9htfm15jqnes8bd33hfiipem0hbmaenllt9ie21; ngacn0comUserInfoCheck=bb6f89d844061915299b2929d7e2fceb; ngacn0comInfoCheckTime=1772636233; Hm_lvt_6933ef97905336bef84f9609785bcc3d=1772586354,1772600547,1772632124,1772715978; HMACCOUNT=CE51ACA11DEACE73; lastvisit=1772720444; lastpath=/read.php?tid=45502551&page=467; bbsmisccookies=%7B%22uisetting%22%3A%7B0%3A1%2C1%3A1773199973%7D%2C%22pv_count_for_insad%22%3A%7B0%3A-186%2C1%3A1772730074%7D%2C%22insad_views%22%3A%7B0%3A2%2C1%3A1772730074%7D%7D; Hm_lpvt_6933ef97905336bef84f9609785bcc3d=1772720690"         # 从Edge复制的Cookie
DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=1985f68a2fc3fc59d343a563747dc79088375b00c694a6f4267154f24c972da0"
# ======================================================


def send_dingtalk(uid, tid):
    """简化版推送：直接用UID，避免用户名匹配问题"""
    try:
        headers = {"Content-Type": "application/json;charset=utf-8"}
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"NGA用户{uid}有新发言",
                "text": f"### [NGA监控] 用户（UID：{uid}）发布新内容\n> 新帖链接：[点击查看](https://bbs.nga.cn/read.php?tid={tid})"
            }
        }
        resp = requests.post(DINGTALK_WEBHOOK, data=json.dumps(data), headers=headers, timeout=10)
        if resp.json()["errcode"] == 0:
            print(f"✅ 钉钉推送成功：UID {uid}")
        else:
            print(f"❌ 钉钉推送失败：{resp.text}")
    except Exception as e:
        print(f"❌ 推送出错（UID {uid}）：{str(e)}")

def main():
    """核心监控逻辑：只关注TID，忽略用户名"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Cookie": NGA_COOKIE,
        "Referer": "https://bbs.nga.cn/",
        # 强制指定编码，避免乱码
        "Accept-Charset": "GBK,utf-8;q=0.7,*;q=0.3"
    }

    # 读取历史TID
    last_tid_file = "last_tid.json"
    last_tid = json.load(open(last_tid_file, "r", encoding="utf-8")) if os.path.exists(last_tid_file) else {}

    for uid in WATCH_UIDS:
        try:
            # 请求用户主页（GBK编码是NGA的默认编码）
            url = f"https://bbs.nga.cn/nuke.php?func=ucp&uid={uid}"
            resp = requests.get(url, headers=headers, timeout=15)
            resp.encoding = "GBK"  # 强制设置NGA的官方编码
            html = resp.text

            # 提取所有TID（简化匹配规则，提高成功率）
            tid_list = re.findall(r'read\.php\?tid=(\d+)', html)
            if not tid_list:
                print(f"ℹ️ UID {uid}：暂无发言/无法获取内容")
                continue
            
            latest_tid = max(tid_list)
            # 对比并推送新帖
            if uid not in last_tid or latest_tid > last_tid[uid]:
                print(f"🔔 UID {uid} 发现新发言：tid={latest_tid}")
                send_dingtalk(uid, latest_tid)
                last_tid[uid] = latest_tid
            else:
                print(f"ℹ️ UID {uid}：无新发言（最新tid={latest_tid}）")

        except RequestException as e:
            print(f"❌ UID {uid} 网络错误：{str(e)}")
        except Exception as e:
            print(f"❌ UID {uid} 处理错误：{str(e)}")

    # 保存最新TID（UTF-8编码）
    with open(last_tid_file, "w", encoding="utf-8") as f:
        json.dump(last_tid, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
