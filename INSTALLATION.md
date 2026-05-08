# 安装和使用说明

## 安装步骤

### 1. 克隆或下载项目

首先，确保您已经有了项目文件。如果是通过压缩包下载的，请先解压。

### 2. 安装依赖

在安装工具之前，需要先安装项目依赖。请在项目根目录下执行以下命令：

```bash
# 确保您在项目根目录下
cd /home/user/vibecoding/workspace/medtech-conference-cli

# 安装依赖
pip install -r requirements.txt
```

### 3. 安装工具

依赖安装完成后，可以安装CLI工具：

```bash
# 在项目根目录下执行
pip install -e .
```

这将以开发模式安装工具，这样您对代码的任何修改都会立即生效，无需重新安装。

## 使用方法

### 基本命令

安装完成后，您可以使用以下命令来使用工具：

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

### 运行示例

您可以运行示例脚本来快速了解工具的功能：

```bash
# 在项目根目录下执行
python example_usage.py
```

### 常见问题解决

#### 问题：找不到 requirements.txt 文件

错误信息：`ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'`

解决方案：确保您在正确的目录下执行命令。请先切换到项目根目录：

```bash
cd /home/user/vibecoding/workspace/medtech-conference-cli
pip install -r requirements.txt
```

#### 问题：命令 `medtech-cli` 找不到

错误信息：`command not found: medtech-cli`

解决方案：这可能是因为安装没有成功，或者安装后的路径没有添加到系统PATH中。请尝试重新安装：

```bash
cd /home/user/vibecoding/workspace/medtech-conference-cli
pip install -e .
```

如果仍然有问题，可以尝试使用完整路径运行：

```bash
python -m medtech_cli.main --help
```

#### 问题：缺少数据库文件

错误信息：与数据库相关的错误

解决方案：工具会自动创建数据库文件，无需手动创建。请确保您有足够的权限在用户目录下创建文件。

## 配置说明

工具的配置文件存储在用户目录下的 `.medtech_cli` 文件夹中：

```
~/.medtech_cli/config.json
~/.medtech_cli/medtech.db
```

您可以通过 `medtech-cli config` 命令来修改配置，也可以直接编辑配置文件。

## 开发说明

如果您想参与开发或修改代码，可以按照以下步骤进行：

1. 确保您已经安装了所有开发依赖：

```bash
pip install -r requirements.txt
```

2. 修改代码后，可以直接运行来测试更改：

```bash
python -m medtech_cli.main [命令]
```

3. 如果您修改了入口点或添加了新的依赖，请更新 `setup.py` 文件。