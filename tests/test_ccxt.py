import pytest
import ccxt

def test_fetch_order_book():
    # 初始化Binance交易所
    exchange = ccxt.binance()
    
    # 定义交易对
    symbol = 'BTC/USDT'
    
    # 获取订单簿数据,限制为5档
    order_book = exchange.fetch_order_book(symbol, limit=5)
    
    # 检查订单簿是否包含必要的键
    assert 'bids' in order_book
    assert 'asks' in order_book
    
    # 检查bids和asks是否各有5个报价
    assert len(order_book['bids']) == 5
    assert len(order_book['asks']) == 5
    
    # 检查每个报价是否包含价格和数量
    for bid in order_book['bids']:
        assert len(bid) == 2
        assert isinstance(bid[0], (int, float))  # 价格
        assert isinstance(bid[1], (int, float))  # 数量
    
    for ask in order_book['asks']:
        assert len(ask) == 2
        assert isinstance(ask[0], (int, float))  # 价格
        assert isinstance(ask[1], (int, float))  # 数量
    
    # 检查买单价格是否按降序排列
    assert all(order_book['bids'][i][0] >= order_book['bids'][i+1][0] for i in range(4))
    
    # 检查卖单价格是否按升序排列
    assert all(order_book['asks'][i][0] <= order_book['asks'][i+1][0] for i in range(4))

    print("订单簿数据:", order_book)

def test_fetch_ticker():
    # 初始化Binance交易所
    exchange = ccxt.binance()
    
    # 定义交易对
    symbol = 'BTC/USDT'
    
    # 获取ticker数据
    ticker = exchange.fetch_ticker(symbol)
    
    # 检查ticker是否包含必要的键
    assert 'last' in ticker
    assert 'bid' in ticker
    assert 'ask' in ticker
    assert 'high' in ticker
    assert 'low' in ticker
    assert 'baseVolume' in ticker
    
    # 检查最新价格是否为正数
    assert ticker['last'] > 0
    
    # 检查最新价格是否在当日最高价和最低价之间
    assert ticker['low'] <= ticker['last'] <= ticker['high']
    
    # 检查买价是否小于等于卖价
    assert ticker['bid'] <= ticker['ask']
    
    # 检查成交量是否为正数
    assert ticker['baseVolume'] > 0
    
    # 检查时间戳是否存在且为正数
    assert 'timestamp' in ticker
    assert ticker['timestamp'] > 0
    
    print(f"BTC/USDT 最新价格: {ticker['last']}")
    print(f"完整的ticker数据: {ticker}")
