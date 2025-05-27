# blog_automation.py
import requests
from bs4 import BeautifulSoup
import json
import re
import time

# 수집할 블로그 주소 (2개 블로그)
BLOG_URLS = [
    "https://blog.naver.com/best-marking",
    "https://blog.naver.com/ijehkorea"  # 마켐이마지 국내 공식1호 대리점 아이제코리아
]

# 제거할 키워드 (내용에서 삭제할 단어들)
REMOVE_KEYWORDS = [
    "공식대리점", "공식 대리점", "대리점", "대리점업체", 
    "총대리점", "공식총대리점", "정식대리점", "독점대리점",
    "영업대행", "판매대행", "판매처", "취급점"
]

def clean_text(text):
    """
    텍스트에서 불필요한 키워드를 제거합니다.
    """
    cleaned_text = text
    removed_words = []
    
    for keyword in REMOVE_KEYWORDS:
        if keyword in cleaned_text:
            cleaned_text = cleaned_text.replace(keyword, "")
            removed_words.append(keyword)
    
    # 연속된 공백 정리
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    if removed_words:
        print(f"    🧹 제거된 단어: {', '.join(removed_words)}")
    
    return cleaned_text

def get_blog_links(blog_url, max_posts=15):
    """
    블로그 메인에서 최신 글 링크를 가져옵니다.
    """
    try:
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
            if len(post_links) >= max_posts * 2:  # 여유분 확보
                break
        
        print(f"  블로그에서 {len(post_links)}개 링크 발견")
        return post_links[:max_posts * 2]
        
    except Exception as e:
        print(f"  ❌ 블로그 링크 수집 실패: {e}")
        return []

def extract_post_content(post_url):
    """
    네이버 블로그 글 본문 추출
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(post_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # iframe 주소 추출
        iframe = soup.find("iframe", {"id": "mainFrame"})
        if iframe:
            iframe_url = "https://blog.naver.com" + iframe["src"]
            res = requests.get(iframe_url, headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
        
        # 본문 내용 추출 (여러 방법 시도)
        content = ""
        
        # 방법 1: se-main-container
        content_div = soup.find("div", {"class": "se-main-container"})
        if content_div:
            content = content_div.get_text(separator="\n").strip()
        
        # 방법 2: postViewArea
        if not content:
            content_div = soup.find("div", id=re.compile("postViewArea"))
            if content_div:
                content = content_div.get_text(separator="\n").strip()
        
        # 방법 3: se-component 모든 요소
        if not content:
            components = soup.find_all("div", class_=re.compile("se-component"))
            content = "\n".join([comp.get_text(strip=True) for comp in components if comp.get_text(strip=True)])
        
        # 제목 추출 (여러 방법 시도)
        title = ""
        
        # 방법 1: se_textarea
        title_tag = soup.find("h3", {"class": "se_textarea"})
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        # 방법 2: pcol1
        if not title:
            title_tag = soup.find("div", class_="pcol1")
            if title_tag:
                title = title_tag.get_text(strip=True)
        
        # 방법 3: title 태그
        if not title:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True).replace(" : 네이버 블로그", "")
        
        # 기본값 설정
        if not title:
            title = "제목 추출 실패"
        if not content:
            content = "본문 추출 실패"
        
        # 키워드 제거 (제목과 내용에서)
        cleaned_title = clean_text(title)
        cleaned_content = clean_text(content[:1000])  # 처음 1000자만 저장
        
        return {
            "title": cleaned_title,
            "link": post_url,
            "content": cleaned_content
        }
        
    except Exception as e:
        print(f"    ❌ 본문 추출 실패: {e}")
        return {
            "title": "추출 실패",
            "link": post_url,
            "content": f"오류: {str(e)}"
        }

def main():
    collected = []
    
    print("=== 네이버 블로그 자동 수집 시작 ===")
    
    for i, blog_url in enumerate(BLOG_URLS, 1):
        print(f"\n[{i}/{len(BLOG_URLS)}] 블로그 수집: {blog_url}")
        
        # 블로그 링크 수집 (15개씩 수집)
        links = get_blog_links(blog_url, max_posts=15)
        
        valid_posts = 0
        for j, link in enumerate(links, 1):
            if valid_posts >= 15:  # 블로그당 최대 15개
                break
                
            print(f"  [{j}] 수집 중: {link}")
            
            # 본문 추출 (키워드는 자동으로 제거됨)
            post = extract_post_content(link)
            
            # 수집 성공
            collected.append(post)
            valid_posts += 1
            print(f"    ✅ 수집 완료: {post['title'][:50]}...")
            
            # 네이버 차단 방지를 위한 대기 (대량 수집 시 약간 늘림)
            time.sleep(2)
    
    # 결과 저장
    with open("collected_posts.json", "w", encoding="utf-8") as f:
        json.dump(collected, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 수집 완료 ===")
    print(f"✅ 총 수집된 글: {len(collected)}개")
    print(f"📁 저장 파일: collected_posts.json")
    print(f"🧹 모든 글에서 대리점 관련 단어가 자동 삭제되었습니다.")
    
    # 수집된 글 제목 미리보기
    if collected:
        print(f"\n=== 수집된 글 제목 ===")
        for i, post in enumerate(collected, 1):
            print(f"{i}. {post['title']}")

if __name__ == "__main__":
    main()
