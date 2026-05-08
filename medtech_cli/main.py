import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import print as rprint

from medtech_cli.config import Config
from medtech_cli.crawlers import ConferenceCrawler
from medtech_cli.processors import ConferenceProcessor
from medtech_cli.recommender import ConferenceRecommender
from medtech_cli.notification import NotificationManager
from medtech_cli.storage import StorageManager

console = Console()
config = Config()
storage = StorageManager()
crawler = ConferenceCrawler(config)
processor = ConferenceProcessor(config)
recommender = ConferenceRecommender(config, storage)
notification = NotificationManager(config)


@click.group()
def cli():
    """医疗科技会议信息管理工具"""
    pass


@cli.command()
@click.option('--region', '-r', default=None, help='指定地区')
@click.option('--topic', '-t', default=None, help='指定主题')
@click.option('--days', '-d', default=30, help='未来天数')
def crawl(region, topic, days):
    """手动触发会议数据采集"""
    console.print(f"[bold blue]开始采集会议数据...[/bold blue]")
    
    try:
        # 构建爬虫参数
        params = {}
        if region:
            params['region'] = region
        if topic:
            params['topic'] = topic
        if days:
            params['days'] = days
            
        # 执行爬虫
        results = crawler.crawl(**params)
        
        # 处理数据
        processed_results = processor.process(results)
        
        # 保存到数据库
        saved_count = storage.save_conferences(processed_results)
        
        console.print(f"[bold green]采集完成！成功保存 {saved_count} 条会议信息[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]采集过程中发生错误: {str(e)}[/bold red]")


@cli.group()
def list():
    """列出会议信息"""
    pass


@list.command()
@click.option('--limit', '-l', default=10, help='显示数量限制')
def upcoming(limit):
    """列出即将举行的会议"""
    console.print(f"[bold blue]即将举行的会议 (未来30天内)[/bold blue]")
    
    try:
        conferences = storage.get_upcoming_conferences(limit=limit)
        
        if not conferences:
            console.print("[yellow]没有找到即将举行的会议[/yellow]")
            return
            
        # 显示会议列表
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("日期", style="dim")
        table.add_column("会议名称", width=40)
        table.add_column("地区")
        table.add_column("主题")
        table.add_column("相关度")
        
        for conf in conferences:
            table.add_row(
                conf['start_date'].strftime('%Y-%m-%d'),
                conf['title'],
                conf['region'],
                ', '.join(conf['topics'][:2]) + ('...' if len(conf['topics']) > 2 else ''),
                f"{conf['relevance_score']:.1f}"
            )
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]查询过程中发生错误: {str(e)}[/bold red]")


@list.command()
@click.argument('region')
@click.option('--limit', '-l', default=10, help='显示数量限制')
def by_region(region, limit):
    """按地区筛选会议"""
    console.print(f"[bold blue]{region}地区的会议[/bold blue]")
    
    try:
        conferences = storage.get_conferences_by_region(region, limit=limit)
        
        if not conferences:
            console.print(f"[yellow]没有找到{region}地区的会议[/yellow]")
            return
            
        # 显示会议列表
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("日期", style="dim")
        table.add_column("会议名称", width=40)
        table.add_column("地点")
        table.add_column("主题")
        
        for conf in conferences:
            table.add_row(
                conf['start_date'].strftime('%Y-%m-%d'),
                conf['title'],
                conf['location'],
                ', '.join(conf['topics'][:2]) + ('...' if len(conf['topics']) > 2 else '')
            )
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]查询过程中发生错误: {str(e)}[/bold red]")


@list.command()
@click.argument('topic')
@click.option('--limit', '-l', default=10, help='显示数量限制')
def by_topic(topic, limit):
    """按主题筛选会议"""
    console.print(f"[bold blue]关于 {topic} 的会议[/bold blue]")
    
    try:
        conferences = storage.get_conferences_by_topic(topic, limit=limit)
        
        if not conferences:
            console.print(f"[yellow]没有找到关于{topic}的会议[/yellow]")
            return
            
        # 显示会议列表
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("日期", style="dim")
        table.add_column("会议名称", width=40)
        table.add_column("地区")
        table.add_column("地点")
        table.add_column("相关度")
        
        for conf in conferences:
            table.add_row(
                conf['start_date'].strftime('%Y-%m-%d'),
                conf['title'],
                conf['region'],
                conf['location'],
                f"{conf['relevance_score']:.1f}"
            )
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]查询过程中发生错误: {str(e)}[/bold red]")


@cli.command()
@click.option('--user', '-u', default=None, help='指定用户')
@click.option('--limit', '-l', default=5, help='显示数量限制')
def recommend(user, limit):
    """显示推荐会议"""
    console.print(f"[bold blue]为您推荐的会议[/bold blue]")
    
    try:
        # 获取推荐会议
        recommendations = recommender.get_recommendations(user=user, limit=limit)
        
        if not recommendations:
            console.print("[yellow]暂无推荐会议，请先设置您的兴趣偏好[/yellow]")
            return
            
        # 显示推荐会议
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("推荐度", style="dim")
        table.add_column("会议名称", width=40)
        table.add_column("日期")
        table.add_column("地区")
        table.add_column("主题")
        
        for conf in recommendations:
            table.add_row(
                f"{conf['recommendation_score']:.1f}",
                conf['title'],
                conf['start_date'].strftime('%Y-%m-%d'),
                conf['region'],
                ', '.join(conf['topics'][:2]) + ('...' if len(conf['topics']) > 2 else '')
            )
            
        console.print(table)
        
        # 询问用户是否对某个会议感兴趣
        if recommendations:
            interest = Confirm.ask("您对以上推荐的会议感兴趣吗？")
            if interest:
                conf_id = Prompt.ask("请输入您感兴趣的会议ID")
                storage.mark_conference_interest(conf_id, user=user)
                console.print("[green]已记录您的兴趣，谢谢反馈！[/green]")
        
    except Exception as e:
        console.print(f"[bold red]获取推荐过程中发生错误: {str(e)}[/bold red]")


