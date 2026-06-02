# api/scraper.py
"""
主爬虫模块 - 聚合多平台二次元同人内容
支持平台：Lofter、微博、小红书、Bilibili
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

class ContentScraper:
    """内容爬虫类"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # 预设数据库（备用数据）
        self.cache = self._init_cache()
    
    def _init_cache(self):
        """初始化预设数据库"""
        return {
            '将进酒': {
                'Lofter': [
                    {
                        'id': 'lofter_jjz_001',
                        'platform': 'Lofter',
                        'title': '【策舟】离北铁骑与中博枭主的极致拉扯',
                        'author': '秋风词',
                        'link': 'https://www.lofter.com/post/1f0d0e_1a8f5c7d9',
                        'tags': ['古代', '强强', '策舟'],
                        'hot': '25.3k',
                        'preview': '这是一篇关于策舟 CP 的精品长篇同人文，讲述了离北与泽川之间的微妙关系...',
                        'time': '2024-01-15'
                    },
                    {
                        'id': 'lofter_jjz_002',
                        'platform': 'Lofter',
                        'title': '【策舟】沈泽川的秘密花园',
                        'author': '墨雨轻扬',
                        'link': 'https://www.lofter.com/post/1f0d0e_1a8f5c7d8',
                        'tags': ['现代', '甜文', '策舟'],
                        'hot': '18.7k',
                        'preview': '现代 AU，离北是个冷酷的金融精英，泽川是他的秘书助理...',
                        'time': '2024-01-14'
                    },
                    {
                        'id': 'lofter_jjz_003',
                        'platform': 'Lofter',
                        'title': '【策舟】兰舟晚，何人知',
                        'author': '长歌当哭',
                        'link': 'https://www.lofter.com/post/1f0d0e_1a8f5c7d7',
                        'tags': ['虐文', '古代', '策舟'],
                        'hot': '32.1k',
                        'preview': '这是一部高虐的古代背景同人，讲述了两人之间的爱恨纠葛...',
                        'time': '2024-01-13'
                    },
                    {
                        'id': 'lofter_jjz_004',
                        'platform': 'Lofter',
                        'title': '【策舟】月明星稀',
                        'author': '云梦泽畔',
                        'link': 'https://www.lofter.com/post/1f0d0e_1a8f5c7d6',
                        'tags': ['古代', '强强', '策舟'],
                        'hot': '21.5k',
                        'preview': '古代侠义背景，两人从对立到携手的故事...',
                        'time': '2024-01-12'
                    }
                ],
                '微博': [
                    {
                        'id': 'weibo_jjz_001',
                        'platform': '微博',
                        'title': '【将进酒同人文推荐】本周必吃榜',
                        'author': '将进酒文推君',
                        'link': 'https://weibo.com/u/7654321?mid=123456789',
                        'tags': ['推荐', '必吃榜'],
                        'hot': '12.5k',
                        'preview': '精选本周最火的将进酒同人文 5 篇，包含各种设定和 CP...',
                        'time': '2024-01-15'
                    },
                    {
                        'id': 'weibo_jjz_002',
                        'platform': '微博',
                        'title': '策舟 CP 超话日常分享',
                        'author': '策舟太太们',
                        'link': 'https://weibo.com/u/8765432?mid=987654321',
                        'tags': ['超话', '日常'],
                        'hot': '8.3k',
                        'preview': '今日策舟 CP 最新同人作品汇总，包含图文和视频...',
                        'time': '2024-01-15'
                    },
                    {
                        'id': 'weibo_jjz_003',
                        'platform': '微博',
                        'title': '将进酒原著分析 | 策舟的爱情线',
                        'author': '文学评论家',
                        'link': 'https://weibo.com/u/5432123?mid=555666777',
                        'tags': ['分析', '原著'],
                        'hot': '15.8k',
                        'preview': '深度解读将进酒原著中策舟两人的感情线索...',
                        'time': '2024-01-14'
                    }
                ],
                '小红书': [
                    {
                        'id': 'xhs_jjz_001',
                        'platform': '小红书',
                        'title': '将进酒必吃榜 | 这 10 篇文必须吃',
                        'author': '云深笔记',
                        'link': 'https://www.xiaohongshu.com/explore/60c9d8e000000000120abcde',
                        'tags': ['必吃榜', '文单'],
                        'hot': '15.2k',
                        'preview': '整理了最受欢迎的将进酒同人文，涵盖古代、现代、校园等设定...',
                        'time': '2024-01-14'
                    },
                    {
                        'id': 'xhs_jjz_002',
                        'platform': '小红书',
                        'title': '策舟甜文推荐 | 这些文让我反复刷',
                        'author': '同人女孩',
                        'link': 'https://www.xiaohongshu.com/explore/60c9d8e000000000120abcdf',
                        'tags': ['甜文', '推荐'],
                        'hot': '9.7k',
                        'preview': '精选策舟向高甜同人文，适合反复品尝...',
                        'time': '2024-01-13'
                    }
                ],
                'Bilibili': [
                    {
                        'id': 'bili_jjz_001',
                        'platform': 'Bilibili',
                        'title': '【将进酒】策舟向高燃混剪',
                        'author': '百香果剪辑',
                        'link': 'https://www.bilibili.com/video/BV1xJ411a7fK',
                        'tags': ['剪辑', '高燃'],
                        'hot': '156.8k',
                        'preview': '用将进酒原著素材制作的策舟向高燃混剪，燃到爆炸...',
                        'time': '2024-01-12'
                    },
                    {
                        'id': 'bili_jjz_002',
                        'platform': 'Bilibili',
                        'title': '【将进酒】所有策舟片段合集',
                        'author': '离北粉丝团',
                        'link': 'https://www.bilibili.com/video/BV1xJ411b8gM',
                        'tags': ['合集', '片段'],
                        'hot': '98.3k',
                        'preview': '全网最全的将进酒策舟出场片段合集...',
                        'time': '2024-01-11'
                    }
                ]
            },
            '魔道祖师': {
                'Lofter': [
                    {
                        'id': 'lofter_mdzs_001',
                        'platform': 'Lofter',
                        'title': '云深不知处（忘羡向长篇）',
                        'author': '忘羡推文君',
                        'link': 'https://www.lofter.com/post/2e1c0e_1b9g6d8e0',
                        'tags': ['校园', '甜文', '忘羡'],
                        'hot': '38.5k',
                        'preview': '大学 AU，魏无羡是个爱玩的富二代，蓝忘机是他的同学...',
                        'time': '2024-01-15'
                    },
                    {
                        'id': 'lofter_mdzs_002',
                        'platform': 'Lofter',
                        'title': '【忘羡】乱世佳人',
                        'author': '墨香铜臭迷',
                        'link': 'https://www.lofter.com/post/2e1c0e_1b9g6d8e1',
                        'tags': ['古代', '强强', '忘羡'],
                        'hot': '41.2k',
                        'preview': '魏氏和蓝氏的家族对抗中，两人逐渐产生了不为人知的感情...',
                        'time': '2024-01-14'
                    }
                ],
                '微博': [
                    {
                        'id': 'weibo_mdzs_001',
                        'platform': '微博',
                        'title': '忘羡 CP 必吃榜 | 2024 年最火的文',
                        'author': '魔道文推君',
                        'link': 'https://weibo.com/u/9876543?mid=654321098',
                        'tags': ['推荐', '必吃榜'],
                        'hot': '45.6k',
                        'preview': '精选忘羡向最受欢迎的同人文，每一篇都是精品...',
                        'time': '2024-01-15'
                    }
                ],
                '小红书': [
                    {
                        'id': 'xhs_mdzs_001',
                        'platform': '小红书',
                        'title': '魔道祖师同人文推荐清单',
                        'author': '墨香阁',
                        'link': 'https://www.xiaohongshu.com/explore/60c9d8e000000000120abcdf',
                        'tags': ['推荐', '清单'],
                        'hot': '22.3k',
                        'preview': '最全面的魔道同人文整理，包含各个 CP 和设定...',
                        'time': '2024-01-13'
                    }
                ]
            },
            '博君一肖': {
                'Bilibili': [
                    {
                        'id': 'bili_bjyx_001',
                        'platform': 'Bilibili',
                        'title': '【BJYX】2024 年演唱会完整高清版',
                        'author': '百香果园',
                        'link': 'https://www.bilibili.com/video/BV1xJ411b8gK',
                        'tags': ['演唱会', '纪念'],
                        'hot': '580.3k',
                        'preview': '博君一肖南京演唱会完整录制，高清 4K 画质...',
                        'time': '2024-01-10'
                    }
                ]
            },
            '天官赐福': {
                'Lofter': [
                    {
                        'id': 'lofter_tgcf_001',
                        'platform': 'Lofter',
                        'title': '【谢花】天官赐福番外（亲情向）',
                        'author': '花城谢怜粉',
                        'link': 'https://www.lofter.com/post/4g3e2g_1d1i8f0g2',
                        'tags': ['番外', '甜文', '谢花'],
                        'hot': '28.6k',
                        'preview': '天官赐福官方番外改编同人，讲述花城和谢怜的日常...',
                        'time': '2024-01-14'
                    }
                ]
            }
        }
    
    def scrape_lofter(self, keyword):
        """爬取 Lofter 内容"""
        try:
            url = f"https://www.lofter.com/tag/{keyword}"
            response = requests.get(url, headers=self.headers, timeout=8)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            # 根据 Lofter 实际 HTML 结构调整选择器
            posts = soup.find_all('div', class_='feed-item')[:20]
            
            for post in posts:
                try:
                    title_elem = post.find('a', class_='post-title')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        if not link.startswith('http'):
                            link = f"https://www.lofter.com{link}"
                        
                        results.append({
                            'platform': 'Lofter',
                            'title': title,
                            'author': '匿名',
                            'link': link,
                            'tags': ['Lofter'],
                            'hot': '10k+',
                            'preview': title[:50] + '...',
                            'time': datetime.now().strftime('%Y-%m-%d')
                        })
                except Exception as e:
                    print(f"解析单条 Lofter 文章失败: {e}")
                    continue
            
            return results
        except Exception as e:
            print(f"Lofter 爬虫错误: {e}")
            return []
    
    def scrape_weibo(self, keyword):
        """爬取微博内容"""
        try:
            url = f"https://s.weibo.com/weibo?q={keyword}"
            response = requests.get(url, headers=self.headers, timeout=8)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            items = soup.find_all('div', class_='feed-item')[:15]
            
            for item in items:
                try:
                    content = item.find('p', class_='txt')
                    if content:
                        text = content.get_text(strip=True)[:100]
                        link_elem = item.find('a', class_='source')
                        link = link_elem.get('href', f'https://s.weibo.com/weibo?q={keyword}') if link_elem else f'https://s.weibo.com/weibo?q={keyword}'
                        
                        results.append({
                            'platform': '微博',
                            'title': text,
                            'author': '微博用户',
                            'link': link if link.startswith('http') else f'https://weibo.com{link}',
                            'tags': ['微博'],
                            'hot': '5k+',
                            'preview': text,
                            'time': datetime.now().strftime('%Y-%m-%d')
                        })
                except Exception as e:
                    print(f"解析单条微博失败: {e}")
                    continue
            
            return results
        except Exception as e:
            print(f"微博爬虫错误: {e}")
            return []
    
    def scrape_xiaohongshu(self, keyword):
        """爬取小红书内容"""
        try:
            url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
            response = requests.get(url, headers=self.headers, timeout=8)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            items = soup.find_all('div', class_='feed-item')[:15]
            
            for item in items:
                try:
                    title_elem = item.find('span', class_='title')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
                        
                        results.append({
                            'platform': '小红书',
                            'title': title,
                            'author': '小红书用户',
                            'link': link,
                            'tags': ['小红书'],
                            'hot': '8k+',
                            'preview': title,
                            'time': datetime.now().strftime('%Y-%m-%d')
                        })
                except Exception as e:
                    print(f"解析单条小红书失败: {e}")
                    continue
            
            return results
        except Exception as e:
            print(f"小红书爬虫错误: {e}")
            return []
    
    def scrape_bilibili(self, keyword):
        """爬取 B 站内容"""
        try:
            url = f"https://search.bilibili.com/all?keyword={keyword}"
            response = requests.get(url, headers=self.headers, timeout=8)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            items = soup.find_all('div', class_='video-item')[:15]
            
            for item in items:
                try:
                    title_elem = item.find('h2', class_='title')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        link = title_elem.find('a')
                        link = link.get('href', '') if link else f'https://search.bilibili.com/all?keyword={keyword}'
                        
                        results.append({
                            'platform': 'Bilibili',
                            'title': title,
                            'author': 'B站UP主',
                            'link': link if link.startswith('http') else f'https://www.bilibili.com{link}',
                            'tags': ['B站'],
                            'hot': '50k+',
                            'preview': title,
                            'time': datetime.now().strftime('%Y-%m-%d')
                        })
                except Exception as e:
                    print(f"解析单条 B 站视频失败: {e}")
                    continue
            
            return results
        except Exception as e:
            print(f"B站爬虫错误: {e}")
            return []
    
    def aggregate(self, ip, xp=None, platform=None):
        """
        聚合多平台内容
        
        Args:
            ip: IP 名称（如"将进酒"）
            xp: XP 标签过滤（可选）
            platform: 平台过滤（可选）
        
        Returns:
            dict: 聚合结果
        """
        # 首先从缓存获取
        if ip not in self.cache:
            return {
                'success': False,
                'error': f'IP "{ip}" 暂无内容',
                'count': 0,
                'data': []
            }
        
        results = []
        cache_data = self.cache[ip]
        
        # 平台优先级
        platform_order = ['Lofter', '微博', '小红书', 'Bilibili']
        
        if platform and platform != '全部':
            # 指定平台
            if platform in cache_data:
                results.extend(cache_data[platform])
        else:
            # 按优先级聚合所有平台
            for p in platform_order:
                if p in cache_data:
                    results.extend(cache_data[p])
        
        # XP 标签过滤
        if xp:
            results = [item for item in results if xp in item.get('tags', [])]
        
        # 按热度排序（从高到低）
        def parse_hot(hot_str):
            """解析热度字符串"""
            import re
            match = re.search(r'(\d+\.?\d*)', hot_str)
            if not match:
                return 0
            num = float(match.group(1))
            if 'k' in hot_str.lower():
                return num * 1000
            elif 'm' in hot_str.lower():
                return num * 1000000
            return num
        
        results.sort(key=lambda x: parse_hot(x.get('hot', '0')), reverse=True)
        
        return {
            'success': True,
            'ip': ip,
            'xp': xp or '全部',
            'platform': platform or '全部',
            'count': len(results),
            'data': results,
            'timestamp': datetime.now().isoformat()
        }

# 全局爬虫实例
scraper = ContentScraper()
