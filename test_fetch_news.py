from FetchSinaNewsDataMCP import NewsDataCollector
from FetchPaperNewsDataMCP import PaperNewsDataCollector
import json
import logging
import asyncio

# 确保日志配置生效
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)

async def test_fetch_news():
    #collector = NewsDataCollector()
    collector = PaperNewsDataCollector()
    
    # 测试用例1: 搜索公司新闻
    print("测试1: 搜索工商银行相关新闻")
    try:
        result = await collector.fetch_news(company="工商银行", days=1, max_results=50)
        print(f"结果类型: {type(result)}")
        print(f"新闻数量: {len(result)}")
        
        if result:
            print("第一条新闻:")
            print(json.dumps(result[0], ensure_ascii=False, indent=2))
            print("测试1通过\n")
        else:
            print("未获取到新闻数据")
            print("测试1失败\n")
    except Exception as e:
        print(f"错误: {e}")
        print("测试1失败\n")
    
    # 测试用例2: 搜索行业新闻
    print("测试2: 搜索财经政策相关新闻")
    try:
        result = await collector.fetch_news(industry="财经政策", days=1, max_results=5)
        print(f"结果类型: {type(result)}")
        print(f"新闻数量: {len(result)}")
        
        if result:
            print("第一条新闻:")
            print(json.dumps(result[0], ensure_ascii=False, indent=2))
            print("测试2通过\n")
        else:
            print("未获取到新闻数据")
            print("测试2失败\n")
    except Exception as e:
        print(f"错误: {e}")
        print("测试2失败\n")
    
    # 测试用例3: 错误情况 - 无参数
    print("测试3: 不提供公司或行业参数")
    try:
        result = await collector.fetch_news(days=1, max_results=5)
        print("测试3失败 - 应该抛出异常\n")
    except ValueError as e:
        print(f"正确捕获错误: {e}")
        print("测试3通过\n")
    except Exception as e:
        print(f"意外错误: {e}")
        print("测试3失败\n")

if __name__ == "__main__":
    asyncio.run(test_fetch_news())