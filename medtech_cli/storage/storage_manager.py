import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager


class StorageManager:
    """存储管理器，负责会议数据的存储和检索"""
    
    def __init__(self, config=None):
        """初始化存储管理器
        
        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        if config is None:
            from medtech_cli.config import Config
            config = Config()
            
        self.db_path = Path(config.get_database_path())
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器
        
        Yields:
            sqlite3.Connection: 数据库连接
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def _init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建会议表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conferences (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    topics TEXT,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    location TEXT,
                    region TEXT NOT NULL,
                    organizer TEXT,
                    url TEXT,
                    registration_url TEXT,
                    price TEXT,
                    keywords TEXT,
                    relevance_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建会议兴趣表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conference_interest (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conference_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    interest_level INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'interested',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conference_id) REFERENCES conferences (id),
                    UNIQUE(conference_id, user_id)
                )
            ''')
            
            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    preferences TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conferences_region ON conferences (region)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conferences_start_date ON conferences (start_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conference_interest_user ON conference_interest (user_id)')
            
            conn.commit()
            
    def save_conference(self, conference: Dict[str, Any]) -> bool:
        """保存单个会议信息
        
        Args:
            conference: 会议信息字典
            
        Returns:
            bool: 是否成功保存
        """
        # 确保会议有唯一ID
        if 'id' not in conference:
            import uuid
            conference['id'] = str(uuid.uuid4())
            
        # 确保日期格式正确
        for date_key in ['start_date', 'end_date']:
            if date_key in conference and conference[date_key]:
                if isinstance(conference[date_key], str):
                    try:
                        # 尝试解析日期字符串
                        conference[date_key] = datetime.strptime(
                            conference[date_key], '%Y-%m-%d'
                        ).date()
                    except ValueError:
                        # 如果解析失败，使用当前日期
                        conference[date_key] = datetime.now().date()
                        
        # 处理列表类型的字段，转换为JSON字符串
        for list_key in ['topics', 'keywords']:
            if list_key in conference and isinstance(conference[list_key], list):
                conference[list_key] = json.dumps(conference[list_key])
                
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查会议是否已存在
            cursor.execute('SELECT id FROM conferences WHERE id = ?', (conference['id'],))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有会议
                try:
                    cursor.execute('''
                        UPDATE conferences SET
                            title = ?,
                            description = ?,
                            topics = ?,
                            start_date = ?,
                            end_date = ?,
                            location = ?,
                            region = ?,
                            organizer = ?,
                            url = ?,
                            registration_url = ?,
                            price = ?,
                            keywords = ?,
                            relevance_score = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        conference.get('title', ''),
                        conference.get('description', ''),
                        conference.get('topics', ''),
                        conference.get('start_date', None),
                        conference.get('end_date', None),
                        conference.get('location', ''),
                        conference.get('region', ''),
                        conference.get('organizer', ''),
                        conference.get('url', ''),
                        conference.get('registration_url', ''),
                        conference.get('price', ''),
                        conference.get('keywords', ''),
                        conference.get('relevance_score', 0.0),
                        conference['id']
                    ))
                    return True
                except Exception as e:
                    print(f"更新会议失败: {e}")
                    return False
            else:
                # 插入新会议
                try:
                    cursor.execute('''
                        INSERT INTO conferences (
                            id, title, description, topics, start_date, end_date,
                            location, region, organizer, url, registration_url,
                            price, keywords, relevance_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        conference['id'],
                        conference.get('title', ''),
                        conference.get('description', ''),
                        conference.get('topics', ''),
                        conference.get('start_date', None),
                        conference.get('end_date', None),
                        conference.get('location', ''),
                        conference.get('region', ''),
                        conference.get('organizer', ''),
                        conference.get('url', ''),
                        conference.get('registration_url', ''),
                        conference.get('price', ''),
                        conference.get('keywords', ''),
                        conference.get('relevance_score', 0.0)
                    ))
                    return True
                except Exception as e:
                    print(f"插入会议失败: {e}")
                    return False
                    
    def save_conferences(self, conferences: List[Dict[str, Any]]) -> int:
        """批量保存会议信息
        
        Args:
            conferences: 会议信息列表
            
        Returns:
            int: 成功保存的会议数量
        """
        saved_count = 0
        for conference in conferences:
            if self.save_conference(conference):
                saved_count += 1
        return saved_count
        
    def get_conference(self, conference_id: str) -> Optional[Dict[str, Any]]:
        """获取单个会议信息
        
        Args:
            conference_id: 会议ID
            
        Returns:
            会议信息字典，如果不存在则返回 None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM conferences WHERE id = ?', (conference_id,))
            row = cursor.fetchone()
            
            if row:
                conference = dict(row)
                # 解析JSON字段
                for json_key in ['topics', 'keywords']:
                    if conference.get(json_key):
                        try:
                            conference[json_key] = json.loads(conference[json_key])
                        except json.JSONDecodeError:
                            conference[json_key] = []
                return conference
            return None
            
    def get_upcoming_conferences(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """获取即将举行的会议
        
        Args:
            days: 未来天数
            limit: 返回数量限制
            
        Returns:
            会议信息列表
        """
        today = datetime.now().date()
        future_date = today + timedelta(days=days)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM conferences
                WHERE start_date >= ? AND start_date <= ?
                ORDER BY start_date ASC, relevance_score DESC
                LIMIT ?
            ''', (today, future_date, limit))
            
            rows = cursor.fetchall()
            conferences = []
            for row in rows:
                conference = dict(row)
                # 解析JSON字段
                for json_key in ['topics', 'keywords']:
                    if conference.get(json_key):
                        try:
                            conference[json_key] = json.loads(conference[json_key])
                        except json.JSONDecodeError:
                            conference[json_key] = []
                conferences.append(conference)
                
            return conferences
            
    def get_latest_conferences(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最新添加的会议
        
        Args:
            limit: 返回数量限制
            
        Returns:
            会议信息列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM conferences
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conferences = []
            for row in rows:
                conference = dict(row)
                # 解析JSON字段
                for json_key in ['topics', 'keywords']:
                    if conference.get(json_key):
                        try:
                            conference[json_key] = json.loads(conference[json_key])
                        except json.JSONDecodeError:
                            conference[json_key] = []
                conferences.append(conference)
                
            return conferences
            
    def get_conferences_by_region(self, region: str, limit: int = 10) -> List[Dict[str, Any]]:
        """按地区获取会议
        
        Args:
            region: 地区名称
            limit: 返回数量限制
            
        Returns:
            会议信息列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM conferences
                WHERE region = ?
                ORDER BY start_date ASC
                LIMIT ?
            ''', (region, limit))
            
            rows = cursor.fetchall()
            conferences = []
            for row in rows:
                conference = dict(row)
                # 解析JSON字段
                for json_key in ['topics', 'keywords']:
                    if conference.get(json_key):
                        try:
                            conference[json_key] = json.loads(conference[json_key])
                        except json.JSONDecodeError:
                            conference[json_key] = []
                conferences.append(conference)
                
            return conferences
            
    def get_conferences_by_topic(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """按主题获取会议
        
        Args:
            topic: 主题关键词
            limit: 返回数量限制
            
        Returns:
            会议信息列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM conferences
                WHERE topics LIKE ? OR keywords LIKE ?
                ORDER BY relevance_score DESC, start_date ASC
                LIMIT ?
            ''', (f'%{topic}%', f'%{topic}%', limit))
            
            rows = cursor.fetchall()
            conferences = []
            for row in rows:
                conference = dict(row)
                # 解析JSON字段
                for json_key in ['topics', 'keywords']:
                    if conference.get(json_key):
                        try:
                            conference[json_key] = json.loads(conference[json_key])
                        except json.JSONDecodeError:
                            conference[json_key] = []
                conferences.append(conference)
                
            return conferences
            
    def mark_conference_interest(self, conference_id: str, user_id: str = 'default', 
                               interest_level: int = 1, status: str = 'interested',
                               notes: str = '') -> bool:
        """标记用户对会议的兴趣
        
        Args:
            conference_id: 会议ID
            user_id: 用户ID，默认为 'default'
            interest_level: 兴趣级别，1-5
            status: 状态，如 'interested', 'registered', 'attended' 等
            notes: 备注
            
        Returns:
            bool: 是否成功标记
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查会议是否存在
            cursor.execute('SELECT id FROM conferences WHERE id = ?', (conference_id,))
            if not cursor.fetchone():
                print(f"会议不存在: {conference_id}")
                return False
                
            # 检查用户是否存在，如果不存在则创建
            cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO users (id, name) VALUES (?, ?)', 
                              (user_id, user_id))
                
            # 检查是否已存在兴趣记录
            cursor.execute('''
                SELECT id FROM conference_interest
                WHERE conference_id = ? AND user_id = ?
            ''', (conference_id, user_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有记录
                try:
                    cursor.execute('''
                        UPDATE conference_interest SET
                            interest_level = ?,
                            status = ?,
                            notes = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE conference_id = ? AND user_id = ?
                    ''', (interest_level, status, notes, conference_id, user_id))
                    return True
                except Exception as e:
                    print(f"更新兴趣记录失败: {e}")
                    return False
            else:
                # 插入新记录
                try:
                    cursor.execute('''
                        INSERT INTO conference_interest (
                            conference_id, user_id, interest_level, status, notes
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (conference_id, user_id, interest_level, status, notes))
                    return True
                except Exception as e:
                    print(f"插入兴趣记录失败: {e}")
                    return False
                    
    def get_user_interests(self, user_id: str = 'default') -> List[Dict[str, Any]]:
        """获取用户感兴趣的会议
        
        Args:
            user_id: 用户ID，默认为 'default'
            
        Returns:
            会议信息列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, ci.interest_level, ci.status, ci.notes
                FROM conferences c
                JOIN conference_interest ci ON c.id = ci.conference_id
                WHERE ci.user_id = ?
                ORDER BY ci.interest_level DESC, c.start_date ASC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conferences = []
            for row in rows:
                conference = dict(row)
                # 解析JSON字段
                for json_key in ['topics', 'keywords']:
                    if conference.get(json_key):
                        try:
                            conference[json_key] = json.loads(conference[json_key])
                        except json.JSONDecodeError:
                            conference[json_key] = []
                conferences.append(conference)
                
            return conferences
            
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'total_conferences': 0,
            'upcoming_conferences': 0,
            'by_region': {},
            'by_topic': {}
        }
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 总会议数
            cursor.execute('SELECT COUNT(*) FROM conferences')
            stats['total_conferences'] = cursor.fetchone()[0]
            
            # 即将举行的会议数
            today = datetime.now().date()
            cursor.execute('SELECT COUNT(*) FROM conferences WHERE start_date >= ?', (today,))
            stats['upcoming_conferences'] = cursor.fetchone()[0]
            
            # 按地区统计
            cursor.execute('''
                SELECT region, COUNT(*) as count
                FROM conferences
                GROUP BY region
                ORDER BY count DESC
            ''')
            for row in cursor.fetchall():
                stats['by_region'][row['region']] = row['count']
                
            # 按主题统计（简化版，实际可能需要更复杂的解析）
            cursor.execute('SELECT topics FROM conferences WHERE topics IS NOT NULL AND topics != ""')
            topic_counts = {}
            for row in cursor.fetchall():
                try:
                    topics = json.loads(row['topics'])
                    for topic in topics:
                        if topic in topic_counts:
                            topic_counts[topic] += 1
                        else:
                            topic_counts[topic] = 1
                except (json.JSONDecodeError, TypeError):
                    pass
                    
            # 取前10个主题
            stats['by_topic'] = dict(sorted(
                topic_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10])
            
        return stats