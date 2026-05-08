#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MedTech Conference CLI 使用示例
"""

import logging
from medtech_cli.config import Config
from medtech_cli.storage import StorageManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        logger.info("MedTech Conference CLI 使用示例")
        
        # 初始化配置
        config = Config()
        
        # 初始化存储管理器
        storage = StorageManager(config)
        
        # 显示统计信息
        stats = storage.get_statistics()
        print(f"总会议数: {stats['total_conferences']}")
        print(f"即将举行的会议: {stats['upcoming_conferences']}")
        
        logger.info("示例运行完成")
        
    except Exception as e:
        logger.error(f"程序运行出错: {e}")


if __name__ == "__main__":
    main()