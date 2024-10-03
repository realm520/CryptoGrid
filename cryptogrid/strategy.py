from loguru import logger
from cryptogrid.util import format_price
import json
from datetime import datetime

class GridLevel:
    def __init__(self, price):
        self.price = price  # 档位价格
        self.reset()

    def reset(self):
        self.amount = 0  # 档位数量
        self.buy_order = None  # 买入订单ID
        self.buy_executed_price = 0  # 买入成交价
        self.buy_order_status = "未下单"  # 买入订单状态
        self.sell_order = None  # 卖出订单ID
        self.sell_executed_price = 0  # 卖出成交价
        self.sell_order_status = "未下单"  # 卖出订单状态

    def __str__(self):
        return f"价格: {self.price}, 数量: {self.amount}, 买入状态: {self.buy_order_status}, 卖出状态: {self.sell_order_status}"

class Order:
    def __init__(self, order_id, price, amount, direction):
        self.order_id = order_id
        self.price = price
        self.amount = amount
        self.direction = direction
        self.status = "已下单"

    def __str__(self):
        return f"订单ID: {self.order_id}, 价格: {self.price}, 数量: {self.amount}, 状态: {self.status}"



class GridTradingStrategy:
    def __init__(self, exchange, symbol, initial_price: float, grid_size: float, grid_levels: int,
                 position_amount: float, initial_capital: float,
                 max_loss: float):
        """
        初始化策略
        :param initial_price: 初始价格
        :param grid_size: 每档的价格百分比变化，例如 0.01 表示 1% 的价格波动
        :param grid_levels: 网格档位的数量（向上和向下的档位数）
        :param position_amount: 每个档位的资金数量，例如 100 USDT
        :param initial_capital: 初始资金
        :param max_loss: 最大亏损
        """
        self.initial_price = initial_price
        self.grid_size = grid_size
        self.grid_price = initial_price * grid_size
        self.position_amount = position_amount
        self.initial_capital = initial_capital
        self.max_loss = max_loss
        self.total_assets = initial_capital
        self.capital = initial_capital
        self.position = 0
        self.pnl = 0
        self.pnl_rate = 0
        self.current_price = initial_price
        self.history_orders = []
        # 生成价格网格数组
        self.grid = self.generate_grid(initial_price, grid_size, grid_levels)

        # 使用 GridLevel 对象来追踪每个档位
        self.grid_levels = {price: GridLevel(price) for price in self.grid}

        # 初始化ccxt交易所
        self.exchange = exchange
        self.symbol = symbol

    def generate_grid(self, initial_price, grid_size, levels):
        """
        生成价格网格数组
        :param initial_price: 初始价格
        :param grid_size: 每档的百分比
        :param levels: 向上和向下的档位数
        :return: 返回一个价格列表，按价格排序
        """
        grid = []
        last_grid_price = initial_price
        grid.append(last_grid_price)
        for i in range(levels - 1):
            grid_price = last_grid_price * (1 - grid_size)
            last_grid_price = grid_price
            grid.append(grid_price)
        last_grid_price = initial_price
        for i in range(levels - 1):
            grid_price = last_grid_price * (1 + grid_size)
            last_grid_price = grid_price
            grid.append(grid_price)
        return sorted(grid, reverse=True)

    def handle_price_change(self, current_price):
        """
        处理当前价格变化的逻辑
        :param current_price: 当前市场价格
        """
        self.current_price = current_price

        # 检查所有档位上的订单
        # 检查下方N档内没有买单时，补上买单
        count = 5
        for price in self.grid:
            level = self.grid_levels[price]
            self.check_order_status(level)
            self.update_pnl(current_price)
            # 如果买单成交了，挂上卖单
            if level.buy_order_status == "filled":
                if level.sell_order_status == "未下单":
                    self.place_sell_order(level)

            # 如果当前价格小于网格价格，则检查买单
            if price < current_price:
                if count > 0:  # N档以内
                    if level.buy_order_status == "未下单":  # 如果未下单，则挂买单
                        self.place_buy_order(level)
                elif level.buy_order_status == "open":    # 如果超出当前价N档以上的买单未成交，则撤单并初始化该档位
                    self.cancel_order(level)
                count -= 1

    def place_buy_order(self, level):
        """
        使用ccxt下买单
        """
        try:
            order = self.exchange.create_limit_buy_order(
                self.symbol,
                self.position_amount / level.price,
                level.price
            )
            level.buy_order_status = "pending"
            level.buy_order = order['id']
            logger.info(f"在 {level.price} 价格处下买单，金额为 {self.position_amount} USDT, 订单状态: {level.buy_order_status}, 订单ID: {level.buy_order}")
        except Exception as e:
            logger.error(f"下买单失败: {str(e)}")

    def place_sell_order(self, level):
        """
        使用ccxt下卖单
        """
        sell_price = level.price + self.grid_price
        try:
            order = self.exchange.create_limit_sell_order(
                self.symbol,
                self.position_amount / sell_price,
                format_price(sell_price)
            )
            level.sell_order_status = "pending"
            level.sell_order = order['id']
            logger.info(f"在 {sell_price} 价格处下卖单，金额为 {self.position_amount} USDT, 订单状态: {level.sell_order_status}, 订单ID: {level.sell_order}")
        except Exception as e:
            logger.error(f"下卖单失败: {str(e)}")

    def cancel_order(self, level):
        """
        使用ccxt撤销订单
        """
        try:
            if level.buy_order:
                self.exchange.cancel_order(level.buy_order, self.symbol)
                logger.info(f"撤销在 {level.price} 价格处的买单")
                level.buy_order_status = "closing"
            if level.sell_order:
                self.exchange.cancel_order(level.sell_order, self.symbol)
                logger.info(f"撤销在 {level.price} 价格处的卖单")
                level.sell_order_status = "closing"
        except Exception as e:
            logger.error(f"撤单失败: {str(e)}")

    def check_order_status(self, level):
        """
        使用ccxt检查订单状态
        """ 
        logger.info(f"检查在 {level.price} 价格处的买单，订单ID: {level.buy_order}")
        logger.info(f"检查在 {level.price} 价格处的卖单，订单ID: {level.sell_order}")
        try:
            # 获取订单状态
            if level.buy_order:
                order = self.exchange.fetch_order(level.buy_order, self.symbol)
                level.buy_order_status = order['status']
                if level.buy_order_status == 'filled':
                    self.capital -= self.position_amount
                    self.position += self.position_amount / level.price
                    self.history_orders.append(order)
            if level.sell_order:
                order = self.exchange.fetch_order(level.sell_order, self.symbol)
                level.sell_order_status = order['status']
                if level.sell_order_status == 'filled':
                    self.capital += self.position_amount
                    self.position -= self.position_amount / level.price
                    self.history_orders.append(order)

            # 如果两个订单都成交了，则重置该档位并保存历史订单
            if level.buy_order_status == 'filled' and level.sell_order_status == 'filled':
                level.reset()
                self.save_history_orders()  # 在这里调用保存方法

            # 处理撤单
            if level.buy_order_status == 'closed':
                if level.sell_order_status != '未下单':
                    logger.warning(f"在 {level.price} 价格处的买单已撤单，但卖单状态不对:{level.sell_order_status}")
                level.reset()
        except Exception as e:
            logger.error(f"检查订单状态失败: {str(e)}")

    def update_pnl(self, price):
        """
        更新盈亏
        """
        self.total_assets = self.capital + self.position * price
        self.pnl = self.total_assets - self.initial_capital
        self.pnl_rate = self.pnl / self.initial_capital

    
    def get_summary(self):
        """
        获取策略的总结信息
        :return: 返回一个包含总资产、资金、持仓数量和盈亏的摘要
        """
        total_assets = self.total_assets
        capital = self.capital
        position = self.position
        pnl = self.pnl
        return {
            "total_assets": total_assets,
            "capital": capital,
            "position": position,
            "pnl": pnl
        }

    def save_history_orders(self):
        """
        将history_orders保存到文件中
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"history_orders_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.history_orders, f, indent=4, default=str)
            logger.info(f"历史订单已保存到文件: {filename}")
        except Exception as e:
            logger.error(f"保存历史订单到文件时出错: {str(e)}")