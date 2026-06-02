"""
AO3爬虫API - 专门用于获取Archive of Our Own内容
"""
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

@app.route('/api/ao3', methods=['GET'])
def search_ao3():
    """搜索AO3作品"""
    keyword = request.args.get('keyword', '')
    sort_by = request.args.get('sort', 'kudos')  # kudos, hits, comments, bookmarks
    page = request.args.get('page', 1)
    
    if not keyword:
        return jsonify({'success': False, 'error': 'Keyword is required'}), 400
    
    try:
        # 构建排序参数
        sort_column = {
            'kudos': 'kudos_count',
            'hits': 'hits',
            'comments': 'comments_count',
            'bookmarks': 'bookmarks_count',
            'date': 'revised_at'
        }.get(sort_by, 'kudos_count')
        
        url = f'https://archiveofourown.org/works/search?work_search[query]={keyword}&work_search[sort_column]={sort_column}&page={page}'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        works = []
        
        # 解析作品列表
        for work in soup.select('li.work'):
            try:
                work_data = parse_work_item(work)
                if work_data:
                    works.append(work_data)
            except Exception as e:
                print(f'Error parsing work: {e}')
                continue
        
        # 获取总结果数
        total_elem = soup.select_one('.pagination .current')
        total = len(works)
        if total_elem:
            total_text = total_elem.get_text()
            # 尝试提取数字
            import re
            numbers = re.findall(r'(\d+)', total_text)
            if numbers:
                total = int(numbers[-1])
        
        return jsonify({
            'success': True,
            'keyword': keyword,
            'sort_by': sort_by,
            'page': page,
            'total': total,
            'count': len(works),
            'works': works
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def parse_work_item(work_elem):
    """解析单个作品元素"""
    try:
        # 标题和链接
        title_elem = work_elem.select_one('h4 a')
        if not title_elem:
            return None
        
        title = title_elem.text.strip()
        work_url = 'https://archiveofourown.org' + title_elem['href']
        work_id = title_elem['href'].split('/')[2] if '/works/' in title_elem['href'] else None
        
        # 作者
        author_elem = work_elem.select_one('a[rel="author"]')
        author = author_elem.text.strip() if author_elem else 'Anonymous'
        author_url = 'https://archiveofourown.org' + author_elem['href'] if author_elem else None
        
        # 同人圈/Fandoms
        fandoms = []
        fandom_elems = work_elem.select('.fandoms a')
        for f in fandom_elems:
            fandoms.append({
                'name': f.text.strip(),
                'url': 'https://archiveofourown.org' + f['href']
            })
        
        # 配对/CP
        relationships = []
        rel_elems = work_elem.select('li.relationships a')
        for r in rel_elems:
            relationships.append(r.text.strip())
        
        # 角色
        characters = []
        char_elems = work_elem.select('li.characters a')
        for c in char_elems:
            characters.append(c.text.strip())
        
        # 标签
        freeforms = []
        tag_elems = work_elem.select('li.freeforms a')
        for t in tag_elems:
            freeforms.append(t.text.strip())
        
        # 摘要
        summary_elem = work_elem.select_one('.summary')
        summary = ''
        if summary_elem:
            summary = summary_elem.get_text(strip=True)
        
        # 统计信息
        stats = {}
        
        # 字数
        words_elem = work_elem.select_one('.words')
        if words_elem:
            words_text = words_elem.get_text(strip=True).replace(',', '')
            try:
                stats['words'] = int(words_text)
            except:
                stats['words'] = 0
        
        # 章节
        chapters_elem = work_elem.select_one('.chapters')
        if chapters_elem:
            stats['chapters'] = chapters_elem.get_text(strip=True)
        
        # 语言
        language_elem = work_elem.select_one('.language')
        if language_elem:
            stats['language'] = language_elem.get_text(strip=True)
        
        # 热度统计
        # Kudos
        kudos_elem = work_elem.select_one('.kudos a')
        stats['kudos'] = int(kudos_elem.text.replace(',', '')) if kudos_elem else 0
        
        # Hits
        hits_elem = work_elem.select_one('.hits')
        stats['hits'] = int(hits_elem.text.replace(',', '')) if hits_elem else 0
        
        # Comments
        comments_elem = work_elem.select_one('.comments a')
        stats['comments'] = int(comments_elem.text.replace(',', '')) if comments_elem else 0
        
        # Bookmarks
        bookmarks_elem = work_elem.select_one('.bookmarks a')
        stats['bookmarks'] = int(bookmarks_elem.text.replace(',', '')) if bookmarks_elem else 0
        
        # 评级和警告
        rating_elem = work_elem.select_one('.rating')
        rating = rating_elem.get_text(strip=True) if rating_elem else 'Not Rated'
        
        warnings = []
        warning_elems = work_elem.select('li.warnings a')
        for w in warning_elems:
            warnings.append(w.text.strip())
        
        # 是否完结
        is_complete = 'Complete' in work_elem.get_text()
        
        # 发布时间
        datetime_elem = work_elem.select_one('p.datetime')
        published_at = None
        if datetime_elem:
            published_at = datetime_elem.get_text(strip=True)
        
        return {
            'id': work_id,
            'title': title,
            'url': work_url,
            'author': {
                'name': author,
                'url': author_url
            },
            'fandoms': fandoms,
            'relationships': relationships,
            'characters': characters,
            'tags': freeforms,
            'summary': summary,
            'stats': stats,
            'rating': rating,
            'warnings': warnings,
            'is_complete': is_complete,
            'published_at': published_at,
            'platform': 'ao3',
            'content_type': 'article',
            'popularity': stats.get('kudos', 0)
        }
        
    except Exception as e:
        print(f'Error in parse_work_item: {e}')
        return None

@app.route('/api/ao3/work/<work_id>', methods=['GET'])
def get_work_detail(work_id):
    """获取单个作品的详细信息"""
    try:
        url = f'https://archiveofourown.org/works/{work_id}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 解析作品详情
        work_meta = soup.select_one('.work.meta')
        if not work_meta:
            return jsonify({'success': False, 'error': 'Work not found'}), 404
        
        # 获取章节内容（如果有的话）
        chapters = []
        chapter_elems = soup.select('#workskin .chapter')
        for chapter in chapter_elems:
            title_elem = chapter.select_one('.title')
            title = title_elem.text.strip() if title_elem else 'Untitled'
            
            content_elem = chapter.select_one('.userstuff')
            content = content_elem.get_text(strip=True) if content_elem else ''
            
            chapters.append({
                'title': title,
                'content': content[:500] + '...' if len(content) > 500 else content
            })
        
        return jsonify({
            'success': True,
            'work_id': work_id,
            'chapters': chapters,
            'chapter_count': len(chapters)
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
    app.run(debug=True, port=5002)
