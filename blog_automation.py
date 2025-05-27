# blog_automation.py
import requests
from bs4 import BeautifulSoup
import json
import re
import time

# 수집할 블로그 주소 (회사 공식 블로그)
BLOG_URLS = [
    "https://blog.naver.com/best-marking"
]

def get_blog_links(blog_url, max_posts=5):
    """
    블로그 메인에서 최신 글 링크를 가져옵니다.
    """
    blog_id = blog_url.split("/")[-1]
    base = f"https://blog.naver.com/PostList.naver?blogId={blog_id}"
    resp = requests.get(base, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(resp.text, "html.parser")

    scripts = soup.find_all("script")
    post_links = []

    for script in scripts:
        if "logNo=" in script.text:
            found = re.findall(r"logNo=(\d+)", script.text)
            for log in found:
                link = f"https://blog.naver.com/{blog_id}/{log}"
                if link not in post_links:
                    post_links.append(link)
        if len(post_links) >= max_posts:
            break

    return post_links[:max_posts]

def extract_post_content(post_url):
    """
    네이버 블로그 글 본문 추출
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(post_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    # iframe 주소 추출
    iframe = soup.find("iframe", {"id": "mainFrame"})
    if iframe:
        iframe_url = "https://blog.naver.com" + iframe["src"]
        res = requests.get(iframe_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

    # 본문 내용 추출
    content_div = soup.find("div", {"class": "se-main-container"})
    if not content_div:
        content_div = soup.find("div", id=re.compile("postViewArea"))
    content = content_div.get_text(separator="\n").strip() if content_div else "본문 추출 실패"

    # 제목
    title_tag = soup.find("h3", {"class": "se_textarea"})
    if not title_tag:
        title_tag = soup.find("div", class_="pcol1")
    title = title_tag.get_text(strip=True) if title_tag else "제목 없음"

    return {
        "title": title,
        "link": post_url,
        "content": content
    }

def main():
    collected = []
    for blog_url in BLOG_URLS:
        links = get_blog_links(blog_url)
        for link in links:
            print(f"수집 중: {link}")
            post = extract_post_content(link)
            collected.append(post)
            time.sleep(2)  # 네이버 차단 방지

    with open("collected_posts.json", "w", encoding="utf-8") as f:
        json.dump(collected, f, ensure_ascii=False, indent=2)

    print(f"총 {len(collected)}개 글 수집 완료")

if __name__ == "__main__":
    main()
