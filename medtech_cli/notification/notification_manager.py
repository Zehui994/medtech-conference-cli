import os
import smtplib
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BaseNotifier:
    """基础通知器类，提供通用的通知功能"""
    
    def __init__(self, config=None):
        """初始化通知器
        
        Args:
            config: 配置对象
        """
        self.config = config
        
    def send_notification(self, subject: str, message: str, 
                         recipients: List[str], **kwargs) -> bool:
        """发送通知
        
        Args:
            subject: 通知主题
            message: 通知内容
            recipients: 接收者列表
            **kwargs: 其他参数
            
        Returns:
            是否发送成功
        """
        raise NotImplementedError("子类必须实现send_notification方法")
        
    def format_message(self, template: str, data: Dict[str, Any]) -> str:
        """格式化消息内容
        
        Args:
            template: 消息模板
            data: 模板数据
            
        Returns:
            格式化后的消息
        """
        try:
            return template.format(**data)
        except KeyError as e:
            logger.error(f"消息格式化失败: 缺少键 {e}")
            return template
            
    def generate_daily_digest(self, latest_conferences: List[Dict[str, Any]],
                            upcoming_conferences: List[Dict[str, Any]],
                            recommended_conferences: List[Dict[str, Any]]) -> str:
        """生成每日会议简报
        
        Args:
            latest_conferences: 最新会议列表
            upcoming_conferences: 即将举行的会议列表
            recommended_conferences: 推荐会议列表
            
        Returns:
            每日简报内容
        """
        today = date.today().strftime('%Y年%m月%d日')
        
        digest = f"""
# 医疗科技会议日报 ({today})

## 今日推荐会议

"""
        
        if recommended_conferences:
            for i, conf in enumerate(recommended_conferences, 1):
                digest += f"""### {i}. {conf.get('title', '未命名会议')}
- 日期: {conf.get('start_date', '').strftime('%Y年%m月%d日') if hasattr(conf.get('start_date'), 'strftime') else '待定'}
- 地点: {conf.get('location', '待定')}
- 地区: {conf.get('region', '未知')}
- 主题: {', '.join(conf.get('topics', []))}
- 推荐度: {conf.get('recommendation_score', 0):.1f}/10
- 链接: {conf.get('url', '#')}

"""
        else:
            digest += "暂无推荐会议\n\n"
            
        digest += """## 即将举行的会议

"""
        
        if upcoming_conferences:
            for conf in upcoming_conferences[:5]:  # 只显示前5个
                digest += f"""### {conf.get('title', '未命名会议')}
- 日期: {conf.get('start_date', '').strftime('%Y年%m月%d日') if hasattr(conf.get('start_date'), 'strftime') else '待定'}
- 地点: {conf.get('location', '待定')}
- 地区: {conf.get('region', '未知')}
- 主题: {', '.join(conf.get('topics', []))}
- 相关度: {conf.get('relevance_score', 0):.1f}/10
- 链接: {conf.get('url', '#')}

"""
        else:
            digest += "暂无即将举行的会议\n\n"
            
        digest += """## 最新添加的会议

"""
        
        if latest_conferences:
            for conf in latest_conferences[:5]:  # 只显示前5个
                digest += f"""### {conf.get('title', '未命名会议')}
- 日期: {conf.get('start_date', '').strftime('%Y年%m月%d日') if hasattr(conf.get('start_date'), 'strftime') else '待定'}
- 地点: {conf.get('location', '待定')}
- 地区: {conf.get('region', '未知')}
- 主题: {', '.join(conf.get('topics', []))}
- 相关度: {conf.get('relevance_score', 0):.1f}/10
- 链接: {conf.get('url', '#')}

"""
        else:
            digest += "暂无最新添加的会议\n\n"
            
        digest += """---

此邮件由 MedTech Conference CLI 自动生成。
如需调整通知设置，请使用 `medtech-cli config schedule` 命令。
"""
        
        return digest


