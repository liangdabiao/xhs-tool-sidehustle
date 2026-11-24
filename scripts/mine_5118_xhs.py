#!/usr/bin/env python
"""5118 小红书长尾词挖掘驱动（bsk 浏览器，需 5118 登录态）。
实测路径（2026-11-24）：落地页 www.5118.com/ci/xhs → 搜索 → 结果页 /xhs/words/<token>，
标题「<词> 小红书长尾关键词挖掘」，长尾词总量在 vom 的 emphasis 节点（共找到行前 ~25 行内取最后两个）。

用法: python mine_5118_xhs.py "音频裁剪" "markdown转word" --out xhs_words.csv
产出: xhs_words.csv (word, total, indexed, ts)
前提: bsk daemon 已启动；浏览器已登录 5118；截图不需要。
"""
import argparse, csv, os, re, subprocess, sys, time

ENV = {**os.environ, "BSK_AUTO_START": "0"}
LANDING = "https://www.5118.com/ci/xhs"


def bsk(*args, timeout=60):
    r = subprocess.run(["bsk", *args], capture_output=True, text=True,
                       encoding="utf-8", errors="ignore", env=ENV, timeout=timeout)
    return r.stdout + "\n" + r.stderr


def sync():
    return bsk("sync")


def wait_root(pattern, tries=8, delay=2.0):
    for _ in range(tries):
        t = sync()
        m = re.search(r'RootWebArea "([^"]*)"', t)
        if m and pattern in m.group(1):
            return m.group(1)
        time.sleep(delay)
    return None


def obs_id():
    m = re.search(r'"observation_id": "([^"]+)"', bsk("sync", "--json"))
    return m.group(1) if m else None


def dismiss_dialog():
    m = re.search(r'@e(\d+) button "确定"', sync())
    if m:
        bsk("click", f"@e{m.group(1)}")
        time.sleep(1)
    bsk("press", "Escape")


def parse_totals(dump):
    lines = dump.splitlines()
    idx = next((i for i, l in enumerate(lines) if "相关小红书长尾词共找到" in l), None)
    if idx is None:
        return "?", "?"
    nums = re.findall(r'emphasis "([\d,]+)"', " ".join(lines[max(0, idx - 25):idx]))
    # 小红书版布局只有一个数字节点（长尾词总量），全网版有两个（总量+有指数）
    if len(nums) >= 2:
        return nums[-2], nums[-1]
    if len(nums) == 1:
        return nums[-1], ""
    return "?", "?"


def do_word(word):
    o = obs_id()
    bsk("open", LANDING, "--observation", o) if o else bsk("open", LANDING)
    if not wait_root("长尾关键词", tries=6):
        return None, "FAIL landing"
    time.sleep(3)
    dismiss_dialog()
    filled = False
    for sel in ("input[type='text']:not([placeholder*='关键词'])",
                "input[type='text']", "input[placeholder*='搜索']"):
        out = bsk("fill", "--selector", sel, "--value", word)
        if "fill ok" in out:
            filled = True
            break
    if not filled:
        return None, "FAIL fill"
    time.sleep(1)
    m = re.search(r'@e(\d+) button "搜 索"', sync())
    if not m:
        return None, "FAIL no search btn"
    bsk("click", f"@e{m.group(1)}")
    # 5118 可能把查询词扩展成关联短语（如「简历制作」→「简历制作-免费模板…|在线制作个人简历」），
    # 因此只要求标题以「小红书长尾关键词挖掘」结尾
    title = wait_root("小红书长尾关键词挖掘", tries=10, delay=2.5)
    if not title:
        return None, "FAIL result page"
    time.sleep(4)
    total, indexed = parse_totals(sync())
    return (total, indexed), f"OK|{title}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words", nargs="+")
    ap.add_argument("--out", default="xhs_words.csv")
    ap.add_argument("--retry", type=int, default=2)
    args = ap.parse_args()

    new = not os.path.exists(args.out)
    with open(args.out, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["word", "total", "indexed", "matched_title", "ts"])
        for word in args.words:
            res, msg = None, ""
            for _ in range(args.retry + 1):
                try:
                    res, msg = do_word(word)
                except Exception as e:
                    res, msg = None, f"FAIL exc: {e}"
                if msg.startswith("OK"):
                    break
                time.sleep(4)
            if res:
                matched = msg[3:] if msg.startswith("OK|") else ""
                w.writerow([word, res[0], res[1], matched, time.strftime("%Y-%m-%d %H:%M")])
                f.flush()
                print(f"{word}: total={res[0]} matched={matched[:30]}", flush=True)
            else:
                print(f"{word}: {msg}", flush=True)
    print(f"done -> {args.out}")


if __name__ == "__main__":
    main()
