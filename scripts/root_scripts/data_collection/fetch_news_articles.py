import requests
from bs4 import BeautifulSoup
import time
import os
import json

# --- Helper function to fetch a single news article (reused from previous version) ---
def fetch_single_news_article(url):
    """
    Fetches a single news article page using requests with aggressive headers,
    and extracts its title, date, and content.
    """
    print(f"  Fetching article: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
        
        soup = BeautifulSoup(html, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "N/A"

        time_tag = soup.find('time')
        date = time_tag['datetime'] if time_tag and 'datetime' in time_tag.attrs else "N/A"

        article_container = soup.find('main', id='article-container')
        content_paragraphs = []
        if article_container:
            for section in article_container.find_all('section', recursive=False):
                for p_tag in section.find_all('p'):
                    content_paragraphs.append(p_tag.text.strip())
        content = "\n".join(content_paragraphs)

        news_data = {
            "title": title,
            "date": date,
            "content": content,
            "url": url
        }
        return news_data

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching article {url}: {e}")
        return None
    except Exception as e:
        print(f"  Error parsing article {url}: {e}")
        return None

# --- Main function to fetch and save multiple news articles ---
def fetch_and_save_news_articles(base_list_url, num_pages_to_scrape, output_filename="news_articles.jsonl"):
    """
    Fetches multiple news articles from a list page, extracts their content, and saves to JSONL.
    """
    all_news_data = []
    output_dir = os.path.join('D:', 'TradingAgents_AI_Cache', 'ai_training_data', 'raw', 'news_articles')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    for page_num in range(1, num_pages_to_scrape + 1):
        list_url = f"{base_list_url}?page={page_num}" # Assuming page parameter
        print(f"\n--- Fetching news list page: {list_url} ---")
        
        try:
            response = requests.get(list_url, headers=headers, timeout=10)
            response.raise_for_status()
            list_html = response.text
            soup = BeautifulSoup(list_html, 'html.parser')

            # Find all article links on the list page
            # Look for <a> tags with href starting with /news/id/
            article_links = soup.find_all('a', href=lambda href: href and href.startswith('/news/id/'))
            
            # Convert relative URLs to absolute URLs
            base_domain = "https://news.cnyes.com"
            article_urls = [base_domain + link['href'] for link in article_links]
            
            print(f"Found {len(article_urls)} articles on page {page_num}.")

            for article_url in article_urls:
                news_data = fetch_single_news_article(article_url)
                if news_data:
                    all_news_data.append(news_data)
                time.sleep(1) # Be polite to the server

        except requests.exceptions.RequestException as e:
            print(f"Error fetching list page {list_url}: {e}")
            break # Stop if list page fails
        except Exception as e:
            print(f"Error processing list page {list_url}: {e}")
            break

    # Save all collected news data to a JSONL file
    with open(output_path, 'w', encoding='utf-8') as f:
        for news_item in all_news_data:
            f.write(json.dumps(news_item, ensure_ascii=False) + '\n')

    print(f"\nSuccessfully scraped {len(all_news_data)} news articles and saved to: {output_path}")

if __name__ == '__main__':
    # Example: Scrape 3 pages of Taiwan stock news from Anue
    base_list_url = "https://news.cnyes.com/news/cat/tw_stock"
    num_pages_to_scrape = 3
    fetch_and_save_news_articles(base_list_url, num_pages_to_scrape)
