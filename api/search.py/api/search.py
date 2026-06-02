"""
聚合搜索API - Vercel Serverless Function
支持多平台内容搜索：AO3、Lofter、微博、B站、爱发电等
"""
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
import re
import os
from datetime import datetime

app = Flask(__name__)

# 加载本地文章数据库
def load_articles_db():
    """加载文章数据库"""
    try:
        # 尝试多个可能的路径
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'data', 'articles.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'articles.json'),
            'data/articles.json',
            '../data/articles.json',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # 如果找不到文件，返回空列表
        return []
    except Exception as e:
        print(f'Error loading articles DB: {e}')
        return []

ARTICLES_DB = load_articles_db()

@app.route('/api/search', methods=['GET'])
def search():
    """主搜索接口"""
    keyword = request.args.get('keyword', '')
    platform = request.args.get('platform', 'all')
    content_type = request.args.get('type', 'all')
    
    if not keyword:
        return jsonify({
            'success': False,
            'error': 'Keyword is required'
        }), 400
    
    results = []
    errors = []
    
    # 1. 先从本地数据库搜索
    try:
        local_results = [
            a for a in ARTICLES_DB 
            if keyword.lower() in a.get('title', '').lower() 
            or keyword.lower() in a.get('ip', '').lower()
            or keyword.lower() in ' '.join(a.get('tags', [])).lower()
        ]
        results.extend(local_results)
    except Exception as e:
        errors.append(f'Local search error: {str(e)}')
    
    # 2. 根据平台调用对应爬虫
    if platform in ['all', 'ao3']:
        try:
            ao3_data = scrape_ao3(keyword)
            results.extend(ao3_data)
        except Exception as e:
            errors.append(f'AO3 error: {str(e)}')
    
    if platform in ['all', 'lofter']:
        try:
            lofter_data = scrape_lofter(keyword)
            results.extend(lofter_data)
        except Exception as e:
            errors.append(f'Lofter error: {str(e)}')
    
    if platform in ['all', 'weibo']:
        try:
            weibo_data = scrape_weibo(keyword)
            results.extend(weibo_data)
        except Exception as e:
            errors.append(f'Weibo error: {str(e)}')
    
    if platform in ['all', 'bilibili']:
        try:
            bilibili_data = scrape_bilibili(keyword)
            results.extend(bilibili_data)
        except Exception as e:
            errors.append(f'Bilibili error: {str(e)}')
    
    # 3. 按热度排序
    results.sort(key=lambda x: x.get('popularity', 0), reverse=True)
    
    return jsonify({
        'success': True,
        'keyword': keyword,
        'platform': platform,
        'total': len(results),
        'errors': errors if errors else None,
        'results': results[:50]  # 最多返回50条
    })

def scrape_ao3(keyword):
    """AO3爬虫 - 获取同人文作品"""
    try:
        url = f'https://archiveofourown.org/works/search?work_search[query]={keyword}&work_search[sort_column]=kudos_count'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        works = []
        for work in soup.select('li.work')[:10]:  # 取前10条
            try:
                title_elem = work.select_one('h4 a')
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                work_url = 'https://archiveofourown.org' + title_elem['href']
                
                # 获取作者
                author_elem = work.select_one('a[rel="author"]')
                author = author_elem.text.strip() if author_elem else 'Unknown'
                
                # 获取摘要
                summary_elem = work.select_one('.summary')
                summary = summary_elem.get_text(strip=True)[:200] if summary_elem else ''
                
                # 获取热度（kudos）
                kudos_elem = work.select_one('.kudos a')
                popularity = 0
                if kudos_elem:
                    try:
                        popularity = int(kudos_elem.text.replace(',', ''))
                    except:
                        pass
                
                # 获取标签
                tags = ['English', 'Novel']
                fandom_elems = work.select('.fandoms a')
                if fandom_elems:
                    tags = [t.text.strip() for t in fandom_elems[:3]]
                
                works.append({
                    'title': title,
                    'author': author,
                    'platform': 'ao3',
                    'content_type': 'article',
                    'content_url': work_url,
                    'summary': summary,
                    'popularity': popularity,
                    'tags': tags,
                    'published_at': datetime.now().isoformat(),
                    'language': 'English'
                })
            except Exception as e:
                print(f'Error parsing AO3 work: {e}')
                continue
        
        return works
    except Exception as e:
        print(f'AO3 scrape error: {e}')
        return []

