#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从公开 RSS 源抓取 AI / 大模型 / 科技新闻，写入 makapaka-data.json。
求职推送部分保留仓库内已有的常驻秋招岗位（秋招季岗位稳定），
仅在前一天有新增时才更新 jobs 字段。

运行环境：GitHub Actions（有网络、可 pip install feedparser）。
本地也可直接 `python update_data.py` 测试（需先 checkout 仓库）。
"""
import feedparser
import json
import re
import datetime
import os

FEEDS = [
    ("量子位",        "https://www.qbitai.com/feed"),
    ("机器之心",      "https://www.jiqizhixin.com/rss"),
    ("Hacker News",   "https://hnrss.org/frontpage"),
    ("The Verge AI",  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
]

NEWS_FILE = "makapaka-data.json"
AI_KEYWORDS = ["ai", "大模型", "模型", "智能体", "agent", "gpt", "gemini",
               "deepseek", "openai", "anthropic", "llm", "机器学习", "神经网络",
               "chatgpt", "claude", "人工智能", "芯片", "算力", "机器人"]


def clean(html):
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", "", html)
    return re.sub(r"\s+", " ", text).strip()


def is_ai_related(title, summary):
    blob = (title + " " + summary).lower()
    return any(k in blob for k in AI_KEYWORDS)


def main():
    today = datetime.date.today()
    date_str = f"{today.month}/{today.day}"

    news = []
    seen_links = set()

    for src, url in FEEDS:
        try:
            d = feedparser.parse(url)
        except Exception:
            continue
        for e in d.entries[:8]:
            title = clean(e.get("title", ""))
            link = e.get("link", "")
            summary = clean(e.get("summary", ""))[:220]
            if not title or not link or link in seen_links:
                continue
            if not is_ai_related(title, summary):
                continue
            seen_links.add(link)
            news.append({
                "id": "n" + str(abs(hash(link)) % 10**10),
                "type": "rss",
                "title": title,
                "src": src,
                "url": link,
                "date": date_str,
                "summary": summary,
            })
        if len(news) >= 10:
            break

    news = news[:8]

    # 读取仓库内已有数据，保留常驻求职岗位
    data = {}
    if os.path.exists(NEWS_FILE):
        try:
            data = json.load(open(NEWS_FILE, encoding="utf-8"))
        except Exception:
            data = {}

    jobs = data.get("jobs", [])
    jobs_updated = data.get("jobsUpdated", f"更新于 {date_str}")

    out = {
        "news": news,
        "jobs": jobs,
        "newsUpdated": f"更新于 {date_str}",
        "jobsUpdated": jobs_updated,
    }

    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"写入完成：news={len(news)} 条，jobs={len(jobs)} 条")


if __name__ == "__main__":
    main()
