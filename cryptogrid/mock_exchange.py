import random
from loguru import logger



class MockExchange:
    def __init__(self, initial_price, volatility=0.005):
        self.price = initial_price
        self.volatility = volatility
        self.orders = []
        self.balance = {'USDT': 10000, 'BTC': 0}

    def fetch_ticker(self, symbol):
        self._update_price()
        return {"last": self.price}

    def fetch_order_book(self, symbol, limit=5):
        self._update_price()
        spread = self.price * 0.001  # 0.1% 价差
        return {
            "bids": [[self.price - spread, 1]] * limit,
            "asks": [[self.price + spread, 1]] * limit
        }

    def create_limit_buy_order(self, symbol, amount, price):
        cost = amount * price
        if self.balance['USDT'] >= cost:
            self.balance['USDT'] -= cost
            order = {
                "id": len(self.orders) + 1,
                "amount": amount,
                "cost": cost,
                "price": price,
                "side": "buy",
                "status": "open"
            }
            self.orders.append(order)
            return order
        else:
            raise Exception("余额不足")

    def create_limit_sell_order(self, symbol, amount, price):
        if self.balance['BTC'] >= amount:
            logger.info(f"创建卖单: {amount} BTC, 价格: {price}, type price: {type(price)}, type(amount): {type(amount)}")
            cost = amount * float(price)
            self.balance['BTC'] -= amount
            order = {
                "id": len(self.orders) + 1,
                "amount": amount,
                "cost": cost,
                "price": price,
                "side": "sell",
                "status": "open"
            }
            self.orders.append(order)
            return order
        else:
            raise Exception("余额不足")

    def cancel_order(self, order_id, symbol):
        for order in self.orders:
            if order["id"] == order_id:
                order["status"] = "closed"
                break
        else:
            raise Exception("订单不存在")

    def fetch_order(self, order_id, symbol):
        for order in self.orders:
            if order["id"] == order_id:
                if order["status"] == "open" and order["side"] == "buy" and float(order["price"]) >= self.price:
                    order["status"] = "filled"
                    self.balance['BTC'] += order["amount"]
                elif order["status"] == "open" and order["side"] == "sell" and float(order["price"]) <= self.price:
                    order["status"] = "filled"
                    self.balance['USDT'] += order["cost"]
                return order
        else:
            raise Exception("订单不存在")

    def _update_price(self):
        change = random.uniform(-self.volatility, self.volatility)
        self.price *= (1 + change)
    

# 使用示例
# mock_exchange = MockExchange(initial_price=30000)
# print(mock_exchange.fetch_ticker("BTC/USDT"))
# print(mock_exchange.create_market_buy_order("BTC/USDT", 0.1))
