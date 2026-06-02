"""
微博爬虫API - 获取微博相关内容
"""
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

app = Flask(__name__)

@app.route('/api/weibo', methods=['GET'])
def search_weibo():
    """搜索微博内容"""
    keyword = request.args.get('keyword', '')
    content_type = request.args.get('type', 'all')  # all, original, video, article
    page = request.args.get('page', 1)
    
    if not keyword:
        return jsonify({'success': False, 'error': 'Keyword is required'}), 400
    
    try:
        # 微博搜索
        search_url = f'https://s.weibo.com/weibo?q={keyword}&page={page}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://weibo.com/',
            'Cookie': 'SUB=_2AkMVWDzTf8NxqwFRmP8Ty2Pna4VwywjEieKjR5VJJRMxHRl-yj9jqkMStRB6Ounk7PHcYbMw2lX9ZBmoDE7i6Yhbg42;'
        }
        
        response = requests.get(search_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        posts = []
        
        # 解析微博卡片
        cards = soup.select('.card-wrap')
        
        for card in cards:
            try:
                post = parse_weibo_card(card)
                if post:
                    posts.append(post)
            except Exception as e:
                print(f'Error parsing weibo card: {e}')
                continue
        
        return jsonify({
            'success': True,
            'keyword': keyword,
            'type': content_type,
            'page': page,
            'count': len(posts),
            'posts': posts
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def parse_weibo_card(card_elem):
    """解析单个微博卡片"""
    try:
        # 用户信息
        user_elem = card_elem.select_one('.name a')
        if not user_elem:
            return None
        
        user_name = user_elem.text.strip()
        user_url = user_elem.get('href', '')
        if user_url and not user_url.startswith('http'):
            user_url = 'https:' + user_url
        
        # 微博内容
        content_elem = card_elem.select_one('.txt')
        if not content_elem:
            return None
        
        # 清理内容中的HTML标签
        content = content_elem.get_text(strip=True)
        
        # 微博链接
        mid = card_elem.get('mid', '')
        weibo_url = f'https://weibo.com/{mid}' if mid else user_url
        
        # 发布时间
        time_elem = card_elem.select_one('.from a')
        publish_time = time_elem.text.strip() if time_elem else ''
        
        # 来源
        source_elem = card_elem.select_one('.from a:nth-child(2)')
        source = source_elem.text.strip() if source_elem else '微博 weibo.com'
        
        # 互动数据
        stats = {}
        
        # 转发
        repost_elem = card_elem.select_one('[action-type="feed_list_forward"]')
        if repost_elem:
            repost_text = repost_elem.get_text()
            match = re.search(r'(\d+)', repost_text)
            stats['reposts'] = int(match.group(1)) if match else 0
        
        # 评论
        comment_elem = card_elem.select_one('[action-type="feed_list_comment"]')
        if comment_elem:
            comment_text = comment_elem.get_text()
            match = re.search(r'(\d+)', comment_text)
            stats['comments'] = int(match.group(1)) if match else 0
        
        # 点赞
        like_elem = card_elem.select_one('[action-type="feed_list_like"]')
        if like_elem:
            like_text = like_elem.get_text()
            match = re.search(r'(\d+)', like_text)
            stats['likes'] = int(match.group(1)) if match else 0
        
        # 图片
        images = []
        img_elems = card_elem.select('.media-piclist img')
        for img in img_elems:
            img_url = img.get('src', '')
            if img_url:
                if not img_url.startswith('http'):
                    img_url = 'https:' + img_url
                # 获取大图URL
                img_url = img_url.replace('/thumbnail/', '/large/')
                images.append(img_url)
        
        # 视频
        video = None
        video_elem = card_elem.select_one('.media-video')
        if video_elem:
            video_url = video_elem.get('action-data', '')
            if video_url:
                video = {'url': video_url}
        
        # 判断内容类型
        content_type = 'text'
        if video:
            content_type = 'video'
        elif images:
            content_type = 'image'
        
        # 计算热度
        popularity = stats.get('likes', 0) + stats.get('reposts', 0) * 2 + stats.get('comments', 0)
        
        return {
            'id': mid,
            'user': {
                'name': user_name,
                'url': user_url
            },
            'content': content,
            'platform': 'weibo',
            'content_type': content_type,
            'url': weibo_url,
            'images': images,
            'video': video,
            'stats': stats,
            'popularity': popularity,
            'publish_time': publish_time,
            'source': source,
            'tags': ['微博', '社交媒体']
        }
        
    except Exception as e:
        print(f'Error in parse_weibo_card: {e}')
        return None

@app.route('/api/weibo/hot', methods=['GET'])
def get_hot_search():
    """获取微博热搜榜"""
    try:
        hot_url = 'https://s.weibo.com/top/summary'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(hot_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        hot_list = []
        
        # 热搜列表
        tr_elems = soup.select('#pl_top_realtimehot tbody tr')
        
        for tr in tr_elems[1:]:  # 跳过表头
            try:
                rank_elem = tr.select_one('.ranktop')
                rank = rank_elem.text.strip() if rank_elem else ''
                
                title_elem = tr.select_one('td a')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                url = title_elem.get('href', '')
                if url and not url.startswith('http'):
                    url = 'https://s.weibo.com' + url
                
                # 热度值
                hot_elem = tr.select_one('td span')
                hot_value = hot_elem.text.strip() if hot_elem else ''
                
                # 标签（新、热、爆等）
                tag_elem = tr.select_one('td i')
                tag = tag_elem.text.strip() if tag_elem else ''
                
                hot_list.append({
                    'rank': rank,
                    'title': title,
                    'url': url,
                    'hot_value': hot_value,
                    'tag': tag
                })
            except Exception as e:
                print(f'Error parsing hot item: {e}')
                continue
        
        return jsonify({
            'success': True,
            'count': len(hot_list),
            'hot_list': hot_list[:50]  # 返回前50条
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weibo/super/<keyword>', methods=['GET'])
def get_super_topic(keyword):
    """获取超话信息"""
    try:
        super_url = f'https://weibo.com/p/100808{keyword}'
        
        return jsonify({
            'success': True,
            'keyword': keyword,
            'super_url': super_url,
            'info': {
                'description': f'{keyword}超话社区',
                'platform': 'weibo',
                'content_type': 'community'
            }
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
    app.run(debug=True, port=5004)
