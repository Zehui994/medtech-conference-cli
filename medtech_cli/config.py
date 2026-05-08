import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional


class Config:
    """配置管理类，负责读取、保存和管理工具的配置信息"""
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为用户目录下的 .medtech_cli/config.json
        """
        if config_file is None:
            self.config_dir = Path.home() / '.medtech_cli'
            self.config_file = self.config_dir / 'config.json'
        else:
            self.config_file = Path(config_file)
            self.config_dir = self.config_file.parent
            
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 默认配置
        self.default_config = {
            'keywords': [
                'HomeCare', 'AI', 'Artificial Intelligence', 'web3', 'RPM', 
                'Remote Patient Monitoring', '远程医疗', '医疗科技', '数字健康',
                'HealthTech', 'Digital Health', '医疗AI', '医疗机器人', '智能医疗'
            ],
            'regions': [
                'china', 'hongkong', 'us', 'singapore', 'japan', 'indonesia'
            ],
            'schedule_time': '09:00',
            'notification_channel': 'email',
            'database_path': str(self.config_dir / 'medtech.db'),
            'log_level': 'INFO',
            'crawler_interval': 24,  # 小时
            'user_preferences': {},
            'team_members': []
        }
        
        # 加载配置
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """从配置文件加载配置
        
        Returns:
            配置字典，如果文件不存在则返回默认配置
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置和用户配置
                    return {**self.default_config, **config}
            except (json.JSONDecodeError, IOError) as e:
                print(f"警告: 无法加载配置文件 {self.config_file}, 使用默认配置. 错误: {e}")
                return self.default_config.copy()
        else:
            # 配置文件不存在，创建默认配置
            self._save_config(self.default_config)
            return self.default_config.copy()
            
    def _save_config(self, config: Dict[str, Any]) -> None:
        """保存配置到文件
        
        Args:
            config: 要保存的配置字典
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"错误: 无法保存配置文件 {self.config_file}. 错误: {e}")
            
    def save(self) -> None:
        """保存当前配置到文件"""
        self._save_config(self.config)
        
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置键名
            default: 默认值，如果键不存在则返回
            
        Returns:
            配置值
        """
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """设置配置项
        
        Args:
            key: 配置键名
            value: 配置值
        """
        self.config[key] = value
        self.save()
        
    def get_keywords(self) -> List[str]:
        """获取关注的关键词列表
        
        Returns:
            关键词列表
        """
        return self.config.get('keywords', [])
        
    def add_keywords(self, keywords: List[str]) -> None:
        """添加关键词
        
        Args:
            keywords: 要添加的关键词列表
        """
        current_keywords = self.get_keywords()
        for keyword in keywords:
            if keyword not in current_keywords:
                current_keywords.append(keyword)
        self.config['keywords'] = current_keywords
        self.save()
        
    def remove_keywords(self, keywords: List[str]) -> None:
        """移除关键词
        
        Args:
            keywords: 要移除的关键词列表
        """
        current_keywords = self.get_keywords()
        self.config['keywords'] = [k for k in current_keywords if k not in keywords]
        self.save()
        
    def get_regions(self) -> List[str]:
        """获取关注的地区列表
        
        Returns:
            地区列表
        """
        return self.config.get('regions', [])
        
    def add_regions(self, regions: List[str]) -> None:
        """添加地区
        
        Args:
            regions: 要添加的地区列表
        """
        current_regions = self.get_regions()
        for region in regions:
            if region not in current_regions:
                current_regions.append(region)
        self.config['regions'] = current_regions
        self.save()
        
    def remove_regions(self, regions: List[str]) -> None:
        """移除地区
        
        Args:
            regions: 要移除的地区列表
        """
        current_regions = self.get_regions()
        self.config['regions'] = [r for r in current_regions if r not in regions]
        self.save()
        
    def get_schedule_time(self) -> str:
        """获取推送时间
        
        Returns:
            推送时间，格式为 "HH:MM"
        """
        return self.config.get('schedule_time', '09:00')
        
    def set_schedule_time(self, time: str) -> None:
        """设置推送时间
        
        Args:
            time: 推送时间，格式为 "HH:MM"
        """
        # 简单验证时间格式
        try:
            hours, minutes = map(int, time.split(':'))
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError("时间格式不正确")
            self.config['schedule_time'] = time
            self.save()
        except (ValueError, AttributeError):
            raise ValueError(f"无效的时间格式: {time}, 应为 HH:MM 格式")
            
    def get_notification_channel(self) -> str:
        """获取通知渠道
        
        Returns:
            通知渠道，如 'email', 'slack' 等
        """
        return self.config.get('notification_channel', 'email')
        
    def set_notification_channel(self, channel: str) -> None:
        """设置通知渠道
        
        Args:
            channel: 通知渠道，如 'email', 'slack' 等
        """
        # 验证渠道是否有效
        valid_channels = ['email', 'slack', 'console']
        if channel not in valid_channels:
            raise ValueError(f"无效的通知渠道: {channel}, 应为 {', '.join(valid_channels)} 之一")
            
        self.config['notification_channel'] = channel
        self.save()
        
    def get_database_path(self) -> str:
        """获取数据库路径
        
        Returns:
            数据库文件路径
        """
        return self.config.get('database_path', str(self.config_dir / 'medtech.db'))
        
    def get_log_level(self) -> str:
        """获取日志级别
        
        Returns:
            日志级别，如 'DEBUG', 'INFO', 'WARNING' 等
        """
        return self.config.get('log_level', 'INFO')
        
    def get_crawler_interval(self) -> int:
        """获取爬虫运行间隔
        
        Returns:
            爬虫运行间隔，单位为小时
        """
        return self.config.get('crawler_interval', 24)
        
    def get_user_preferences(self, user: Optional[str] = None) -> Dict[str, Any]:
        """获取用户偏好设置
        
        Args:
            user: 用户名，如果为 None 则返回所有用户的偏好设置
            
        Returns:
            用户偏好设置字典
        """
        preferences = self.config.get('user_preferences', {})
        if user is None:
            return preferences
        return preferences.get(user, {})
        
    def set_user_preferences(self, user: str, preferences: Dict[str, Any]) -> None:
        """设置用户偏好
        
        Args:
            user: 用户名
            preferences: 用户偏好设置字典
        """
        if 'user_preferences' not in self.config:
            self.config['user_preferences'] = {}
            
        self.config['user_preferences'][user] = preferences
        self.save()
        
    def get_team_members(self) -> List[str]:
        """获取团队成员列表
        
        Returns:
            团队成员用户名列表
        """
        return self.config.get('team_members', [])
        
    def add_team_member(self, member: str) -> None:
        """添加团队成员
        
        Args:
            member: 团队成员用户名
        """
        members = self.get_team_members()
        if member not in members:
            members.append(member)
            self.config['team_members'] = members
            self.save()
            
    def remove_team_member(self, member: str) -> None:
        """移除团队成员
        
        Args:
            member: 团队成员用户名
        """
        members = self.get_team_members()
        self.config['team_members'] = [m for m in members if m != member]
        self.save()