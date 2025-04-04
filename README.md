# HNU_gym-automatic-reservation

# HNU体育馆自动预约系统

这是一个用于湖南大学体育馆自动预约的Python脚本。该脚本可以自动在指定时间进行体育馆场地预约，支持同时预约多个时段。

## 功能特点

- 自动登录湖南大学统一认证系统
- 支持预约1-2个时段
- 自动等待到预约时间点
- 预约失败自动重试
- 支持配置文件方式运行
- 支持命令行参数方式运行

## 准备工作
### 1. Python环境要求

- Python 3.6或更高版本

- 可以通过以下命令检查Python版本：

```bash
python  --version
```
### 2. 安装依赖

```bash
pip install requests
```

### 3. 配置文件设置

在项目根目录创建 `config.json` 文件，内容如下：

```json
{
    "username": "你的学号",
    "password": "你的密码",
    "resource_id": "场馆资源ID",
    "slots": 1,
    "date": "2025-05-05",
    "period1": "时间段1ID",
    "sub_resource_id1": "台号1ID",
    "period2": "时间段2ID",
    "sub_resource_id2": "台号2ID"
}
```

### 4. 场馆信息

在 `场馆resource_id，period,sub_resource_id.xlsx` 文件中可以找到：
- 各场馆的resource_id
- 各时间段对应的period
- 各台号对应的sub_resource_id

## 使用方法

### 方式一：使用配置文件（推荐）

1. 编辑 `config.json` 文件，填入必要信息
2. 运行脚本：
```bash
python try.py
```

### 方式二：命令行参数

```bash
python try.py --username "学号" --password "密码" --resource_id "资源id" --period1 "时间段1" --sub_resource_id1 "台号1" --slots 1 --date "2024-05-20"
```
可设置程序启动时间：
```bash
python try.py --time "2025-05-20 13:14:00"
```

参数说明：
- `--username`: 学号
- `--password`: 密码
- `--resource_id`: 场馆资源ID
- `--slots`: 预约时段数（1或2）
- `--date`: 预约日期（格式：YYYY-MM-DD）
- `--period1`: 第一个时间段ID
- `--sub_resource_id1`: 第一个台号ID
- `--period2`: 第二个时间段ID（当slots=2时使用）
- `--sub_resource_id2`: 第二个台号ID（当slots=2时使用）
