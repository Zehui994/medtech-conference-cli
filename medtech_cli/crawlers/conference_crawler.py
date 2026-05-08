import time
import random
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BaseCrawler:
    """基础爬虫类，提供通用的爬虫功能"""
    
    def __init__(self, config=None):
        """初始化爬虫
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        })
        self.timeout = 30
        self.retry_count = 3
        self.retry_delay = 5
        
    def fetch(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Optional[str]:
        """获取网页内容
        
        Args:
            url: 网页URL
            params: URL参数
            headers: 请求头
            
        Returns:
            网页HTML内容，如果失败则返回None
        """
        for attempt in range(self.retry_count):
            try:
                response = self.session.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"获取 {url} 失败 (尝试 {attempt+1}/{self.retry_count}): {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay + random.uniform(0, 2))
                else:
                    logger.error(f"获取 {url} 失败，已达到最大重试次数")
                    return None
                    
    def parse_date(self, date_str: str, formats: List[str]) -> Optional[datetime]:
        """解析日期字符串
        
        Args:
            date_str: 日期字符串
            formats: 可能的日期格式列表
            
        Returns:
            解析后的日期对象，如果失败则返回None
        """
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
        
    def extract_text(self, soup: BeautifulSoup, selector: str) -> str:
        """从网页中提取文本
        
        Args:
            soup: BeautifulSoup对象
            selector: CSS选择器
            
        Returns:
            提取的文本，如果未找到则返回空字符串
        """
        element = soup.select_one(selector)
        if element:
            return element.get_text(strip=True)
        return ""
        
    def extract_link(self, soup: BeautifulSoup, selector: str, base_url: str) -> str:
        """从网页中提取链接
        
        Args:
            soup: BeautifulSoup对象
            selector: CSS选择器
            base_url: 基础URL，用于相对链接的拼接
            
        Returns:
            提取的链接，如果未找到则返回空字符串
        """
        element = soup.select_one(selector)
        if element and element.get('href'):
            return urljoin(base_url, element.get('href'))
        return ""
        
    def crawl(self, **kwargs) -> List[Dict[str, Any]]:
        """执行爬虫，子类必须实现此方法
        
        Returns:
            爬取的会议列表
        """
        raise NotImplementedError("子类必须实现crawl方法")


class ChinaCrawler(BaseCrawler):
    """中国大陆地区会议爬虫"""
    
    def crawl(self, **kwargs) -> List[Dict[str, Any]]:
        """爬取中国大陆地区的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        
        # 爬取活动行
        conferences.extend(self._crawl_huodongxing())
        
        # 爬取会议家
        conferences.extend(self._crawl_huiyijia())
        
        return conferences
        
    def _crawl_huodongxing(self) -> List[Dict[str, Any]]:
        """爬取活动行网站的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        keywords = self.config.get_keywords() if self.config else []
        
        for keyword in keywords:
            url = "https://www.huodongxing.com/search"
            params = {
                "keywords": keyword,
                "city": "",
                "start": "",
                "end": ""
            }
            
            logger.info(f"正在爬取活动行关键词: {keyword}")
            html = self.fetch(url, params=params)
            
            if not html:
                continue
                
            soup = BeautifulSoup(html, 'lxml')
            
            # 解析会议列表
            event_list = soup.select('.search-list > .event-list > .event-item')
            
            for event in event_list:
                try:
                    # 提取会议信息
                    title = self.extract_text(event, '.title > a')
                    if not title:
                        continue
                        
                    link = self.extract_link(event, '.title > a', url)
                    date_str = self.extract_text(event, '.time')
                    location = self.extract_text(event, '.address')
                    price = self.extract_text(event, '.price')
                    
                    # 解析日期
                    start_date = None
                    if date_str:
                        # 活动行日期格式：2023年10月15日 周日 09:00-18:00
                        start_date = self.parse_date(date_str.split(' ')[0], ['%Y年%m月%d日'])
                    
                    # 构建会议对象
                    conference = {
                        'title': title,
                        'url': link,
                        'start_date': start_date.date() if start_date else None,
                        'location': location,
                        'price': price,
                        'region': 'china',
                        'source': 'huodongxing',
                        'keywords': [keyword]
                    }
                    
                    conferences.append(conference)
                    
                except Exception as e:
                    logger.error(f"解析活动行会议失败: {e}")
                    
            # 避免请求过快
            time.sleep(random.uniform(1, 3))
            
        return conferences
        
    def _crawl_huiyijia(self) -> List[Dict[str, Any]]:
        """爬取会议家网站的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        keywords = self.config.get_keywords() if self.config else []
        
        for keyword in keywords:
            url = "https://www.huiyijia.com/search"
            params = {
                "keyword": keyword
            }
            
            logger.info(f"正在爬取会议家关键词: {keyword}")
            html = self.fetch(url, params=params)
            
            if not html:
                continue
                
            soup = BeautifulSoup(html, 'lxml')
            
            # 解析会议列表
            event_list = soup.select('.search_list > li')
            
            for event in event_list:
                try:
                    # 提取会议信息
                    title = self.extract_text(event, '.meet_name > a')
                    if not title:
                        continue
                        
                    link = self.extract_link(event, '.meet_name > a', url)
                    date_str = self.extract_text(event, '.meet_time')
                    location = self.extract_text(event, '.meet_place')
                    
                    # 解析日期
                    start_date = None
                    if date_str:
                        # 会议家日期格式：2023-10-15 至 2023-10-17
                        date_parts = date_str.split(' 至 ')
                        if date_parts:
                            start_date = self.parse_date(date_parts[0], ['%Y-%m-%d'])
                    
                    # 构建会议对象
                    conference = {
                        'title': title,
                        'url': link,
                        'start_date': start_date.date() if start_date else None,
                        'location': location,
                        'region': 'china',
                        'source': 'huiyijia',
                        'keywords': [keyword]
                    }
                    
                    conferences.append(conference)
                    
                except Exception as e:
                    logger.error(f"解析会议家会议失败: {e}")
                    
            # 避免请求过快
            time.sleep(random.uniform(1, 3))
            
        return conferences


