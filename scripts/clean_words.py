#!/usr/bin/env python
"""阶段2 清洗（修正版）：去疑问词 -> 分词 -> 去无效词(排除对象词白名单) -> 聚类 -> 每类选最短代表词。
对应 references/02-cleaning.md。实测教训已内置：
  1) 全局词频 top 会把对象词(图片/音频/水印...)误判为无效词 —— 对象词白名单强制保留；
  2) 代表词必须选最短（"markdown转word在线编辑器"查得0条，"markdown转word"查得100条）。
用法（sidehustle-work/ 下）: python <skill>/scripts/clean_words.py --mine-dir 01_mining --out-dir 02_cleaned
"""
import argparse, csv, glob, os, re, sys

try:
    import jieba
except ImportError:
    sys.exit("需要 jieba: pip install jieba（且不能用 python -I 运行本脚本）")

# 疑问/延伸词表：长尾词包含即整词去除（references/02-cleaning.md）
QUESTION_WORDS = list(
    "哪里 哪有 哪个 哪能 哪几 哪样 哪种 哪些 那个 那些 多少 几个 几种 有啥 什么 怎么 怎样 "
    "有没有 能不能 是不是 要不要 好不好 行不行 够不够 可不可以 能不能够 "
    "不够 不行 不好 不会 不能 无法 无需 不了 不可以 没办法 "
    "好用 最好 不用 没有 可以 还是 需要 好吗 好么 可能 大概 大约 应该 如何 怎么样".split()
)
# 通用无效词（不体现需求核心）
GENERIC = {"在线", "工具", "软件", "免费", "下载", "版", "手机", "app", "小程序",
           "最新", "官方", "正版", "安装", "大全", "合集", "排行", "推荐", "网站",
           "使用", "方法", "教程", "步骤", "介绍", "怎么样", "如何"}
# 对象词白名单：承载需求核心的"事物"，即使词频再高也不当无效词（实测教训 1）
OBJECT_WORDS = {"图片", "照片", "文本", "文字", "文档", "音频", "视频", "语音", "文章",
                "mp3", "pdf", "word", "ppt", "excel", "markdown", "html", "水印",
                "字幕", "直播", "群", "好友", "通讯录", "压缩", "转换", "转", "裁剪",
                "剪辑", "提取", "识别", "编辑", "编辑器", "格式"}
CJK_RUN = re.compile(r"[\u4e00-\u9fa5A-Za-z0-9]+")


def tokens(word):
    out = []
    for seg in CJK_RUN.findall(word):
        if re.fullmatch(r"[A-Za-z0-9]+", seg):
            out.append(seg.lower())
        else:
            out.extend(t.strip() for t in jieba.cut(seg) if t.strip())
    return [t.lower() for t in out if t]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mine-dir", default="01_mining")
    ap.add_argument("--out-dir", default="02_cleaned")
    ap.add_argument("--top-generic", type=int, default=15)
    ap.add_argument("--extra-objects", nargs="*", default=[], help="补充对象词")
    args = ap.parse_args()

    objects = {o.lower() for o in OBJECT_WORDS | set(args.extra_objects)}

    all_words, freq = [], {}
    for path in glob.glob(os.path.join(args.mine_dir, "words_*.csv")):
        with open(path, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                w = (row.get("word") or "").strip()
                if w:
                    all_words.append(w)
    all_words = sorted(set(all_words))
    for w in all_words:
        for t in tokens(w):
            freq[t] = freq.get(t, 0) + 1

    # 无效词 = 通用词 ∪ 词频top，但强制剔除对象词白名单（实测教训 1）
    top = [t for t, _ in sorted(freq.items(), key=lambda x: -x[1])[:args.top_generic]]
    generic = (set(GENERIC) | set(top)) - objects
    print(f"[info] 无效词({len(generic)}): {sorted(generic)}", file=sys.stderr)

    kept = [w for w in all_words if not any(q in w for q in QUESTION_WORDS)]
    print(f"[info] 总词 {len(all_words)}，疑问词去除 {len(all_words)-len(kept)}，剩 {len(kept)}", file=sys.stderr)

    clusters, no_key = {}, 0
    for w in kept:
        core = [t for t in dict.fromkeys(tokens(w)) if t not in generic]
        if not core:
            no_key += 1
            continue
        key = ",".join(sorted(set(core)))
        clusters.setdefault(key, []).append(w)
    print(f"[info] 聚类 {len(clusters)} 类，无法提取核心词丢弃 {no_key}", file=sys.stderr)

    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "representatives.csv"), "w", newline="",
              encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["cluster_key", "representative", "group_size", "members"])
        for key, ws in sorted(clusters.items(), key=lambda x: -len(x[1])):
            rep = min(ws, key=len)  # 代表词选最短（实测教训 2）
            w.writerow([key, rep, len(ws), "|".join(ws[:10])])
    with open(os.path.join(args.out_dir, "global_freq.csv"), "w", newline="",
              encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["token", "count"])
        for t, c in sorted(freq.items(), key=lambda x: -x[1]):
            w.writerow([t, c])
    print(f"done -> {args.out_dir}/representatives.csv & global_freq.csv")


if __name__ == "__main__":
    main()
