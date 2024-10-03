import pytest
from cryptogrid.util import generate_random_price, format_price

def test_generate_random_price():
    # 测试生成的随机价格是否在预期范围内
    current_price = 100.0
    for _ in range(1000):  # 多次测试以确保结果的随机性
        new_price = generate_random_price(current_price)
        assert current_price * 0.999 <= new_price <= current_price * 1.001

@pytest.mark.parametrize("input_price, precision, expected_output", [
    (123.456, None, "123.46"),
    (123.456, 3, "123.456"),
    (123.4, 0, "123"),
    (123.456, 1, "123.5"),
    (123.456, 2, "123.46"),
    (123.456, 4, "123.4560"),
    (123.456, 5, "123.45600"),
    (0.0001, 4, "0.0001"),
    (0.0001, 3, "0.000"),
    (9999.9999, 2, "10000.00"),
    (1.23456789, 6, "1.234568"),
    (0.000001, 7, "0.0000010"),
    (1000000, 0, "1000000"),
    (0.1, 1, "0.1"),
    (0.01, 2, "0.01"),
    (0.001, 3, "0.001"),
    (1234567.89, 1, "1234567.9"),
    (0.00000001, 8, "0.00000001"),
    (999999.999999, 4, "1000000.0000"),
])
def test_format_price(input_price, precision, expected_output):
    # 测试价格格式化函数
    if precision is None:
        assert format_price(input_price) == expected_output
    else:
        assert format_price(input_price, precision=precision) == expected_output