class HongKongCrawler(BaseCrawler):
    """香港地区会议爬虫"""
    
    def crawl(self, **kwargs) -> List[Dict[str, Any]]:
        """爬取香港地区的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        
        # 爬取香港会议展览中心
        conferences.extend(self._crawl_hkcec())
        
        return conferences
        
    def _crawl_hkcec(self) -> List[Dict[str, Any]]:
        """爬取香港会议展览中心网站的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        url = "https://www.hkcec.com/en/exhibition-calendar"
        
        logger.info("正在爬取香港会议展览中心")
        html = self.fetch(url)
        
        if not html:
            return conferences
            
        soup = BeautifulSoup(html, 'lxml')
        
        # 解析会议列表
        event_list = soup.select('.event-list > .event-item')
        
        for event in event_list:
            try:
                # 提取会议信息
                title = self.extract_text(event, '.event-title')
                if not title:
                    continue
                    
                link = self.extract_link(event, '.event-title > a', url)
                date_str = self.extract_text(event, '.event-date')
                location = "Hong Kong Convention and Exhibition Centre"
                
                # 解析日期
                start_date = None
                if date_str:
                    # 香港会议展览中心日期格式：15 - 17 October 2023
                    date_parts = date_str.split(' - ')
                    if date_parts:
                        start_date_str = date_parts[0] + date_parts[1] if len(date_parts) > 1 else date_parts[0]
                        start_date = self.parse_date(start_date_str.strip(), ['%d %B %Y', '%d-%d %B %Y'])
                
                # 构建会议对象
                conference = {
                    'title': title,
                    'url': link,
                    'start_date': start_date.date() if start_date else None,
                    'location': location,
                    'region': 'hongkong',
                    'source': 'hkcec'
                }
                
                conferences.append(conference)
                
            except Exception as e:
                logger.error(f"解析香港会议展览中心会议失败: {e}")
                
        return conferences


