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
import threading

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

def update_strategy_state_thread(strategy, stop_event):
    while not stop_event.is_set():
        strategy.handle_price_change()
        time.sleep(1)  # 每秒更新一次策略状态
    strategy.save_strategy_state()


def main():
    # 设置日志
    panel_handler = setup_logger()
    
    # 初始化策略
    strategy_params = init_strategy_params()
    exchange = MockExchange(initial_price=10000, volatility=0.005)
    strategy = GridTradingStrategy(exchange, strategy_params["symbol"])
    strategy_state_file = f"{strategy_params['exchange']}_{strategy_params['symbol']}_strategy_state.json"
    if os.path.exists(strategy_state_file):
        strategy.load_strategy_state(strategy_state_file)
    else:
        current_price = exchange.fetch_ticker(strategy_params["symbol"])["last"]
        strategy.set_strategy_params(
            initial_price=current_price,
            grid_size=strategy_params["grid_size"],
            grid_levels=strategy_params["grid_count"],
            position_amount=strategy_params["position_amount"],
            initial_capital=strategy_params["initial_capital"],
            max_loss=strategy_params["max_loss"]
        )

    # 创建停止事件和线程
    stop_event = threading.Event()
    update_thread = threading.Thread(target=update_strategy_state_thread, args=(strategy, stop_event))
    update_thread.start()

    layout = create_layout()
    try:
        with Live(layout, refresh_per_second=1, screen=True):
            while True:
                # 更新界面
                layout["params"].update(create_strategy_params_panel(strategy_params))
                layout["capital_status"].update(create_capital_status_panel(strategy))
                layout["market_depth"].update(create_market_depth_panel(strategy.exchange.fetch_order_book(strategy_params["symbol"], limit=5)))
                layout["grid_status"].update(create_grid_status_panel(strategy))
                layout["order_status"].update(create_order_status_panel(strategy))
                layout["log"].update(create_log_panel(panel_handler))
                
                time.sleep(0.1)  # 稍微降低主线程的刷新频率，减少CPU使用
    except KeyboardInterrupt:
        print("正在停止程序...")
    finally:
        # 停止更新线程
        stop_event.set()
        update_thread.join()
    

if __name__ == "__main__":
    main()