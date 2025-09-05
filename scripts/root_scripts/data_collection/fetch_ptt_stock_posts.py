import requests
from bs4 import BeautifulSoup
import time
import os
import json
import yaml

BASE_URL = "https://www.ptt.cc"

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"}

def get_article_links(board, pages=1):
    """抓取某看板最新的文章連結 (預設 1 頁)"""
    links = []
    for page in range(pages):
        url = f"{BASE_URL}/bbs/{board}/index{page}.html"
        print(f"  Fetching list page: {url}")
        try:
            # Use the over18 cookie to bypass age verification
            res = requests.get(url, headers=headers, cookies={'over18': '1'}, timeout=10)
            res.raise_for_status()
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, "html.parser")

            # Find all article links on the list page
            # Look for <a> tags within div.r-ent (each article entry)
            for entry in soup.find_all('div', class_='r-ent'):
                link_tag = entry.find('a')
                if link_tag and link_tag.get('href'):
                    full_url = BASE_URL + link_tag['href']
                    links.append(full_url)
            time.sleep(1)  # Be polite to the server
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching list page {url}: {e}")
            break
    return links


def parse_article(url, board):
    """
    解析單篇文章，回傳標題、內文、推文
    Adapted for www.ptt.cc structure.
    """
    print(f"  Parsing article: {url}")
    try:
        # Use the over18 cookie to bypass age verification
        res = requests.get(url, headers=headers, cookies={'over18': '1'}, timeout=10)
        res.raise_for_status()
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # --- Extract Metadata (Title, Author, Date) ---
        # Find the main content div first, as meta info is within it
        main_content_div = soup.find('div', id='main-content')
        if not main_content_div:
            print("Error: Could not find main-content div.")
            return None

        title = "N/A"
        author = "N/A"
        date = "N/A"
        
        # Metadata is in div.article-metaline and div.article-metaline-right
        meta_lines = main_content_div.find_all('div', class_=['article-metaline', 'article-metaline-right'])
        for meta_line in meta_lines:
            tag = meta_line.find('span', class_='article-meta-tag')
            value = meta_line.find('span', class_='article-meta-value')
            if tag and value:
                if tag.text.strip() == '作者':
                    author = value.text.strip()
                elif tag.text.strip() == '標題':
                    title = value.text.strip()
                elif tag.text.strip() == '時間':
                    date = value.text.strip()

        # --- Extract Main Content ---
        main_content_div = soup.find('div', id='main-content')
        content = ""
        if main_content_div:
            # Create a copy of the main_content_div to manipulate without affecting other finds
            content_copy = BeautifulSoup(str(main_content_div), 'html.parser')

            # Remove elements that are NOT part of the main article text
            for tag in content_copy.find_all('div', class_=['article-metaline', 'article-metaline-right', 'push', 'richcontent']):
                tag.decompose()
            
            # Get all remaining text, handling <br> tags as newlines
            content = content_copy.get_text(separator='\n', strip=True)

        # --- Extract Comments (推文) ---
        comments = []
        # Comments are typically in div.push tags
        for push_tag in soup.find_all('div', class_='push'): # Use original soup for comments
            tag = push_tag.find('span', class_='push-tag').text.strip() if push_tag.find('span', class_='push-tag') else "N/A"
            user = push_tag.find('span', class_='push-userid').text.strip() if push_tag.find('span', class_='push-userid') else "N/A"
            comment_content = push_tag.find('span', class_='push-content').text.strip() if push_tag.find('span', class_='push-content') else "N/A"
            timestamp = push_tag.find('span', class_='push-ipdatetime').text.strip() if push_tag.find('span', class_='push-ipdatetime') else "N/A"
            comments.append({
                "tag": tag,
                "user": user,
                "content": comment_content,
                "timestamp": timestamp
            })

        ptt_data = {
            "title": title,
            "author": author,
            "date": date,
            "content": content,
            "comments": comments,
            "url": url
        }
        return ptt_data

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching article {url}: {e}")
        return None
    except Exception as e:
        print(f"  Error parsing article {url}: {e}")
        return None


def fetch_and_save_ptt_posts(board, num_pages_to_scrape, output_filename="ptt_posts.jsonl"):
    """
    Fetches multiple PTT posts from a board, extracts their content, and saves to JSONL.
    """
    all_posts_data = []
    
    # Load output directory from config
    try:
        with open("configs/data_sources.yaml", 'r', encoding='utf-8') as f:
            data_cfg = yaml.safe_load(f)
        storage_base = data_cfg['storage']['base_path']
        raw_subdir = data_cfg['storage']['raw_subdir']
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    output_dir = os.path.join(storage_base, raw_subdir, 'social_media_posts')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    print(f"Starting PTT post scraping for board '{board}'...")

    article_links = get_article_links(board, pages=num_pages_to_scrape)
    print(f"Found {len(article_links)} articles to scrape.")

    for i, link in enumerate(article_links):
        post_data = parse_article(link, board)
        if post_data:
            all_posts_data.append(post_data)
        time.sleep(1) # Be polite to the server

    # Save all collected news data to a JSONL file
    with open(output_path, 'w', encoding='utf-8') as f:
        for post_item in all_posts_data:
            f.write(json.dumps(post_item, ensure_ascii=False) + '\n')

    print(f"\nSuccessfully scraped {len(all_posts_data)} PTT posts and saved to: {output_path}")


# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()

if __name__ == "__main__":
    # Example: Scrape 3 pages of Stock board posts from pttweb.cc
    BOARD_NAME = "Stock"
    NUM_PAGES = 3
    fetch_and_save_ptt_posts(BOARD_NAME, NUM_PAGES)
