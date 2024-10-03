from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.live import Live

# 创建日志面板
def create_log_panel(panel_handler):
    log_text = Text()
    # 只获取最新的10条日志，并反转顺序
    latest_logs = list(panel_handler.logs)[-10:][::-1]
    
    for i, log in enumerate(latest_logs):
        if i == 0:  # 最新的日志
            log_text.append(log + "\n", style="bold yellow")
        else:
            log_text.append(log + "\n")
    
    return Panel(log_text, title="最新日志", border_style="bold")

# 创建策略参数面板
def create_strategy_params_panel(strategy_params):
    table = Table(show_header=False, expand=True)
    table.add_column("参数名称", style="cyan")
    table.add_column("参数值", style="magenta")
    
    for key, value in strategy_params.items():
        if isinstance(value, float) and key not in ['grid_size']:
            table.add_row(key, f"{value:.2%}")
        else:
            table.add_row(key, str(value))
    
    return Panel(table, title="策略参数", border_style="bold")

# 创建资金状态面板
def create_capital_status_panel(strategy):
    table = Table(show_header=False, expand=True)
    table.add_column("项目", style="cyan", justify="center")
    table.add_column("数值", style="magenta", justify="center")
    
    table.add_row("初始资金", f"{strategy.initial_capital:.2f}")
    table.add_row("当前资金", f"{strategy.capital:.2f}")
    table.add_row("持仓数量", f"{strategy.position:.4f}")
    table.add_row("总资产", f"{strategy.total_assets:.2f}")
    table.add_row("盈亏", f"{strategy.pnl:.2f}")
    table.add_row("盈亏率", f"{strategy.pnl_rate:.2%}")
    
    return Panel(table, title="资金情况", border_style="bold")

# 创建市场深度面板
def create_market_depth_panel(market_depth):
    table = Table(expand=True)
    table.add_column("买入", style="green")
    table.add_column("卖出", style="red")
    
    for i in range(5):
        table.add_row(f"{market_depth['bids'][i][0]} ({market_depth['bids'][i][1]})",
                      f"{market_depth['asks'][i][0]} ({market_depth['asks'][i][1]})")
    
    return Panel(table, title="市场深度", border_style="bold")

# 创建网格状态面板
def create_grid_status_panel(strategy):
    table = Table(expand=True)
    table.add_column("价格", style="cyan")
    table.add_column("买单状态", style="magenta")
    table.add_column("买单ID", style="green")
    table.add_column("卖单状态", style="magenta")
    table.add_column("卖单ID", style="green")
    for price in strategy.grid:
        level = strategy.grid_levels[price]
        table.add_row(f"{price:.2f}", level.buy_order_status, str(level.buy_order), level.sell_order_status, str(level.sell_order))
    
    return Panel(table, title="网格状态", border_style="bold")

# 创建订单状态面板
def create_order_status_panel(strategy):
    table = Table(expand=True)
    table.add_column("订单ID", style="cyan")
    table.add_column("类型", style="magenta")
    table.add_column("价格", style="yellow")
    table.add_column("数量", style="green")
    table.add_column("状态", style="magenta")
    
    # 使用集合来跟踪已添加的订单ID
    added_order_ids = set()
    
    for order in reversed(strategy.history_orders):  # 反转列表以显示最新的订单
        order_id = str(order['id'])
        if order_id not in added_order_ids:
            if order['side'] == 'buy':
                table.add_row(order_id, "买入", f"{order['price']}", 
                              f"{order['amount']:.4f}", order['status'])
            elif order['side'] == 'sell':
                table.add_row(order_id, "卖出", f"{order['price']}", 
                              f"{order['amount']:.4f}", order['status'])
            added_order_ids.add(order_id)
    
    return Panel(table, title="订单状态", border_style="bold")

# 创建布局
def create_layout():
    layout = Layout()
    
    layout.split_column(
        Layout(name="upper", ratio=1),
        Layout(name="middle", ratio=2),
        Layout(name="log", ratio=1)
    )
    
    layout["upper"].split_row(
        Layout(name="params"),
        Layout(name="capital_status"),
        Layout(name="market_depth")
    )
    
    layout["middle"].split_row(
        Layout(name="grid_status"),
        Layout(name="order_status")
    )
    
    return layout

# 添加新的函数来创建Live对象
def create_live_display(layout):
    return Live(
        layout,
        refresh_per_second=4,  # 每秒刷新4次
        screen=True,  # 使用备用屏幕缓冲区
        auto_refresh=False  # 禁用自动刷新，我们将手动控制刷新
    )