class EmailNotifier(BaseNotifier):
    """邮件通知器"""
    
    def __init__(self, config=None):
        """初始化邮件通知器
        
        Args:
            config: 配置对象
        """
        super().__init__(config)
        
        # 邮件配置
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.sender = os.environ.get('SMTP_SENDER', self.smtp_username)
        
        # 如果没有设置环境变量，尝试从配置中获取
        if self.config:
            email_config = self.config.get('email_config', {})
            self.smtp_server = email_config.get('smtp_server', self.smtp_server)
            self.smtp_port = email_config.get('smtp_port', self.smtp_port)
            self.smtp_username = email_config.get('smtp_username', self.smtp_username)
            self.smtp_password = email_config.get('smtp_password', self.smtp_password)
            self.sender = email_config.get('sender', self.sender)
            
    def send_notification(self, subject: str, message: str, 
                         recipients: List[str], **kwargs) -> bool:
        """发送邮件通知
        
        Args:
            subject: 邮件主题
            message: 邮件内容
            recipients: 收件人列表
            **kwargs: 其他参数，如 attachments（附件列表）
            
        Returns:
            是否发送成功
        """
        if not self.smtp_username or not self.smtp_password:
            logger.error("邮件发送失败: 未配置SMTP账号信息")
            return False
            
        if not recipients:
            logger.error("邮件发送失败: 收件人列表为空")
            return False
            
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # 添加HTML内容
            html_message = self._convert_markdown_to_html(message)
            msg.attach(MIMEText(html_message, 'html', 'utf-8'))
            
            # 添加纯文本内容（备用）
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # 添加附件
            attachments = kwargs.get('attachments', [])
            for attachment in attachments:
                if os.path.exists(attachment):
                    with open(attachment, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                        msg.attach(part)
                        
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            logger.info(f"邮件已发送至 {', '.join(recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
            
    def _convert_markdown_to_html(self, markdown: str) -> str:
        """将Markdown格式转换为HTML
        
        Args:
            markdown: Markdown格式的文本
            
        Returns:
            HTML格式的文本
        """
        # 简单的Markdown转HTML
        html = markdown
        
        # 标题
        html = re.sub(r'^# (.*)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # 列表
        html = re.sub(r'^- (.*)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        
        # 链接
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
        
        # 段落
        html = re.sub(r'^(?!<[a-z])', r'<p>', html, flags=re.MULTILINE)
        html = re.sub(r'$(?![a-z])', r'</p>', html, flags=re.MULTILINE)
        
        # 水平线
        html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
        
        # 添加基本样式
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        h1 {{
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
        }}
        ul {{
            padding-left: 20px;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .conference-card {{
            background-color: #f9f9f9;
            border-left: 4px solid #3498db;
            padding: 10px 15px;
            margin: 15px 0;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            font-size: 0.9em;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
{html}
</body>
</html>"""
        
        return html


class SlackNotifier(BaseNotifier):
    """Slack通知器"""
    
    def __init__(self, config=None):
        """初始化Slack通知器
        
        Args:
            config: 配置对象
        """
        super().__init__(config)
        
        # Slack配置
        self.slack_token = os.environ.get('SLACK_TOKEN')
        self.slack_channel = os.environ.get('SLACK_CHANNEL', '#general')
        
        # 如果没有设置环境变量，尝试从配置中获取
        if self.config:
            slack_config = self.config.get('slack_config', {})
            self.slack_token = slack_config.get('slack_token', self.slack_token)
            self.slack_channel = slack_config.get('slack_channel', self.slack_channel)
            
    def send_notification(self, subject: str, message: str, 
                         recipients: List[str], **kwargs) -> bool:
        """发送Slack通知
        
        Args:
            subject: 通知主题
            message: 通知内容
            recipients: 接收者列表（Slack中可以忽略，使用channel）
            **kwargs: 其他参数
            
        Returns:
            是否发送成功
        """
        if not self.slack_token:
            logger.error("Slack发送失败: 未配置Slack Token")
            return False
            
        try:
            # 导入Slack SDK
            from slack_sdk import WebClient
            from slack_sdk.errors import SlackApiError
            
            # 创建Slack客户端
            client = WebClient(token=self.slack_token)
            
            # 发送消息
            response = client.chat_postMessage(
                channel=self.slack_channel,
                text=f"*{subject}*\n\n{message[:3000]}",  # Slack有消息长度限制
                mrkdwn=True
            )
            
            logger.info(f"Slack消息已发送至频道 {self.slack_channel}")
            return True
            
        except ImportError:
            logger.error("Slack发送失败: 未安装slack-sdk包")
            return False
        except SlackApiError as e:
            logger.error(f"Slack发送失败: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Slack发送失败: {e}")
            return False


class ConsoleNotifier(BaseNotifier):
    """控制台通知器"""
    
    def __init__(self, config=None):
        """初始化控制台通知器
        
        Args:
            config: 配置对象
        """
        super().__init__(config)
        
    def send_notification(self, subject: str, message: str, 
                         recipients: List[str], **kwargs) -> bool:
        """发送控制台通知
        
        Args:
            subject: 通知主题
            message: 通知内容
            recipients: 接收者列表（控制台中可以忽略）
            **kwargs: 其他参数
            
        Returns:
            是否发送成功
        """
        try:
            print(f"\n{'=' * 80}")
            print(f"通知: {subject}")
            print('=' * 80)
            print(message)
            print('=' * 80)
            
            logger.info("控制台通知已显示")
            return True
            
        except Exception as e:
            logger.error(f"控制台通知显示失败: {e}")
            return False


class NotificationManager:
    """通知管理器，负责协调各种通知方式"""
    
    def __init__(self, config=None):
        """初始化通知管理器
        
        Args:
            config: 配置对象
        """
        self.config = config
        
        # 初始化各种通知器
        self.notifiers = {
            'email': EmailNotifier(config),
            'slack': SlackNotifier(config),
            'console': ConsoleNotifier(config)
        }
        
        # 默认通知渠道
        self.default_channel = 'console'
        if self.config:
            self.default_channel = self.config.get_notification_channel()
            
        # 团队成员列表
        self.team_members = []
        if self.config:
            self.team_members = self.config.get_team_members()
            
    def send_notification(self, subject: str, message: str, 
                         recipients: Optional[List[str]] = None,
                         channel: Optional[str] = None, **kwargs) -> bool:
        """发送通知
        
        Args:
            subject: 通知主题
            message: 通知内容
            recipients: 接收者列表，如果为 None 则使用团队成员
            channel: 通知渠道，如果为 None 则使用默认渠道
            **kwargs: 其他参数
            
        Returns:
            是否发送成功
        """
        # 确定通知渠道
        if channel is None:
            channel = self.default_channel
            
        # 确定接收者
        if recipients is None:
            recipients = self._get_recipients(channel)
            
        if not recipients:
            logger.error("通知发送失败: 未指定接收者")
            return False
            
        # 检查通知渠道是否支持
        if channel not in self.notifiers:
            logger.error(f"通知发送失败: 不支持的通知渠道 {channel}")
            return False
            
        # 发送通知
        notifier = self.notifiers[channel]
        return notifier.send_notification(subject, message, recipients, **kwargs)
        
    def send_daily_digest(self, latest_conferences: List[Dict[str, Any]],
                         upcoming_conferences: List[Dict[str, Any]],
                         recommended_conferences: List[Dict[str, Any]],
                         recipients: Optional[List[str]] = None,
                         channel: Optional[str] = None) -> bool:
        """发送每日会议简报
        
        Args:
            latest_conferences: 最新会议列表
            upcoming_conferences: 即将举行的会议列表
            recommended_conferences: 推荐会议列表
            recipients: 接收者列表，如果为 None 则使用团队成员
            channel: 通知渠道，如果为 None 则使用默认渠道
            
        Returns:
            是否发送成功
        """
        # 确定通知渠道
        if channel is None:
            channel = self.default_channel
            
        # 获取对应的通知器
        if channel not in self.notifiers:
            logger.error(f"通知发送失败: 不支持的通知渠道 {channel}")
            return False
            
        notifier = self.notifiers[channel]
        
        # 生成每日简报
        digest = notifier.generate_daily_digest(
            latest_conferences,
            upcoming_conferences,
            recommended_conferences
        )
        
        # 发送通知
        subject = f"医疗科技会议日报 ({date.today().strftime('%Y-%m-%d')})"
        return self.send_notification(subject, digest, recipients, channel)
        
    def send_test_notification(self) -> bool:
        """发送测试通知
        
        Returns:
            是否发送成功
        """
        subject = "测试通知"
        message = """这是一条测试通知，用于验证 MedTech Conference CLI 的通知功能是否正常工作。

如果您收到此通知，说明通知系统已正确配置。

测试时间: {}
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return self.send_notification(subject, message)
        
    def _get_recipients(self, channel: str) -> List[str]:
        """获取接收者列表
        
        Args:
            channel: 通知渠道
            
        Returns:
            接收者列表
        """
        if channel == 'email':
            # 对于邮件通知，返回团队成员的邮箱
            # 这里简化处理，实际应该从配置或数据库中获取
            return [f"{member}@example.com" for member in self.team_members]
        elif channel == 'slack':
            # 对于Slack通知，返回空列表，使用配置的频道
            return []
        else:
            # 对于其他通知，返回团队成员列表
            return self.team_members
            
    def schedule_notification(self, subject: str, message: str,
                            recipients: Optional[List[str]] = None,
                            channel: Optional[str] = None,
                            schedule_time: Optional[str] = None) -> bool:
        """安排定时通知
        
        Args:
            subject: 通知主题
            message: 通知内容
            recipients: 接收者列表，如果为 None 则使用团队成员
            channel: 通知渠道，如果为 None 则使用默认渠道
            schedule_time: 定时时间，如果为 None 则使用配置的时间
            
        Returns:
            是否安排成功
        """
        # 确定定时时间
        if schedule_time is None and self.config:
            schedule_time = self.config.get_schedule_time()
            
        if not schedule_time:
            logger.error("定时通知安排失败: 未指定定时时间")
            return False
            
        try:
            # 导入APScheduler
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            
            # 解析时间
            hour, minute = map(int, schedule_time.split(':'))
            
            # 创建调度器
            scheduler = BackgroundScheduler()
            
            # 添加任务
            scheduler.add_job(
                func=self.send_notification,
                trigger=CronTrigger(hour=hour, minute=minute),
                args=[subject, message],
                kwargs={
                    'recipients': recipients,
                    'channel': channel
                },
                id='daily_notification',
                replace_existing=True
            )
            
            # 启动调度器
            scheduler.start()
            
            logger.info(f"已安排定时通知，将在每天 {schedule_time} 发送")
            return True
            
        except ImportError:
            logger.error("定时通知安排失败: 未安装apscheduler包")
            return False
        except ValueError as e:
            logger.error(f"定时通知安排失败: {e}")
            return False
        except Exception as e:
            logger.error(f"定时通知安排失败: {e}")
            return False