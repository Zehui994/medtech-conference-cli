import logging
import math
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, date, timedelta
from collections import defaultdict, Counter

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConferenceRecommender:
    """会议推荐引擎，基于用户兴趣和历史参与记录推荐相关会议"""
    
    def __init__(self, config=None, storage=None):
        """初始化推荐引擎
        
        Args:
            config: 配置对象
            storage: 存储管理器对象
        """
        self.config = config
        self.storage = storage
        
        # 主题权重配置
        self.topic_weights = {
            'AI': 1.5,
            'Remote Patient Monitoring': 1.5,
            'Telemedicine': 1.2,
            'Digital Health': 1.2,
            'Wearables & IoT': 1.0,
            'Blockchain & Web3': 0.8,
            'Healthcare Analytics': 1.0,
            'Medical Devices': 0.9,
            'Robotics & Automation': 1.1,
            'Virtual & Augmented Reality': 0.9
        }
        
        # 时间衰减因子
        self.time_decay_factor = 0.9
        
        # 地区偏好权重
        self.region_weights = {
            'china': 1.0,
            'hongkong': 0.9,
            'us': 1.2,
            'singapore': 0.8,
            'japan': 0.8,
            'indonesia': 0.7
        }
        
    def get_recommendations(self, user: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """获取会议推荐
        
        Args:
            user: 用户名，如果为 None 则使用默认用户
            limit: 返回数量限制
            
        Returns:
            推荐的会议列表，按推荐度排序
        """
        if user is None:
            user = 'default'
            
        # 获取用户兴趣偏好
        user_preferences = self._get_user_preferences(user)
        
        # 获取用户历史参与记录
        user_history = self._get_user_history(user)
        
        # 获取候选会议
        candidate_conferences = self._get_candidate_conferences()
        
        if not candidate_conferences:
            logger.warning("没有找到候选会议")
            return []
            
        # 计算每个会议的推荐分数
        recommendations = []
        for conference in candidate_conferences:
            # 计算内容相似度分数
            content_score = self._calculate_content_similarity(
                conference, user_preferences
            )
            
            # 计算协同过滤分数
            collaborative_score = self._calculate_collaborative_score(
                conference, user_history
            )
            
            # 计算时间相关分数
            time_score = self._calculate_time_score(conference)
            
            # 计算地区偏好分数
            region_score = self._calculate_region_score(conference, user_preferences)
            
            # 计算综合推荐分数
            recommendation_score = self._calculate_recommendation_score(
                content_score, collaborative_score, time_score, region_score
            )
            
            # 添加推荐分数到会议信息中
            conference_with_score = conference.copy()
            conference_with_score['recommendation_score'] = recommendation_score
            conference_with_score['content_score'] = content_score
            conference_with_score['collaborative_score'] = collaborative_score
            conference_with_score['time_score'] = time_score
            conference_with_score['region_score'] = region_score
            
            recommendations.append(conference_with_score)
            
        # 按推荐分数排序
        recommendations.sort(key=lambda x: x.get('recommendation_score', 0), reverse=True)
        
        # 返回前N个推荐
        return recommendations[:limit]
        
    def _get_user_preferences(self, user: str) -> Dict[str, Any]:
        """获取用户兴趣偏好
        
        Args:
            user: 用户名
            
        Returns:
            用户兴趣偏好字典
        """
        if self.config:
            # 从配置中获取用户偏好
            all_preferences = self.config.get_user_preferences()
            if user in all_preferences:
                return all_preferences[user]
                
        # 默认偏好
        return {
            'topics': ['AI', 'Remote Patient Monitoring', 'Digital Health'],
            'regions': ['china', 'us'],
            'keywords': ['HomeCare', 'AI', '远程医疗'],
            'time_preference': 'upcoming',  # 'upcoming', 'recent', 'any'
            'price_preference': 'any',  # 'free', 'paid', 'any'
            'format_preference': 'any'  # 'in-person', 'virtual', 'hybrid', 'any'
        }
        
    def _get_user_history(self, user: str) -> List[Dict[str, Any]]:
        """获取用户历史参与记录
        
        Args:
            user: 用户名
            
        Returns:
            用户历史参与的会议列表
        """
        if self.storage:
            # 从存储中获取用户历史
            return self.storage.get_user_interests(user)
        else:
            return []
            
    def _get_candidate_conferences(self) -> List[Dict[str, Any]]:
        """获取候选会议列表
        
        Returns:
            候选会议列表
        """
        if self.storage:
            # 从存储中获取最近的会议
            return self.storage.get_upcoming_conferences(days=180, limit=100)
        else:
            return []
            
    def _calculate_content_similarity(self, conference: Dict[str, Any], 
                                    user_preferences: Dict[str, Any]) -> float:
        """计算会议内容与用户兴趣的相似度
        
        Args:
            conference: 会议信息
            user_preferences: 用户兴趣偏好
            
        Returns:
            内容相似度分数，范围0-1
        """
        if not conference or not user_preferences:
            return 0.0
            
        score = 0.0
        total_weight = 0.0
        
        # 检查主题匹配
        conference_topics = conference.get('topics', [])
        user_topics = user_preferences.get('topics', [])
        
        for topic in conference_topics:
            if topic in user_topics:
                # 使用主题权重
                weight = self.topic_weights.get(topic, 1.0)
                score += weight
                total_weight += weight
                
        # 检查关键词匹配
        conference_keywords = conference.get('keywords', [])
        user_keywords = user_preferences.get('keywords', [])
        
        for keyword in conference_keywords:
            if keyword.lower() in [k.lower() for k in user_keywords]:
                score += 0.5
                total_weight += 0.5
                
        # 计算相似度分数
        if total_weight > 0:
            similarity = score / total_weight
        else:
            similarity = 0.0
            
        # 归一化到0-1范围
        return min(similarity, 1.0)
        
    def _calculate_collaborative_score(self, conference: Dict[str, Any], 
                                     user_history: List[Dict[str, Any]]) -> float:
        """基于用户历史参与记录计算协同过滤分数
        
        Args:
            conference: 会议信息
            user_history: 用户历史参与记录
            
        Returns:
            协同过滤分数，范围0-1
        """
        if not user_history:
            return 0.0
            
        score = 0.0
        total_weight = 0.0
        
        # 获取会议的主题和关键词
        conference_topics = set(conference.get('topics', []))
        conference_keywords = set(conference.get('keywords', []))
        
        # 遍历用户历史记录
        for history_item in user_history:
            # 获取历史会议的主题和关键词
            history_topics = set(history_item.get('topics', []))
            history_keywords = set(history_item.get('keywords', []))
            
            # 计算主题重叠度
            topic_overlap = len(conference_topics.intersection(history_topics))
            topic_similarity = topic_overlap / (len(conference_topics) + 1)
            
            # 计算关键词重叠度
            keyword_overlap = len(conference_keywords.intersection(history_keywords))
            keyword_similarity = keyword_overlap / (len(conference_keywords) + 1)
            
            # 获取用户对历史会议的兴趣级别
            interest_level = history_item.get('interest_level', 1)
            
            # 计算时间衰减因子
            time_decay = self._calculate_time_decay(history_item.get('created_at', datetime.now()))
            
            # 计算该历史记录的贡献分数
            history_score = (topic_similarity * 0.6 + keyword_similarity * 0.4) * interest_level * time_decay
            
            score += history_score
            total_weight += interest_level * time_decay
            
        # 计算最终协同过滤分数
        if total_weight > 0:
            collaborative_score = score / total_weight
        else:
            collaborative_score = 0.0
            
        # 归一化到0-1范围
        return min(collaborative_score, 1.0)
        
    def _calculate_time_score(self, conference: Dict[str, Any]) -> float:
        """计算会议时间相关分数
        
        Args:
            conference: 会议信息
            
        Returns:
            时间相关分数，范围0-1
        """
        if 'start_date' not in conference:
            return 0.5  # 未知时间，给予中等分数
            
        today = date.today()
        start_date = conference['start_date']
        
        # 如果是过去的会议，分数为0
        if start_date < today:
            return 0.0
            
        # 计算距离今天的天数
        days_from_now = (start_date - today).days
        
        # 时间分数计算逻辑
        if days_from_now <= 7:
            # 一周内的会议
            time_score = 1.0
        elif days_from_now <= 30:
            # 一个月内的会议
            time_score = 0.9
        elif days_from_now <= 90:
            # 三个月内的会议
            time_score = 0.7
        elif days_from_now <= 180:
            # 半年内的会议
            time_score = 0.5
        else:
            # 半年后的会议
            time_score = 0.3
            
        return time_score
        
    def _calculate_region_score(self, conference: Dict[str, Any], 
                              user_preferences: Dict[str, Any]) -> float:
        """计算地区偏好分数
        
        Args:
            conference: 会议信息
            user_preferences: 用户兴趣偏好
            
        Returns:
            地区偏好分数，范围0-1
        """
        if 'region' not in conference:
            return 0.5  # 未知地区，给予中等分数
            
        conference_region = conference['region']
        user_regions = user_preferences.get('regions', [])
        
        # 检查是否在用户偏好的地区
        if conference_region in user_regions:
            # 使用地区权重
            weight = self.region_weights.get(conference_region, 1.0)
            return min(weight, 1.0)
        else:
            return 0.3  # 不在偏好地区，给予低分
            
    def _calculate_recommendation_score(self, content_score: float, 
                                      collaborative_score: float, 
                                      time_score: float, 
                                      region_score: float) -> float:
        """计算综合推荐分数
        
        Args:
            content_score: 内容相似度分数
            collaborative_score: 协同过滤分数
            time_score: 时间相关分数
            region_score: 地区偏好分数
            
        Returns:
            综合推荐分数，范围0-10
        """
        # 权重配置
        weights = {
            'content': 0.5,
            'collaborative': 0.2,
            'time': 0.2,
            'region': 0.1
        }
        
        # 计算加权平均分
        weighted_score = (
            content_score * weights['content'] +
            collaborative_score * weights['collaborative'] +
            time_score * weights['time'] +
            region_score * weights['region']
        )
        
        # 转换到0-10分制
        recommendation_score = weighted_score * 10
        
        return recommendation_score
        
    def _calculate_time_decay(self, timestamp: Any) -> float:
        """计算时间衰减因子
        
        Args:
            timestamp: 时间戳
            
        Returns:
            时间衰减因子，范围0-1
        """
        if not timestamp:
            return 1.0
            
        # 转换为datetime对象
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return 1.0
                
        # 计算距今的天数
        now = datetime.now()
        if isinstance(timestamp, datetime):
            days_passed = (now - timestamp).days
        elif isinstance(timestamp, date):
            days_passed = (now.date() - timestamp).days
        else:
            return 1.0
            
        # 计算衰减因子
        # 使用指数衰减，半衰期为90天
        half_life = 90.0
        decay = math.pow(self.time_decay_factor, days_passed / half_life)
        
        return decay
        
    def update_user_preferences(self, user: str, preferences: Dict[str, Any]) -> bool:
        """更新用户兴趣偏好
        
        Args:
            user: 用户名
            preferences: 用户兴趣偏好
            
        Returns:
            是否成功更新
        """
        if self.config:
            # 更新配置中的用户偏好
            self.config.set_user_preferences(user, preferences)
            return True
        else:
            return False
            
    def learn_from_feedback(self, user: str, conference_id: str, 
                           feedback: str, rating: int = 1) -> bool:
        """从用户反馈中学习
        
        Args:
            user: 用户名
            conference_id: 会议ID
            feedback: 反馈类型，'like', 'dislike', 'attend', 'ignore'
            rating: 评分，1-5
            
        Returns:
            是否成功学习
        """
        # 获取用户当前偏好
        preferences = self._get_user_preferences(user)
        
        # 获取会议信息
        conference = None
        if self.storage:
            conference = self.storage.get_conference(conference_id)
            
        if not conference:
            logger.warning(f"无法找到会议: {conference_id}")
            return False
            
        # 根据反馈类型更新偏好
        if feedback == 'like' or feedback == 'attend':
            # 增加相关主题的权重
            conference_topics = conference.get('topics', [])
            user_topics = preferences.get('topics', [])
            
            # 将会议主题添加到用户偏好中
            for topic in conference_topics:
                if topic not in user_topics:
                    user_topics.append(topic)
                    
            preferences['topics'] = user_topics
            
            # 增加相关关键词的权重
            conference_keywords = conference.get('keywords', [])
            user_keywords = preferences.get('keywords', [])
            
            # 将会议关键词添加到用户偏好中
            for keyword in conference_keywords:
                if keyword not in user_keywords:
                    user_keywords.append(keyword)
                    
            preferences['keywords'] = user_keywords
            
            # 如果是参加过的会议，还可以更新地区偏好
            if feedback == 'attend' and 'region' in conference:
                conference_region = conference['region']
                user_regions = preferences.get('regions', [])
                
                if conference_region not in user_regions:
                    user_regions.append(conference_region)
                    
                preferences['regions'] = user_regions
                
        elif feedback == 'dislike':
            # 减少相关主题的权重
            conference_topics = conference.get('topics', [])
            user_topics = preferences.get('topics', [])
            
            # 将会议主题从用户偏好中移除
            for topic in conference_topics:
                if topic in user_topics:
                    user_topics.remove(topic)
                    
            preferences['topics'] = user_topics
            
        # 更新用户偏好
        return self.update_user_preferences(user, preferences)
        
    def get_similar_conferences(self, conference_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取与指定会议相似的会议
        
        Args:
            conference_id: 会议ID
            limit: 返回数量限制
            
        Returns:
            相似会议列表
        """
        # 获取指定会议
        target_conference = None
        if self.storage:
            target_conference = self.storage.get_conference(conference_id)
            
        if not target_conference:
            logger.warning(f"无法找到会议: {conference_id}")
            return []
            
        # 获取候选会议
        candidate_conferences = self._get_candidate_conferences()
        
        # 计算相似度
        similarities = []
        for conference in candidate_conferences:
            # 跳过自己
            if conference.get('id') == conference_id:
                continue
                
            # 计算主题相似度
            topic_similarity = self._calculate_topic_similarity(
                target_conference.get('topics', []),
                conference.get('topics', [])
            )
            
            # 计算关键词相似度
            keyword_similarity = self._calculate_keyword_similarity(
                target_conference.get('keywords', []),
                conference.get('keywords', [])
            )
            
            # 计算时间相似度
            time_similarity = self._calculate_time_similarity(
                target_conference.get('start_date'),
                conference.get('start_date')
            )
            
            # 计算地区相似度
            region_similarity = self._calculate_region_similarity(
                target_conference.get('region'),
                conference.get('region')
            )
            
            # 综合相似度
            similarity = (
                topic_similarity * 0.4 +
                keyword_similarity * 0.3 +
                time_similarity * 0.2 +
                region_similarity * 0.1
            )
            
            similarities.append({
                'conference': conference,
                'similarity': similarity,
                'topic_similarity': topic_similarity,
                'keyword_similarity': keyword_similarity,
                'time_similarity': time_similarity,
                'region_similarity': region_similarity
            })
            
        # 按相似度排序
        similarities.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        # 返回前N个相似会议
        return [item['conference'] for item in similarities[:limit]]
        
    def _calculate_topic_similarity(self, topics1: List[str], topics2: List[str]) -> float:
        """计算主题相似度
        
        Args:
            topics1: 主题列表1
            topics2: 主题列表2
            
        Returns:
            相似度分数，范围0-1
        """
        if not topics1 or not topics2:
            return 0.0
            
        # 计算Jaccard相似度
        set1 = set(topics1)
        set2 = set(topics2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
            
        return intersection / union
        
    def _calculate_keyword_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """计算关键词相似度
        
        Args:
            keywords1: 关键词列表1
            keywords2: 关键词列表2
            
        Returns:
            相似度分数，范围0-1
        """
        if not keywords1 or not keywords2:
            return 0.0
            
        # 计算Jaccard相似度
        set1 = set([k.lower() for k in keywords1])
        set2 = set([k.lower() for k in keywords2])
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
            
        return intersection / union
        
    def _calculate_time_similarity(self, date1: Any, date2: Any) -> float:
        """计算时间相似度
        
        Args:
            date1: 日期1
            date2: 日期2
            
        Returns:
            相似度分数，范围0-1
        """
        if not date1 or not date2:
            return 0.0
            
        # 确保都是date对象
        if isinstance(date1, datetime):
            date1 = date1.date()
        if isinstance(date2, datetime):
            date2 = date2.date()
            
        # 计算日期差
        delta = abs((date1 - date2).days)
        
        # 30天内相似度为1，超过365天相似度为0
        if delta <= 30:
            return 1.0
        elif delta >= 365:
            return 0.0
        else:
            return 1.0 - (delta - 30) / (365 - 30)
            
    def _calculate_region_similarity(self, region1: str, region2: str) -> float:
        """计算地区相似度
        
        Args:
            region1: 地区1
            region2: 地区2
            
        Returns:
            相似度分数，范围0-1
        """
        if not region1 or not region2:
            return 0.0
            
        # 相同地区相似度为1，否则为0
        return 1.0 if region1 == region2 else 0.0