class USACrawler(BaseCrawler):
    """美国地区会议爬虫"""
    
    def crawl(self, **kwargs) -> List[Dict[str, Any]]:
        """爬取美国地区的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        
        # 爬取Conference Alerts
        conferences.extend(self._crawl_conference_alerts())
        
        # 爬取All Conference Alert
        conferences.extend(self._crawl_all_conference_alert())
        
        return conferences
        
    def _crawl_conference_alerts(self) -> List[Dict[str, Any]]:
        """爬取Conference Alerts网站的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        keywords = self.config.get_keywords() if self.config else []
        
        for keyword in keywords:
            url = "https://www.conferencealerts.com/Results.aspx"
            params = {
                "k": keyword,
                "c": "",
                "cc": "US"
            }
            
            logger.info(f"正在爬取Conference Alerts关键词: {keyword}")
            html = self.fetch(url, params=params)
            
            if not html:
                continue
                
            soup = BeautifulSoup(html, 'lxml')
            
            # 解析会议列表
            event_list = soup.select('.conf-list > li')
            
            for event in event_list:
                try:
                    # 提取会议信息
                    title = self.extract_text(event, '.conf-title')
                    if not title:
                        continue
                        
                    link = self.extract_link(event, '.conf-title > a', url)
                    date_str = self.extract_text(event, '.conf-date')
                    location = self.extract_text(event, '.conf-venue')
                    
                    # 解析日期
                    start_date = None
                    if date_str:
                        # Conference Alerts日期格式：Oct 15-17, 2023
                        start_date = self.parse_date(date_str.split(',')[0], ['%b %d-%d', '%b %d'])
                        if start_date:
                            # 添加年份
                            year = date_str.split(',')[-1].strip() if ',' in date_str else str(datetime.now().year)
                            start_date = start_date.replace(year=int(year))
                    
                    # 构建会议对象
                    conference = {
                        'title': title,
                        'url': link,
                        'start_date': start_date.date() if start_date else None,
                        'location': location,
                        'region': 'us',
                        'source': 'conferencealerts',
                        'keywords': [keyword]
                    }
                    
                    conferences.append(conference)
                    
                except Exception as e:
                    logger.error(f"解析Conference Alerts会议失败: {e}")
                    
            # 避免请求过快
            time.sleep(random.uniform(1, 3))
            
        return conferences
        
    def _crawl_all_conference_alert(self) -> List[Dict[str, Any]]:
        """爬取All Conference Alert网站的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        keywords = self.config.get_keywords() if self.config else []
        
        for keyword in keywords:
            url = "https://www.allconferencealert.com/search-conference"
            params = {
                "s": keyword,
                "country": "USA"
            }
            
            logger.info(f"正在爬取All Conference Alert关键词: {keyword}")
            html = self.fetch(url, params=params)
            
            if not html:
                continue
                
            soup = BeautifulSoup(html, 'lxml')
            
            # 解析会议列表
            event_list = soup.select('.conference-list > .conference-item')
            
            for event in event_list:
                try:
                    # 提取会议信息
                    title = self.extract_text(event, '.conference-title')
                    if not title:
                        continue
                        
                    link = self.extract_link(event, '.conference-title > a', url)
                    date_str = self.extract_text(event, '.conference-date')
                    location = self.extract_text(event, '.conference-location')
                    
                    # 解析日期
                    start_date = None
                    if date_str:
                        # All Conference Alert日期格式：October 15-17, 2023
                        start_date = self.parse_date(date_str.split(',')[0], ['%B %d-%d', '%B %d'])
                        if start_date:
                            # 添加年份
                            year = date_str.split(',')[-1].strip() if ',' in date_str else str(datetime.now().year)
                            start_date = start_date.replace(year=int(year))
                    
                    # 构建会议对象
                    conference = {
                        'title': title,
                        'url': link,
                        'start_date': start_date.date() if start_date else None,
                        'location': location,
                        'region': 'us',
                        'source': 'allconferencealert',
                        'keywords': [keyword]
                    }
                    
                    conferences.append(conference)
                    
                except Exception as e:
                    logger.error(f"解析All Conference Alert会议失败: {e}")
                    
            # 避免请求过快
            time.sleep(random.uniform(1, 3))
            
        return conferences


class SingaporeCrawler(BaseCrawler):
    """新加坡地区会议爬虫"""
    
    def crawl(self, **kwargs) -> List[Dict[str, Any]]:
        """爬取新加坡地区的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        
        # 爬取新加坡展览会议局
        conferences.extend(self._crawl_visit_singapore())
        
        return conferences
        
    def _crawl_visit_singapore(self) -> List[Dict[str, Any]]:
        """爬取新加坡展览会议局网站的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        url = "https://www.visitsingapore.com/mice/en/events/"
        
        logger.info("正在爬取新加坡展览会议局")
        html = self.fetch(url)
        
        if not html:
            return conferences
            
        soup = BeautifulSoup(html, 'lxml')
        
        # 解析会议列表
        event_list = soup.select('.event-card')
        
        for event in event_list:
            try:
                # 提取会议信息
                title = self.extract_text(event, '.event-title')
                if not title:
                    continue
                    
                link = self.extract_link(event, '.event-title > a', url)
                date_str = self.extract_text(event, '.event-date')
                location = self.extract_text(event, '.event-location')
                
                # 解析日期
                start_date = None
                if date_str:
                    # 新加坡展览会议局日期格式：15 - 17 Oct 2023
                    date_parts = date_str.split(' - ')
                    if date_parts:
                        start_date = self.parse_date(date_parts[0].strip(), ['%d %b %Y'])
                
                # 构建会议对象
                conference = {
                    'title': title,
                    'url': link,
                    'start_date': start_date.date() if start_date else None,
                    'location': location,
                    'region': 'singapore',
                    'source': 'visitsingapore'
                }
                
                conferences.append(conference)
                
            except Exception as e:
                logger.error(f"解析新加坡展览会议局会议失败: {e}")
                
        return conferences


class JapanCrawler(BaseCrawler):
    """日本地区会议爬虫"""
    
    def crawl(self, **kwargs) -> List[Dict[str, Any]]:
        """爬取日本地区的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        
        # 爬取日本会议信息网站
        conferences.extend(self._crawl_japan_conferences())
        
        return conferences
        
    def _crawl_japan_conferences(self) -> List[Dict[str, Any]]:
        """爬取日本会议信息网站的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        keywords = self.config.get_keywords() if self.config else []
        
        for keyword in keywords:
            url = "https://www.japanconference.net/search"
            params = {
                "q": keyword,
                "country": "JP"
            }
            
            logger.info(f"正在爬取日本会议信息关键词: {keyword}")
            html = self.fetch(url, params=params)
            
            if not html:
                continue
                
            soup = BeautifulSoup(html, 'lxml')
            
            # 解析会议列表
            event_list = soup.select('.conference-list > .conference-item')
            
            for event in event_list:
                try:
                    # 提取会议信息
                    title = self.extract_text(event, '.conference-title')
                    if not title:
                        continue
                        
                    link = self.extract_link(event, '.conference-title > a', url)
                    date_str = self.extract_text(event, '.conference-date')
                    location = self.extract_text(event, '.conference-location')
                    
                    # 解析日期
                    start_date = None
                    if date_str:
                        # 日本会议日期格式：2023年10月15日〜17日
                        date_parts = date_str.split('〜')
                        if date_parts:
                            start_date = self.parse_date(date_parts[0], ['%Y年%m月%d日'])
                    
                    # 构建会议对象
                    conference = {
                        'title': title,
                        'url': link,
                        'start_date': start_date.date() if start_date else None,
                        'location': location,
                        'region': 'japan',
                        'source': 'japanconference',
                        'keywords': [keyword]
                    }
                    
                    conferences.append(conference)
                    
                except Exception as e:
                    logger.error(f"解析日本会议失败: {e}")
                    
            # 避免请求过快
            time.sleep(random.uniform(1, 3))
            
        return conferences


class IndonesiaCrawler(BaseCrawler):
    """印尼地区会议爬虫"""
    
    def crawl(self, **kwargs) -> List[Dict[str, Any]]:
        """爬取印尼地区的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        
        # 爬取印尼会议信息网站
        conferences.extend(self._crawl_indonesia_conferences())
        
        return conferences
        
    def _crawl_indonesia_conferences(self) -> List[Dict[str, Any]]:
        """爬取印尼会议信息网站的会议信息
        
        Returns:
            会议列表
        """
        conferences = []
        keywords = self.config.get_keywords() if self.config else []
        
        for keyword in keywords:
            url = "https://www.indonesiaconference.com/search"
            params = {
                "q": keyword,
                "country": "ID"
            }
            
            logger.info(f"正在爬取印尼会议信息关键词: {keyword}")
            html = self.fetch(url, params=params)
            
            if not html:
                continue
                
            soup = BeautifulSoup(html, 'lxml')
            
            # 解析会议列表
            event_list = soup.select('.event-list > .event-item')
            
            for event in event_list:
                try:
                    # 提取会议信息
                    title = self.extract_text(event, '.event-title')
                    if not title:
                        continue
                        
                    link = self.extract_link(event, '.event-title > a', url)
                    date_str = self.extract_text(event, '.event-date')
                    location = self.extract_text(event, '.event-location')
                    
                    # 解析日期
                    start_date = None
                    if date_str:
                        # 印尼会议日期格式：15-17 October 2023
                        date_parts = date_str.split('-')
                        if date_parts:
                            start_date = self.parse_date(date_parts[0].strip() + date_parts[1].split(' ')[-1], ['%d %B %Y'])
                    
                    # 构建会议对象
                    conference = {
                        'title': title,
                        'url': link,
                        'start_date': start_date.date() if start_date else None,
                        'location': location,
                        'region': 'indonesia',
                        'source': 'indonesiaconference',
                        'keywords': [keyword]
                    }
                    
                    conferences.append(conference)
                    
                except Exception as e:
                    logger.error(f"解析印尼会议失败: {e}")
                    
            # 避免请求过快
            time.sleep(random.uniform(1, 3))
            
        return conferences