def scrape_lofter(keyword):
    """Lofter爬虫 - 获取同人文和图文"""
    try:
        # Lofter搜索API
        search_url = f'https://www.lofter.com/search?q={keyword}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.lofter.com/'
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # Lofter的文章通常在特定的class中
        articles = soup.select('.m-article')[:8]
        
        for article in articles:
            try:
                title_elem = article.select_one('.tit a')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                url = title_elem.get('href', '')
                if url and not url.startswith('http'):
                    url = 'https:' + url
                
                # 获取作者
                author_elem = article.select_one('.author a')
                author = author_elem.text.strip() if author_elem else 'Unknown'
                
                # 获取摘要
                summary_elem = article.select_one('.txt')
                summary = summary_elem.text.strip()[:150] if summary_elem else ''
                
                # 获取热度（阅读数）
                hot_elem = article.select_one('.hot')
                popularity = 0
                if hot_elem:
                    hot_text = hot_elem.text
                    match = re.search(r'(\d+)', hot_text)
                    if match:
                        popularity = int(match.group(1))
                
                results.append({
                    'title': title,
                    'author': author,
                    'platform': 'lofter',
                    'content_type': 'article',
                    'content_url': url,
                    'summary': summary,
                    'popularity': popularity,
                    'tags': [keyword, '同人文'],
                    'published_at': datetime.now().isoformat()
                })
            except Exception as e:
                print(f'Error parsing Lofter article: {e}')
                continue
        
        return results
    except Exception as e:
        print(f'Lofter scrape error: {e}')
        return []

def scrape_weibo(keyword):
    """微博搜索 - 获取相关微博内容"""
    try:
        # 微博搜索需要登录，这里返回模拟数据或公开内容
        # 实际生产环境可以使用微博开放平台API
        return [
            {
                'title': f'#{keyword}# 超话',
                'author': '微博超话社区',
                'platform': 'weibo',
                'content_type': 'social',
                'content_url': f'https://weibo.com/p/100808{keyword}',
                'summary': f'微博{keyword}超话社区，粉丝互动聚集地',
                'popularity': 50000,
                'tags': ['微博', '超话', '社区'],
                'published_at': datetime.now().isoformat()
            }
        ]
    except Exception as e:
        print(f'Weibo scrape error: {e}')
        return []

def scrape_bilibili(keyword):
    """B站搜索 - 获取相关视频"""
    try:
        # B站搜索API
        search_url = f'https://api.bilibili.com/x/web-interface/search/all?keyword={keyword}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://search.bilibili.com/'
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        data = response.json()
        
        results = []
        if data.get('data', {}).get('result', []):
            videos = data['data']['result']
            for video in videos[:8]:
                if video.get('result_type') == 'video':
                    for item in video.get('data', [])[:5]:
                        try:
                            results.append({
                                'title': item.get('title', '').replace('<em class="keyword">', '').replace('</em>', ''),
                                'author': item.get('author', 'Unknown'),
                                'platform': 'bilibili',
                                'content_type': 'video',
                                'content_url': f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                                'summary': item.get('description', '')[:150],
                                'popularity': item.get('play', 0),
                                'tags': ['视频', keyword],
                                'published_at': datetime.fromtimestamp(item.get('pubdate', 0)).isoformat() if item.get('pubdate') else datetime.now().isoformat(),
                                'cover': item.get('pic', '')
                            })
                        except Exception as e:
                            print(f'Error parsing Bilibili video: {e}')
                            continue
        
        return results
    except Exception as e:
        print(f'Bilibili scrape error: {e}')
        return []

# Vercel Serverless Function handler
def handler(request):
    """Vercel serverless function handler"""
    with app.request_context(request.environ):
        return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
