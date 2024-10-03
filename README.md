# CryptoGrid

CryptoGrid是一个基于Python的加密货币网格交易策略实现。它使用网格交易算法在加密货币市场中自动执行买入和卖出操作,旨在从市场波动中获利。

## 功能特点

- 自动化网格交易策略
- 实时市场数据监控
- 动态订单管理
- 盈亏实时计算
- 交易历史记录
- 可视化界面展示交易状态

## 安装

1. 克隆仓库:

git clone https://github.com/yourusername/cryptogrid.git
cd cryptogrid

2. 安装依赖:

pip install poetry
poetry install

## 配置

1. 复制`.env.example`文件并重命名为`.env`
2. 在`.env`文件中填写您的交易所API密钥和其他配置参数

## 使用方法

运行主程序:

poetry run python main.py

## 项目结构

- `main.py`: 主程序入口
- `cryptogrid/`: 核心策略和功能模块
  - `strategy.py`: 网格交易策略实现
  - `mock_exchange.py`: 模拟交易所接口
  - `ui_components.py`: 用户界面组件
  - `util.py`: 工具函数
- `tests/`: 测试文件目录

## 依赖项

- Python 3.12+
- ccxt
- rich
- loguru
- python-dotenv

## 注意事项

- 本项目仅用于教育和研究目的,请勿在实际交易中使用
- 使用真实资金进行交易前,请充分了解相关风险

## 贡献

欢迎提交问题和拉取请求。对于重大更改,请先开issue讨论您想要改变的内容。

## 许可证

本项目采用MIT许可证 - 详情请见 [LICENSE](LICENSE) 文件
