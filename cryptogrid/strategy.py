from loguru import logger
from cryptogrid.util import format_price
import json
from datetime import datetime

class GridLevel:
    def __init__(self, price):
        self.price = price  # 档位价格
        self.reset()

    def reset(self):
        self.buy_order_status = "未下单"
        self.sell_order_status = "未下单"
        self.amount = 0  # 档位数量
        self.buy_order = None  # 买入订单ID
        self.buy_executed_price = 0  # 买入成交价
        self.sell_order = None  # 卖出订单ID
        self.sell_executed_price = 0  # 卖出成交价

    def save_completed_trade(self):
        # 创建要保存的记录
        completed_trade = {
            "price": self.price,
            "buy_executed_price": self.buy_executed_price,
            "sell_executed_price": self.sell_executed_price,
            "amount": self.amount,
            "timestamp": datetime.now().isoformat()
        }
        
        # 将记录追加到文件中
        try:
            with open("completed_trades.json", "a+") as f:
                f.seek(0)  # 移动到文件开头
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
                
                existing_data.append(completed_trade)
                
                f.seek(0)  # 移动到文件开头
                f.truncate()  # 清空文件内容
                json.dump(existing_data, f, indent=4)
            
            logger.info(f"成功记录完成的交易: {completed_trade}")
        except Exception as e:
            logger.error(f"记录完成的交易时出错: {str(e)}")
 
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
    def __init__(self, exchange, symbol, load_from_file: bool = False):
        """
        初始化策略
        :param exchange: 交易所对象
        :param symbol: 交易对
        :param load_from_file: 是否从文件加载策略状态
        """
        self.exchange = exchange
        self.symbol = symbol

        if load_from_file:
            self.load_strategy_state()
        else:
            self.reset_strategy()

    def reset_strategy(self):
        """
        重置策略参数为初始状态
        """
        self.initial_price = 0
        self.grid_size = 0
        self.grid_price = 0
        self.position_amount = 0
        self.initial_capital = 0
        self.max_loss = 0
        self.total_assets = 0
        self.capital = 0
        self.position = 0
        self.pnl = 0
        self.pnl_rate = 0
        self.current_price = 0
        self.history_orders = []
        self.grid = []
        self.grid_levels = {}

    def set_strategy_params(self, initial_price: float, grid_size: float, grid_levels: int,
                            position_amount: float, initial_capital: float, max_loss: float):
        """
        设置策略参数
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
        self.current_price = initial_price

        # 生成价格网格数组
        self.grid = self.generate_grid(initial_price, grid_size, grid_levels)
        # 使用 GridLevel 对象来追踪每个档位
        self.grid_levels = {price: GridLevel(price) for price in self.grid}
        self.save_strategy_state()

    def save_strategy_state(self, filename='strategy_state.json'):
        """
        保存策略参数和状态到JSON文件
        """
        state = {
            'initial_price': self.initial_price,
            'grid_size': self.grid_size,
            'grid_price': self.grid_price,
            'position_amount': self.position_amount,
            'initial_capital': self.initial_capital,
            'max_loss': self.max_loss,
            'total_assets': self.total_assets,
            'capital': self.capital,
            'position': self.position,
            'pnl': self.pnl,
            'pnl_rate': self.pnl_rate,
            'current_price': self.current_price,
            'grid': self.grid,
            'grid_levels': {price: level.__dict__ for price, level in self.grid_levels.items()},
            'symbol': self.symbol
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=4)
        
        logger.info(f"策略状态已保存到 {filename}")

    def load_strategy_state(self, filename='strategy_state.json'):
        """
        从JSON文件加载策略参数和状态
        """
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            
            # 恢复策略参数和状态
            self.initial_price = state['initial_price']
            self.grid_size = state['grid_size']
            self.grid_price = state['grid_price']
            self.position_amount = state['position_amount']
            self.initial_capital = state['initial_capital']
            self.max_loss = state['max_loss']
            self.total_assets = state['total_assets']
            self.capital = state['capital']
            self.position = state['position']
            self.pnl = state['pnl']
            self.pnl_rate = state['pnl_rate']
            self.current_price = state['current_price']
            self.grid = state['grid']
            self.symbol = state['symbol']
            
            # 恢复网格级别状态
            self.grid_levels = {float(price): GridLevel(float(price)) for price in state['grid_levels']}
            for price, level_data in state['grid_levels'].items():
                self.grid_levels[float(price)].__dict__.update(level_data)
            
            logger.info(f"策略状态已从 {filename} 加载")
        except FileNotFoundError:
            logger.warning(f"未找到状态文件 {filename}，使用初始设置")
        except json.JSONDecodeError:
            logger.error(f"无法解析状态文件 {filename}，使用初始设置")


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

    def handle_price_change(self):
        """
        处理当前价格变化的逻辑
        :param current_price: 当前市场价格
        """
        market_depth = self.exchange.fetch_order_book(self.symbol, limit=5)
        current_price = market_depth["bids"][0][0]
        self.current_price = current_price
        logger.info(f"当前价格: {current_price:.2f}, 总资产: {self.total_assets:.2f}")

        # 检查所有档位上的订单
        # 检查下方N档内没有买单时，补上买单
        count = 5
        order_changed = False
        for price in self.grid:
            level = self.grid_levels[price]
            order_changed = self.check_order_status(level)
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
        if order_changed:
            self.save_history_orders()
        self.save_strategy_state()

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
        try:
            order_changed = False
            # 获取订单状态
            if level.buy_order:
                order = self.exchange.fetch_order(level.buy_order, self.symbol)
                level.buy_order_status = order['status']
                if level.buy_order_status == 'filled':
                    self.capital -= self.position_amount
                    self.position += self.position_amount / level.price
                    self.history_orders.append(order)
                    order_changed = True
            if level.sell_order:
                order = self.exchange.fetch_order(level.sell_order, self.symbol)
                level.sell_order_status = order['status']
                if level.sell_order_status == 'filled':
                    self.capital += self.position_amount
                    self.position -= self.position_amount / level.price
                    self.history_orders.append(order)
                    order_changed = True
            if order_changed:
                self.save_history_orders()
            # 处理撤单
            if level.buy_order_status == 'closed' or (level.buy_order_status == 'filled' and level.sell_order_status == 'filled'):
                if level.sell_order_status != '未下单':
                    logger.warning(f"在 {level.price} 价格处的买单已撤单，但卖单状态不对:{level.sell_order_status}")
                level.reset()
        except Exception as e:
            logger.error(f"检查订单状态失败: {str(e)}")
        return order_changed

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
        filename = f"history_orders_{self.exchange.name}_{self.symbol}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.history_orders, f, indent=4, default=str)
            logger.info(f"历史订单已保存到文件: {filename}")
        except Exception as e:
            logger.error(f"保存历史订单到文件时出错: {str(e)}")