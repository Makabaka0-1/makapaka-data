#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从公开 RSS 源抓取行业动态，写入 makapaka-data.json。
内容范围：
  1. 大厂 / 国内著名 AI 公司的技术动态（模型更新、产品发布等）
  2. 大厂组织 / 人事变动（高管离职、入职、组织架构调整等）
求职推送部分保留仓库内已有的常驻秋招岗位。

运行环境：GitHub Actions（有网络、可 pip install feedparser）。
"""
import feedparser
import json
import re
import datetime
import os

FEEDS = [
    # 国内 AI 专业媒体（模型更新 / 技术动态）
    ("量子位",        "https://www.qbitai.com/feed"),
    ("机器之心",      "https://www.jiqizhixin.com/rss"),
    # 国内科技综合媒体（大厂组织 / 人事变动）
    ("36氪",          "https://36kr.com/feed"),
    ("IT之家",        "https://www.ithome.com/rss/"),
    # 海外 AI / 科技
    ("Hacker News",   "https://hnrss.org/frontpage"),
    ("The Verge AI",  "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
]

NEWS_FILE = "makapaka-data.json"

# AI 技术关键词
AI_KEYWORDS = ["ai", "大模型", "模型", "智能体", "agent", "gpt", "gemini",
               "deepseek", "openai", "anthropic", "llm", "机器学习", "神经网络",
               "chatgpt", "claude", "人工智能", "芯片", "算力", "机器人",
               "多模态", "vlm", "diffusion", "sora", "scaling"]

# 大厂 / 国内著名 AI 公司名
BIGTECH = ["阿里", "阿里巴巴", "阿里云", "通义", "字节", "抖音", "飞书", "豆包",
           "腾讯", "混元", "百度", "文心", "美团", "京东", "小米", "华为", "盘古",
           "网易", "快手", "拼多多", "滴滴", "b站", "哔哩哔哩", "微软", "谷歌", "google",
           "meta", "facebook", "苹果", "apple", "openai", "anthropic", "deepseek",
           "月之暗面", "kimi", "智谱", "百川", "商汤", "旷视", "科大讯飞", "mistral",
           "perplexity", "阶跃", "minimax", "零一", "出门问问", "面壁", "蔚来",
           "理想", "小鹏", "大疆", "联发科", "英伟达", "nvidia"]

# 人事 / 组织变动关键词
HR_KEYWORDS = ["离职", "辞任", "卸任", "辞去", "加盟", "入职", "出任",
               "升任", "履新", "任命", "调任", "轮岗", "转岗", "组织架构", "人事变动",
               "高管", "总裁", "副总裁", "ceo", "cto", "cfo", "coo", "合伙人",
               "架构调整", "业务调整", "裁员", "优化", "毕业", "反腐", "被查",
               "创业"]


def clean(html):
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", "", html)
    return re.sub(r"\s+", " ", text).strip()


COMPREHENSIVE = {"36氪", "IT之家"}  # 综合科技源，需限定大厂避免消费电子噪音

def is_relevant(src, title, summary):
    """筛选：AI 技术动态，或 大厂组织/人事变动"""
    blob = (title + " " + summary).lower()
    has_big = any(k in blob for k in BIGTECH)
    has_hr = any(k in blob for k in HR_KEYWORDS)
    # 综合源（36氪/IT之家）：必须大厂相关，避免小品牌消费电子混入
    if src in COMPREHENSIVE:
        if not has_big:
            return False
        return any(k in blob for k in AI_KEYWORDS) or has_hr
    # 专业 AI 源：AI 技术词 或 (大厂 + 人事)
    if any(k in blob for k in AI_KEYWORDS):
        return True
    if has_big and has_hr:
        return True
    return False


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
        for e in d.entries[:10]:
            title = clean(e.get("title", ""))
            link = e.get("link", "")
            summary = clean(e.get("summary", ""))[:220]
            if not title or not link or link in seen_links:
                continue
            if not is_relevant(src, title, summary):
                continue
            seen_links.add(link)
            # 标记分类，方便前端区分「技术」与「人事动态」
            blob = (title + " " + summary).lower()
            category = "动态" if any(k in blob for k in HR_KEYWORDS) else "技术"
            news.append({
                "id": "n" + str(abs(hash(link)) % 10**10),
                "type": "rss",
                "category": category,
                "title": title,
                "src": src,
                "url": link,
                "date": date_str,
                "summary": summary,
            })
        if len(news) >= 12:
            break

    news = news[:10]

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