class ConferenceCrawler:
    """会议爬虫管理器，负责协调各地区爬虫"""
    
    def __init__(self, config=None):
        """初始化会议爬虫管理器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.crawlers = {
            'china': ChinaCrawler(config),
            'hongkong': HongKongCrawler(config),
            'us': USACrawler(config),
            'singapore': SingaporeCrawler(config),
            'japan': JapanCrawler(config),
            'indonesia': IndonesiaCrawler(config)
        }
        
    def crawl(self, region: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """执行爬虫
        
        Args:
            region: 地区名称，如果为 None 则爬取所有地区
            **kwargs: 其他参数
            
        Returns:
            爬取的会议列表
        """
        conferences = []
        
        # 确定要爬取的地区
        regions = [region] if region and region in self.crawlers else \
                 self.config.get_regions() if self.config else \
                 list(self.crawlers.keys())
                 
        # 移除不在支持列表中的地区
        regions = [r for r in regions if r in self.crawlers]
        
        if not regions:
            logger.warning("没有有效的地区配置")
            return conferences
            
        logger.info(f"开始爬取地区: {', '.join(regions)}")
        
        # 使用线程池并发爬取
        with ThreadPoolExecutor(max_workers=min(3, len(regions))) as executor:
            future_to_region = {
                executor.submit(self.crawlers[region].crawl, **kwargs): region
                for region in regions
            }
            
            for future in as_completed(future_to_region):
                region = future_to_region[future]
                try:
                    region_conferences = future.result()
                    conferences.extend(region_conferences)
                    logger.info(f"地区 {region} 爬取完成，获取 {len(region_conferences)} 条会议信息")
                except Exception as e:
                    logger.error(f"地区 {region} 爬取失败: {e}")
                    
        logger.info(f"所有地区爬取完成，共获取 {len(conferences)} 条会议信息")
        
        # 去重
        unique_conferences = self._remove_duplicates(conferences)
        logger.info(f"去重后剩余 {len(unique_conferences)} 条会议信息")
        
        return unique_conferences
        
    def _remove_duplicates(self, conferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复的会议
        
        Args:
            conferences: 会议列表
            
        Returns:
            去重后的会议列表
        """
        seen = set()
        unique_conferences = []
        
        for conf in conferences:
            # 使用标题和日期作为唯一标识
            key = f"{conf.get('title', '')}_{conf.get('start_date', '')}"
            if key not in seen:
                seen.add(key)
                unique_conferences.append(conf)
                
        return unique_conferences