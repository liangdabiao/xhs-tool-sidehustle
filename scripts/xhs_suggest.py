#!/usr/bin/env python
"""小红书搜索联想词采集（bsk 浏览器，需小红书登录态）。
实测（2026-11-24）：网页版搜索框 fill 触发联想面板，vom 中 button 型条目即联想词
（示例：「音频裁剪 」→ 剪映可以单独剪音频吗 / 音频怎么截取一部分 / 纯音频怎么裁剪…）。

用法: python xhs_suggest.py "音频裁剪" "求推荐剪辑工具" --out xhs_suggest.csv
产出: xhs_suggest.csv (word, suggest, ts)
纪律: 每词间隔 ≥3s；不自动点赞/关注/评论（合规红线）。
"""
import argparse, csv, os, re, subprocess, sys, time

ENV = {**os.environ, "BSK_AUTO_START": "0"}
SEARCH_URL = "https://www.xiaohongshu.com/search_result?keyword=__WD__"


def bsk(*args, timeout=60):
    r = subprocess.run(["bsk", *args], capture_output=True, text=True,
                       encoding="utf-8", errors="ignore", env=ENV, timeout=timeout)
    return r.stdout + "\n" + r.stderr


def obs_id():
    m = re.search(r'"observation_id": "([^"]+)"', bsk("sync", "--json"))
    return m.group(1) if m else None


def sync():
    return bsk("sync")


def collect(word, delay=3.0):
    import urllib.parse
    url = SEARCH_URL.replace("__WD__", urllib.parse.quote(word))
    o = obs_id()
    bsk("open", url, "--observation", o) if o else bsk("open", url)
    time.sleep(5)
    t = sync()
    m = re.search(r'@e(\d+) (?:textbox|searchbox) "([^"]*(?:搜索|小红书)[^"]*)"', t)
    if not m:
        return None, "FAIL no search box (未登录或页面未加载)"
    bsk("fill", f"@e{m.group(1)}", "--value", word + " ")
    time.sleep(2)
    t2 = sync()
    words = re.findall(r'@e\d+ button "([^"]{2,40})"', t2)
    # 归一化：vom 渲染会在字符间插空格；过滤 UI 按钮
    words = [re.sub(r"\s+", "", w) for w in words]
    words = [w for w in words if w and w.lower() not in
             ("close", "搜索", "确定", "取消", "×") and not w.startswith("筛")]
    time.sleep(delay)
    return words, "OK"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words", nargs="+")
    ap.add_argument("--out", default="xhs_suggest.csv")
    ap.add_argument("--delay", type=float, default=3.0)
    args = ap.parse_args()

    new = not os.path.exists(args.out)
    with open(args.out, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["word", "suggest", "ts"])
        for word in args.words:
            try:
                words, msg = collect(word, args.delay)
            except Exception as e:
                words, msg = None, f"FAIL exc: {e}"
            if words is None:
                print(f"{word}: {msg}", flush=True)
                continue
            w.writerow([word, "|".join(words), time.strftime("%Y-%m-%d %H:%M")])
            f.flush()
            print(f"{word}: {len(words)} 条联想 -> {words[:5]}", flush=True)
    print(f"done -> {args.out}")


if __name__ == "__main__":
    main()