@cli.group()
def config():
    """配置工具参数"""
    pass


@config.command()
@click.option('--add', '-a', default=None, help='添加关键词')
@click.option('--remove', '-r', default=None, help='移除关键词')
@click.option('--list', '-l', is_flag=True, help='列出所有关键词')
def keywords(add, remove, list):
    """设置关注的关键词"""
    if list:
        current_keywords = config.get_keywords()
        console.print(f"[bold blue]当前关注的关键词:[/bold blue]")
        for keyword in current_keywords:
            console.print(f"  - {keyword}")
        return
        
    if add:
        new_keywords = [k.strip() for k in add.split(',')]
        config.add_keywords(new_keywords)
        console.print(f"[green]已添加关键词: {', '.join(new_keywords)}[/green]")
        
    if remove:
        remove_keywords = [k.strip() for k in remove.split(',')]
        config.remove_keywords(remove_keywords)
        console.print(f"[green]已移除关键词: {', '.join(remove_keywords)}[/green]")


@config.command()
@click.option('--add', '-a', default=None, help='添加地区')
@click.option('--remove', '-r', default=None, help='移除地区')
@click.option('--list', '-l', is_flag=True, help='列出所有地区')
def regions(add, remove, list):
    """设置关注的地区"""
    if list:
        current_regions = config.get_regions()
        console.print(f"[bold blue]当前关注的地区:[/bold blue]")
        for region in current_regions:
            console.print(f"  - {region}")
        return
        
    if add:
        new_regions = [r.strip() for r in add.split(',')]
        config.add_regions(new_regions)
        console.print(f"[green]已添加地区: {', '.join(new_regions)}[/green]")
        
    if remove:
        remove_regions = [r.strip() for r in remove.split(',')]
        config.remove_regions(remove_regions)
        console.print(f"[green]已移除地区: {', '.join(remove_regions)}[/green]")


@config.command()
@click.option('--time', '-t', default=None, help='设置推送时间')
@click.option('--channel', '-c', default=None, help='设置推送渠道')
@click.option('--list', '-l', is_flag=True, help='列出当前设置')
def schedule(time, channel, list):
    """设置推送时间和渠道"""
    if list:
        current_time = config.get_schedule_time()
        current_channel = config.get_notification_channel()
        console.print(f"[bold blue]当前推送设置:[/bold blue]")
        console.print(f"  - 推送时间: {current_time}")
        console.print(f"  - 推送渠道: {current_channel}")
        return
        
    if time:
        config.set_schedule_time(time)
        console.print(f"[green]已设置推送时间: {time}[/green]")
        
    if channel:
        config.set_notification_channel(channel)
        console.print(f"[green]已设置推送渠道: {channel}[/green]")


@cli.command()
def stats():
    """显示统计信息"""
    console.print(f"[bold blue]会议统计信息[/bold blue]")
    
    try:
        stats = storage.get_statistics()
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("统计项")
        table.add_column("数值")
        
        table.add_row("总会议数", str(stats['total_conferences']))
        table.add_row("即将举行的会议", str(stats['upcoming_conferences']))
        table.add_row("按地区分类", "")
        for region, count in stats['by_region'].items():
            table.add_row(f"  - {region}", str(count))
            
        table.add_row("按主题分类", "")
        for topic, count in stats['by_topic'].items():
            table.add_row(f"  - {topic}", str(count))
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]获取统计信息过程中发生错误: {str(e)}[/bold red]")


@cli.command()
@click.option('--test', '-t', is_flag=True, help='发送测试通知')
def notify(test):
    """手动触发通知推送"""
    if test:
        console.print(f"[bold blue]发送测试通知...[/bold blue]")
        notification.send_test_notification()
        return
        
    console.print(f"[bold blue]生成并发送会议简报...[/bold blue]")
    
    try:
        # 获取最新会议
        latest_conferences = storage.get_latest_conferences(limit=5)
        
        # 获取即将开始的会议
        upcoming_conferences = storage.get_upcoming_conferences(limit=5)
        
        # 获取推荐会议
        recommended_conferences = recommender.get_recommendations(limit=5)
        
        # 发送通知
        notification.send_daily_digest(
            latest_conferences=latest_conferences,
            upcoming_conferences=upcoming_conferences,
            recommended_conferences=recommended_conferences
        )
        
        console.print(f"[green]会议简报已发送[/green]")
        
    except Exception as e:
        console.print(f"[bold red]发送通知过程中发生错误: {str(e)}[/bold red]")


if __name__ == '__main__':
    cli()