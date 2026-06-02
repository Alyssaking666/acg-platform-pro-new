"""
Lofter爬虫API - 获取Lofter平台内容
"""
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

app = Flask(__name__)

@app.route('/api/lofter', methods=['GET'])
def search_lofter():
    """搜索Lofter内容"""
    keyword = request.args.get('keyword', '')
    content_type = request.args.get('type', 'all')  # all, article, image, text
    page = request.args.get('page', 1)
    
    if not keyword:
        return jsonify({'success': False, 'error': 'Keyword is required'}), 400
    
    try:
        # Lofter搜索
        search_url = f'https://www.lofter.com/search?q={keyword}&page={page}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.lofter.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        response = requests.get(search_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        
        # 解析文章
        articles = soup.select('.m-article, .post, .item')
        
        for article in articles:
            try:
                result = parse_lofter_article(article)
                if result:
                    results.append(result)
            except Exception as e:
                print(f'Error parsing article: {e}')
                continue
        
        # 如果没有找到内容，尝试备用解析方式
        if not results:
            results = parse_lofter_alternative(soup)
        
        return jsonify({
            'success': True,
            'keyword': keyword,
            'type': content_type,
            'page': page,
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def parse_lofter_article(article_elem):
    """解析单个Lofter文章"""
    try:
        # 标题
        title_elem = article_elem.select_one('.tit a, .title a, h2 a, h3 a')
        if not title_elem:
            return None
        
        title = title_elem.text.strip()
        url = title_elem.get('href', '')
        if url and not url.startswith('http'):
            url = 'https:' + url
        
        # 作者
        author_elem = article_elem.select_one('.author a, .user a, .name a')
        author = author_elem.text.strip() if author_elem else 'Unknown'
        author_url = author_elem.get('href', '') if author_elem else ''
        if author_url and not author_url.startswith('http'):
            author_url = 'https:' + author_url
        
        # 摘要/内容预览
        summary_elem = article_elem.select_one('.txt, .content, .summary, .desc')
        summary = summary_elem.text.strip()[:200] if summary_elem else ''
        
        # 图片
        images = []
        img_elems = article_elem.select('img')
        for img in img_elems[:3]:  # 最多取3张图片
            img_url = img.get('src', '')
            if img_url:
                if not img_url.startswith('http'):
                    img_url = 'https:' + img_url
                images.append(img_url)
        
        # 热度/互动数据
        popularity = 0
        hot_elem = article_elem.select_one('.hot, .view, .read')
        if hot_elem:
            hot_text = hot_elem.get_text()
            match = re.search(r'(\d+)', hot_text.replace(',', ''))
            if match:
                popularity = int(match.group(1))
        
        # 点赞数
        likes = 0
        like_elem = article_elem.select_one('.like, .favor')
        if like_elem:
            like_text = like_elem.get_text()
            match = re.search(r'(\d+)', like_text.replace(',', ''))
            if match:
                likes = int(match.group(1))
        
        # 评论数
        comments = 0
        comment_elem = article_elem.select_one('.comment, .reply')
        if comment_elem:
            comment_text = comment_elem.get_text()
            match = re.search(r'(\d+)', comment_text.replace(',', ''))
            if match:
                comments = int(match.group(1))
        
        # 发布时间
        time_elem = article_elem.select_one('.time, .date, .pubtime')
        published_at = time_elem.text.strip() if time_elem else datetime.now().isoformat()
        
        # 标签
        tags = []
        tag_elems = article_elem.select('.tag a, .tags a')
        for t in tag_elems:
            tags.append(t.text.strip())
        
        # 判断内容类型
        content_type = 'article'
        if images and not summary:
            content_type = 'image'
        elif images and summary:
            content_type = 'mixed'
        
        return {
            'title': title,
            'author': author,
            'author_url': author_url,
            'platform': 'lofter',
            'content_type': content_type,
            'content_url': url,
            'summary': summary,
            'images': images,
            'popularity': popularity or likes,
            'likes': likes,
            'comments': comments,
            'tags': tags if tags else ['同人文'],
            'published_at': published_at
        }
        
    except Exception as e:
        print(f'Error in parse_lofter_article: {e}')
        return None

def parse_lofter_alternative(soup):
    """备用解析方式"""
    results = []
    
    # 尝试其他选择器
    selectors = [
        '.search-result .item',
        '.result-list .post',
        '.content-list article',
        '.m-list .item'
    ]
    
    for selector in selectors:
        items = soup.select(selector)
        for item in items:
            try:
                # 尝试提取基本信息
                title = item.get_text()[:50] if item else 'Untitled'
                
                # 查找链接
                link = item.find('a')
                url = link.get('href', '') if link else ''
                if url and not url.startswith('http'):
                    url = 'https:' + url
                
                results.append({
                    'title': title,
                    'author': 'Unknown',
                    'platform': 'lofter',
                    'content_type': 'article',
                    'content_url': url,
                    'summary': item.get_text(strip=True)[:150],
                    'popularity': 0,
                    'tags': ['同人文'],
                    'published_at': datetime.now().isoformat()
                })
            except:
                continue
        
        if results:
            break
    
    return results

@app.route('/api/lofter/user/<username>', methods=['GET'])
def get_user_posts(username):
    """获取指定用户的文章"""
    try:
        user_url = f'https://{username}.lofter.com/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(user_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        posts = []
        post_elems = soup.select('.post, .article, .item')
        
        for post in post_elems[:20]:
            result = parse_lofter_article(post)
            if result:
                posts.append(result)
        
        return jsonify({
            'success': True,
            'username': username,
            'count': len(posts),
            'posts': posts
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/lofter/tag/<tag>', methods=['GET'])
def get_tag_posts(tag):
    """获取指定标签的文章"""
    try:
        tag_url = f'https://www.lofter.com/tag/{tag}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(tag_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        posts = []
        post_elems = soup.select('.post, .article, .item')
        
        for post in post_elems[:20]:
            result = parse_lofter_article(post)
            if result:
                posts.append(result)
        
        return jsonify({
            'success': True,
            'tag': tag,
            'count': len(posts),
            'posts': posts
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Vercel handler
def handler(request):
    with app.request_context(request.environ):
        return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True, port=5003)
