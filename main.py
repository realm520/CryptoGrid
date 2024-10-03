from cryptogrid.strategy import GridTradingStrategy
import os
from dotenv import load_dotenv
from rich.live import Live
import time
import ccxt
from cryptogrid.mock_exchange import MockExchange
from cryptogrid.util import format_price
from cryptogrid.logger_config import setup_logger, logger
from cryptogrid.ui_components import (
    create_strategy_params_panel, create_capital_status_panel,
    create_market_depth_panel, create_grid_status_panel,
    create_order_status_panel, create_layout, create_log_panel
)

# 策略参数
def init_strategy_params():
    # 加载.env文件中的环境变量
    load_dotenv()

    # 从环境变量中读取策略参数
    GRID_SIZE = float(os.getenv('GRID_SIZE', 0.01))  # 网格大小，默认值为0.01 (1%)
    GRID_COUNT = int(os.getenv('GRID_COUNT', 10))  # 网格数量，默认值为10
    INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', 10000))  # 初始资金，默认值为10000
    MAX_LOSS = float(os.getenv('MAX_LOSS', 0.2))  # 最大允许损失比例，默认值为20%
    POSITION_AMOUNT = float(os.getenv('POSITION_AMOUNT', 100))  # 每个档位的资金数量，默认值为100
    EXCHANGE = os.getenv('EXCHANGE', "binance")  # 交易所，默认值为binance
    SYMBOL = os.getenv('SYMBOL', "BTCUSDT")  # 交易对，默认值为BTCUSDT

    return {
        "grid_size": GRID_SIZE,
        "grid_count": GRID_COUNT,
        "initial_capital": INITIAL_CAPITAL,
        "max_loss": MAX_LOSS,
        "position_amount": POSITION_AMOUNT,
        "exchange": EXCHANGE,
        "symbol": SYMBOL
    }

def main():
    strategy_params = init_strategy_params()
    # exchange = getattr(ccxt, strategy_params["exchange"])()
    exchange = MockExchange(initial_price=10000, volatility=0.005)
    current_price = exchange.fetch_ticker(strategy_params["symbol"])["last"]
    
    # 设置日志
    panel_handler = setup_logger()
    
    strategy = GridTradingStrategy(
        exchange=exchange,
        symbol=strategy_params["symbol"],
        initial_price=current_price,
        grid_size=strategy_params["grid_size"],
        grid_levels=strategy_params["grid_count"],
        initial_capital=strategy_params["initial_capital"],
        position_amount=strategy_params["position_amount"],
        max_loss=strategy_params["max_loss"]
    )
    
    layout = create_layout()
    
    with Live(layout, refresh_per_second=1, screen=True):
        while True:
            # 更新市场深度数据
            market_depth = exchange.fetch_order_book(strategy_params["symbol"], limit=5)
            current_price = market_depth["bids"][0][0]
            
            # 更新策略状态
            strategy.handle_price_change(current_price)
            
            # 使用logger记录日志
            logger.info(f"当前价格: {current_price:.2f}, 总资产: {strategy.total_assets:.2f}")
            
            # 更新界面
            layout["params"].update(create_strategy_params_panel(strategy_params))
            layout["capital_status"].update(create_capital_status_panel(strategy))
            layout["market_depth"].update(create_market_depth_panel(market_depth))
            layout["grid_status"].update(create_grid_status_panel(strategy))
            layout["order_status"].update(create_order_status_panel(strategy))
            layout["log"].update(create_log_panel(panel_handler))
            
            time.sleep(1)

if __name__ == "__main__":
    main()