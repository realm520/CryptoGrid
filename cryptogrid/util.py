import random

def generate_random_price(current_price):
    """
    生成一个随机价格
    """
    return current_price * (1 + random.uniform(-0.001, 0.001))

def format_price(price, precision=2):
    """
    格式化价格
    """
    return f"{price:.{precision}f}"


