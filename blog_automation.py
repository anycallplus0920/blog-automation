# blog_automation.py
import feedparser
import requests
import json

# RSS 피드 목록
RSS_FEEDS = [
    "https://www.printweek.com/rss",
    "https://www.packagingdigest.com/rss",
]

# 키워드 필터
KEYWORDS = ["잉크젯", "프린터", "인쇄", "라벨", "패키징"]

def get_latest_posts():
    posts = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:3]:  # 최신 3개
            if any(keyword in entry.title.lower() or keyword in entry.summary.lower() for keyword in KEYWORDS):
                posts.append({
                    'title': entry.title,
                    'content': entry.summary,
                    'link': entry.link,
                    'published': entry.published
                })
    return posts

def save_to_file(posts):
    with open('collected_posts.json', 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    posts = get_latest_posts()
    save_to_file(posts)
    print(f"수집된 포스트: {len(posts)}개")
