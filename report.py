#!/usr/bin/env python3
"""밥상 치트키 성과 리포트를 만들어 텔레그램으로 보낸다.
사용: python3 report.py [--no-send] [--probe]
토큰은 환경 변수(THREADS_ACCESS_TOKEN, TELEGRAM_BOT_TOKEN)에서만 읽고 출력하지 않는다."""
import json, os, sys, urllib.request, urllib.parse
BASE = "https://graph.threads.net/v1.0"
TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def get(path, **params):
    params["access_token"] = TOKEN
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode(errors="replace").replace(TOKEN, "***")[:300]}


def metric_map(res):
    out = {}
    for m in res.get("data", []):
        v = m.get("total_value", {}).get("value")
        if v is None and m.get("values"):
            v = sum(x.get("value", 0) for x in m["values"])
        out[m["name"]] = v
    return out


def main():
    args = sys.argv[1:]
    if "--probe" in args:
        print("me:", get("me", fields="id,username"))
        print("user insights:", get("me/threads_insights", metric="views,likes,replies,reposts,followers_count"))
        print("keyword_search:", str(get("keyword_search", q="자취 요리", search_type="TOP", fields="id,text,permalink,username"))[:600])
        return
    lines = ["🍚 밥상 치트키 리포트"]
    u = metric_map(get("me/threads_insights", metric="views,likes,replies,reposts,followers_count"))
    if u:
        lines.append(f"팔로워 {u.get('followers_count', '-')}명 · 최근 조회 {u.get('views', '-')} · 좋아요 {u.get('likes', '-')} · 댓글 {u.get('replies', '-')}")
    posts = get("me/threads", fields="id,text,permalink,timestamp", limit=5).get("data", [])
    for p in posts[:3]:
        m = metric_map(get(f"{p['id']}/insights", metric="views,likes,replies,reposts"))
        title = (p.get("text") or "(이미지 글)").splitlines()[0][:22]
        lines.append(f"• {title}… 조회 {m.get('views', '-')} 좋아요 {m.get('likes', '-')} 댓글 {m.get('replies', '-')} 리포스트 {m.get('reposts', '-')}")
    extra = os.environ.get("REPORT_EXTRA", "").strip()
    if extra:
        lines.append(extra)
    msg = "\n".join(lines)
    print(msg)
    if "--no-send" not in args and TG and CHAT_ID:
        data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": msg, "disable_web_page_preview": "true"}).encode()
        with urllib.request.urlopen(f"https://api.telegram.org/bot{TG}/sendMessage", data=data, timeout=30) as r:
            print("텔레그램 전송:", json.load(r).get("ok"))


if __name__ == "__main__":
    main()
