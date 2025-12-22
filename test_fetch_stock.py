from FetchStockerDataMCP import StockerDataCollector
import json
import logging

# 确保日志配置生效
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)

def test_fetch_stock_data():
    collector = StockerDataCollector()
    
    # 测试用例1: 正常情况
    print("测试1: 获取农业银行股票数据")
    result = collector.fetch_stock_data("农业银行", 30)
    print(f"结果类型: {type(result)}")
    if "error" not in result:
        print(f"公司名称: {result['metadata']['company_name']}")
        print(f"股票代码: {result['metadata']['symbol']}")
        print(f"数据天数: {result['metadata']['data_days']}")
        print("完整结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("测试1通过\n")
    else:
        print(f"错误: {result['error']}")
        print("测试1失败\n")
    
    # 测试用例2: 错误情况
    print("测试2: 查询不存在的公司")
    result = collector.fetch_stock_data("不存在的公司", 5)
    if "error" in result:
        print(f"正确捕获错误: {result['error']}")
        print("测试2通过\n")
    else:
        print("测试2失败\n")

if __name__ == "__main__":
    test_fetch_stock_data()