# MedTech Conference CLI

一个命令行工具，用于自动收集、筛选、推送和管理全球医疗科技领域的会议信息，帮助团队高效选择和参与相关会议。

## 功能特点

- **全球会议信息采集**：自动从大陆、香港、美国、新加坡、日本、印尼等地区的主要会议平台收集会议信息
- **智能筛选与分类**：基于关键词（HomeCare、AI、web3、RPM、远程医疗等）自动筛选和分类相关会议
- **个性化推荐**：根据团队成员的兴趣和历史参与记录，智能推荐最相关的会议
- **每日推送**：定时生成会议简报，通过多种渠道推送给团队成员
- **会议管理**：记录团队成员对会议的兴趣度、报名状态和参与情况

## 安装

### 从源码安装

```bash
git clone https://github.com/yourusername/medtech-conference-cli.git
cd medtech-conference-cli
pip install -e .
```

### 依赖安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本命令

```bash
# 查看帮助信息
medtech-cli --help

# 列出即将举行的会议
medtech-cli list upcoming

# 按地区筛选会议
medtech-cli list by-region china

# 按主题筛选会议
medtech-cli list by-topic ai

# 显示推荐会议
medtech-cli recommend

# 手动触发数据采集
medtech-cli crawl

# 配置工具参数
medtech-cli config
```

### 配置

首次使用时，需要进行基本配置：

```bash
# 设置关注的关键词
medtech-cli config keywords --add "HomeCare, AI, 远程医疗"

# 设置关注的地区
medtech-cli config regions --add "china, hongkong, us, singapore, japan, indonesia"

# 设置推送时间
medtech-cli config schedule --time "09:00"
```

### 每日推送

工具会在配置的时间自动生成会议简报并推送给团队成员。推送内容包括：

- 最新收集的相关会议
- 即将开始的会议提醒
- 基于团队兴趣的推荐会议

## 项目结构

```
medtech-conference-cli/
├── medtech_cli/
│   ├── __init__.py
│   ├── main.py            # CLI入口
│   ├── config.py          # 配置管理
│   ├── crawlers/          # 数据采集模块
│   ├── processors/        # 数据处理模块
│   ├── recommender/       # 推荐引擎模块
│   ├── ui/                # 用户交互模块
│   ├── notification/      # 通知推送模块
│   └── storage/           # 数据存储模块
├── setup.py
├── requirements.txt
└── README.md
```

## 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，请通过以下方式联系我：

- 邮箱：yangzehui994@gmail.com
