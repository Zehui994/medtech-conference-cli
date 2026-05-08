import re
import logging
import nltk
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, date
from collections import defaultdict

# 下载必要的NLTK资源
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConferenceProcessor:
    """会议数据处理器，负责清洗、标准化和分类会议数据"""
    
    def __init__(self, config=None):
        """初始化会议处理器
        
        Args:
            config: 配置对象
        """
        self.config = config
        
        # 初始化关键词列表
        self.keywords = self._get_keywords()
        
        # 初始化主题分类映射
        self.topic_mapping = self._init_topic_mapping()
        
        # 初始化NLTK工具
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        
        # 添加医疗相关的停用词
        self.medical_stop_words = {
            'conference', 'meeting', 'symposium', 'workshop', 'exhibition',
            'expo', 'summit', 'forum', 'congress', 'event', '2023', '2024',
            'international', 'global', 'world', 'annual', 'virtual', 'hybrid'
        }
        self.stop_words.update(self.medical_stop_words)
        
    def _get_keywords(self) -> List[str]:
        """获取关键词列表
        
        Returns:
            关键词列表
        """
        if self.config:
            return self.config.get_keywords()
        else:
            # 默认关键词
            return [
                'HomeCare', 'AI', 'Artificial Intelligence', 'web3', 'RPM', 
                'Remote Patient Monitoring', '远程医疗', '医疗科技', '数字健康',
                'HealthTech', 'Digital Health', '医疗AI', '医疗机器人', '智能医疗',
                'Telemedicine', 'Telehealth', 'eHealth', 'mHealth', 'Healthcare IT',
                'Medical Devices', 'Wearables', 'IoT', 'Internet of Things',
                'Blockchain', 'Big Data', 'Analytics', 'Cloud Computing',
                'Machine Learning', 'Deep Learning', 'Computer Vision',
                'Natural Language Processing', 'Robotics', 'Sensors',
                'Virtual Reality', 'Augmented Reality', 'Mixed Reality',
                '3D Printing', 'Biotechnology', 'Genomics', 'Precision Medicine',
                'Personalized Medicine', 'Chronic Disease Management',
                'Health Monitoring', 'Digital Therapeutics', 'Pharmaceutical',
                'Drug Discovery', 'Clinical Trials', 'Healthcare Management',
                'Hospital Management', 'Patient Engagement', 'Patient Experience',
                'Healthcare Analytics', 'Population Health', 'Preventive Care',
                'Primary Care', 'Specialty Care', 'Mental Health', 'Wellness',
                'Fitness', 'Nutrition', 'Aging', 'Geriatrics', 'Pediatrics',
                'Women Health', 'Men Health', 'Dental', 'Ophthalmology',
                'Dermatology', 'Cardiology', 'Neurology', 'Oncology',
                'Orthopedics', 'Pulmonology', 'Gastroenterology', 'Nephrology',
                'Endocrinology', 'Rheumatology', 'Infectious Disease',
                'Immunology', 'Hematology', 'Urology', 'Obstetrics', 'Gynecology'
            ]
            
    def _init_topic_mapping(self) -> Dict[str, List[str]]:
        """初始化主题分类映射
        
        Returns:
            主题分类映射
        """
        return {
            'AI': [
                'AI', 'Artificial Intelligence', 'Machine Learning', 'Deep Learning',
                'Computer Vision', 'Natural Language Processing', 'Neural Networks',
                'Predictive Analytics', 'Cognitive Computing', 'AI in Healthcare',
                '医疗AI', '智能医疗', '机器学习', '深度学习', '计算机视觉',
                '自然语言处理'
            ],
            'Remote Patient Monitoring': [
                'RPM', 'Remote Patient Monitoring', 'Patient Monitoring',
                'Health Monitoring', 'Continuous Monitoring', 'Remote Monitoring',
                '远程监护', '远程监测', '患者监护', '健康监测'
            ],
            'Telemedicine': [
                'Telemedicine', 'Telehealth', 'Telecare', 'Virtual Care',
                'Remote Care', 'Online Consultation', 'Video Consultation',
                '远程医疗', '远程诊疗', '在线医疗', '视频问诊'
            ],
            'Digital Health': [
                'Digital Health', 'eHealth', 'mHealth', 'HealthTech',
                'Healthcare IT', 'Digital Healthcare', 'Healthcare Technology',
                '数字健康', '电子健康', '移动健康', '医疗科技'
            ],
            'Wearables & IoT': [
                'Wearables', 'Wearable Devices', 'IoT', 'Internet of Things',
                'Connected Devices', 'Smart Devices', 'Medical Wearables',
                'Wearable Sensors', '可穿戴设备', '物联网', '智能设备'
            ],
            'Blockchain & Web3': [
                'Blockchain', 'Web3', 'Distributed Ledger', 'Smart Contracts',
                'Cryptocurrency', 'Decentralized', 'NFT', 'Metaverse',
                '区块链', '分布式账本', '智能合约', '去中心化'
            ],
            'Healthcare Analytics': [
                'Big Data', 'Analytics', 'Healthcare Analytics', 'Data Analytics',
                'Business Intelligence', 'Predictive Analytics', 'Population Health',
                'Health Informatics', 'Clinical Analytics', '大数据', '数据分析',
                '健康信息学', '临床分析'
            ],
            'Medical Devices': [
                'Medical Devices', 'Medical Equipment', 'Diagnostic Devices',
                'Therapeutic Devices', 'Surgical Devices', 'Implantable Devices',
                'Medical Technology', '医疗器械', '医疗设备', '诊断设备',
                '治疗设备', '手术设备', '植入式设备'
            ],
            'Robotics & Automation': [
                'Robotics', 'Medical Robotics', 'Surgical Robotics', 'Robotic Surgery',
                'Automation', 'Autonomous Systems', 'AI Robotics', '医疗机器人',
                '手术机器人', '机器人手术', '自动化', '自主系统'
            ],
            'Virtual & Augmented Reality': [
                'Virtual Reality', 'VR', 'Augmented Reality', 'AR', 'Mixed Reality',
                'MR', 'Extended Reality', 'XR', '3D Visualization', 'Virtual Training',
                '虚拟实境', '增强实境', '混合实境', '扩展实境', '3D可视化', '虚拟培训'
            ]
        }
        
    def process(self, conferences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理会议数据
        
        Args:
            conferences: 原始会议数据列表
            
        Returns:
            处理后的会议数据列表
        """
        processed_conferences = []
        
        for conference in conferences:
            try:
                # 清洗数据
                cleaned_conference = self._clean_conference(conference)
                
                # 提取关键词
                extracted_keywords = self._extract_keywords(
                    cleaned_conference.get('title', '') + ' ' + 
                    cleaned_conference.get('description', '')
                )
                
                # 分类主题
                topics = self._classify_topics(extracted_keywords)
                
                # 计算相关度得分
                relevance_score = self._calculate_relevance_score(
                    extracted_keywords, topics
                )
                
                # 更新会议数据
                cleaned_conference['keywords'] = extracted_keywords
                cleaned_conference['topics'] = topics
                cleaned_conference['relevance_score'] = relevance_score
                
                # 只保留相关度大于0的会议
                if relevance_score > 0:
                    processed_conferences.append(cleaned_conference)
                    
            except Exception as e:
                logger.error(f"处理会议失败: {e}, 会议数据: {conference}")
                
        # 按相关度排序
        processed_conferences.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return processed_conferences
        
    def _clean_conference(self, conference: Dict[str, Any]) -> Dict[str, Any]:
        """清洗会议数据
        
        Args:
            conference: 原始会议数据
            
        Returns:
            清洗后的会议数据
        """
        cleaned = conference.copy()
        
        # 清洗标题
        if 'title' in cleaned and cleaned['title']:
            cleaned['title'] = self._clean_text(cleaned['title'])
            
        # 清洗描述
        if 'description' in cleaned and cleaned['description']:
            cleaned['description'] = self._clean_text(cleaned['description'])
            
        # 清洗地点
        if 'location' in cleaned and cleaned['location']:
            cleaned['location'] = self._clean_text(cleaned['location'])
            
        # 标准化日期
        if 'start_date' in cleaned:
            cleaned['start_date'] = self._normalize_date(cleaned['start_date'])
            
        if 'end_date' in cleaned:
            cleaned['end_date'] = self._normalize_date(cleaned['end_date'])
            
        # 标准化地区
        if 'region' in cleaned:
            cleaned['region'] = self._normalize_region(cleaned['region'])
            
        # 确保URL格式正确
        if 'url' in cleaned and cleaned['url']:
            if not cleaned['url'].startswith(('http://', 'https://')):
                cleaned['url'] = 'https://' + cleaned['url']
                
        if 'registration_url' in cleaned and cleaned['registration_url']:
            if not cleaned['registration_url'].startswith(('http://', 'https://')):
                cleaned['registration_url'] = 'https://' + cleaned['registration_url']
                
        return cleaned
        
    def _clean_text(self, text: str) -> str:
        """清洗文本
        
        Args:
            text: 原始文本
            
        Returns:
            清洗后的文本
        """
        if not text:
            return ''
            
        # 转换为字符串
        text = str(text)
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除特殊字符，保留字母、数字和基本标点
        text = re.sub(r'[^\w\s\.\,\-\(\)\:]', '', text)
        
        # 移除多余的空格
        text = re.sub(r'\s+', ' ', text)
        
        # 移除首尾空格
        text = text.strip()
        
        return text
        
    def _normalize_date(self, date_obj: Any) -> Optional[date]:
        """标准化日期
        
        Args:
            date_obj: 日期对象或字符串
            
        Returns:
            标准化的日期对象
        """
        if date_obj is None:
            return None
            
        if isinstance(date_obj, date):
            return date_obj
            
        if isinstance(date_obj, datetime):
            return date_obj.date()
            
        if isinstance(date_obj, str):
            # 尝试解析日期字符串
            date_formats = [
                '%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y',
                '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y',
                '%Y年%m月%d日', '%m月%d日,%Y', '%d日%m月%Y年'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_obj, fmt).date()
                except ValueError:
                    continue
                    
        return None
        
    def _normalize_region(self, region: str) -> str:
        """标准化地区名称
        
        Args:
            region: 地区名称
            
        Returns:
            标准化的地区名称
        """
        if not region:
            return 'unknown'
            
        # 转换为小写
        region = region.lower()
        
        # 标准化地区名称
        region_mapping = {
            'china': ['china', 'cn', '中国', '大陆'],
            'hongkong': ['hongkong', 'hk', '香港'],
            'us': ['us', 'usa', 'united states', 'america', '美国'],
            'singapore': ['singapore', 'sg', '新加坡'],
            'japan': ['japan', 'jp', '日本'],
            'indonesia': ['indonesia', 'id', '印尼', '印度尼西亚']
        }
        
        for standard_region, variants in region_mapping.items():
            if region in variants:
                return standard_region
                
        return 'unknown'
        
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词
        
        Args:
            text: 输入文本
            
        Returns:
            提取的关键词列表
        """
        if not text:
            return []
            
        # 转换为小写
        text = text.lower()
        
        # 分词
        tokens = word_tokenize(text)
        
        # 去除停用词和非字母数字字符
        tokens = [
            self.stemmer.stem(token)
            for token in tokens
            if token.isalnum() and token not in self.stop_words
        ]
        
        # 提取关键词
        extracted_keywords = []
        
        # 检查是否包含预定义关键词
        for keyword in self.keywords:
            keyword_lower = keyword.lower()
            keyword_stem = self.stemmer.stem(keyword_lower)
            
            # 检查原始关键词
            if keyword_lower in text:
                extracted_keywords.append(keyword)
            # 检查词干
            elif keyword_stem in tokens:
                extracted_keywords.append(keyword)
                
        # 去重
        extracted_keywords = list(set(extracted_keywords))
        
        return extracted_keywords
        
    def _classify_topics(self, keywords: List[str]) -> List[str]:
        """根据关键词分类主题
        
        Args:
            keywords: 关键词列表
            
        Returns:
            主题列表
        """
        topics = set()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            for topic, topic_keywords in self.topic_mapping.items():
                for topic_keyword in topic_keywords:
                    if topic_keyword.lower() == keyword_lower:
                        topics.add(topic)
                        break
                        
        return list(topics)
        
    def _calculate_relevance_score(self, keywords: List[str], topics: List[str]) -> float:
        """计算会议与关注领域的相关度得分
        
        Args:
            keywords: 提取的关键词列表
            topics: 分类的主题列表
            
        Returns:
            相关度得分，范围0-10
        """
        if not keywords and not topics:
            return 0.0
            
        # 基础得分
        score = 0.0
        
        # 关键词得分
        keyword_score = len(keywords) * 0.5
        
        # 主题得分
        topic_score = len(topics) * 1.0
        
        # 核心主题加分
        core_topics = ['AI', 'Remote Patient Monitoring', 'Telemedicine', 'Digital Health']
        core_topic_bonus = sum(1.5 for topic in topics if topic in core_topics)
        
        # 总分
        score = keyword_score + topic_score + core_topic_bonus
        
        # 限制最高分为10分
        score = min(score, 10.0)
        
        return score
        
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """从文本中提取实体（如组织机构、地点等）
        
        Args:
            text: 输入文本
            
        Returns:
            实体字典
        """
        entities = {
            'organizations': [],
            'locations': [],
            'persons': []
        }
        
        # 这里可以使用更复杂的NLP技术进行实体识别
        # 简单实现，使用正则表达式匹配
        
        # 匹配可能的组织机构（包含特定关键词的短语）
        org_pattern = r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:Institution|Institute|University|College|Center|Centre|Foundation|Association|Society|Group|Corporation|Company|Inc\.|Ltd\.|LLC)\b'
        org_matches = re.findall(org_pattern, text)
        entities['organizations'] = org_matches
        
        # 匹配可能的地点（包含特定关键词的短语）
        location_pattern = r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:City|Town|Province|State|Country|Region|District)\b'
        location_matches = re.findall(location_pattern, text)
        entities['locations'] = location_matches
        
        return entities
        
    def generate_summary(self, text: str, max_length: int = 150) -> str:
        """生成文本摘要
        
        Args:
            text: 输入文本
            max_length: 摘要最大长度
            
        Returns:
            文本摘要
        """
        if not text:
            return ''
            
        # 简单实现，截取前max_length个字符
        if len(text) <= max_length:
            return text
            
        # 尝试在句子边界截断
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        
        if last_period > max_length * 0.7:
            return truncated[:last_period + 1]
            
        return truncated + '...'