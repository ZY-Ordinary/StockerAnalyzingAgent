import akshare as ak
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
import argparse
import asyncio
import unittest
import logging
import os
from mcp.server.fastmcp import FastMCP

# Create MCP server
app = FastMCP("stock-data-fetcher")

# Set up logging
# Ensure the log directory exists
log_file_path = 'FetchStockerNewsLog.txt'
try:
    if not os.path.exists(os.path.dirname(log_file_path)):
        os.makedirs(os.path.dirname(log_file_path))
except Exception:
    # If we can't create directories, just use the file name directly
    pass

# Configure logging with both file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()  # Also print to console
    ],
    force=True  # Force reconfiguration in case logging was already configured
)

logger = logging.getLogger(__name__)
logger.info("FetchStockerDataMCP模块已加载")


class StockerDataCollector():
   
    def __init__(self):
        pass

    def fetch_stock_data(self, company_name: str, days: int = 30):
        """
        获取A股股票历史数据并格式化为标准JSON结构
        
        参数:
            company_name (str): 公司名称，如"工商银行", "贵州茅台"等
            days (int): 获取历史数据的天数范围，支持1-365天，默认30天
        
        返回:
            dict: 格式化的字典，包含以下结构:
            {
                "metadata": {
                    "company_name": "公司名称",
                    "symbol": "股票代码",
                    "market": "交易所(SH/SZ)",
                    "update_time": "数据更新时间",
                    "data_days": 实际获取天数,
                    "currency": "CNY"
                },
                "statistics": {
                    "close_price": {
                        "max": 最高收盘价,
                        "min": 最低收盘价,
                        "current": 最新收盘价,
                        "change_pct": 最新涨跌幅(%)
                    },
                    "volume": {
                        "total": 总成交量,
                        "avg": 日均成交量,
                        "latest": 最新成交量
                    }
                },
                "technical_indicators": {
                    "sma5": 5日均线值,
                    "sma20": 20日均线值,
                    "rsi14": 14日RSI值
                },
                "time_series": {
                    "dates": ["日期1", "日期2", ...],
                    "ohlc": {
                        "open": [开盘价1, 开盘价2, ...],
                        "high": [最高价1, 最高价2, ...],
                        "low": [最低价1, 最低价2, ...],
                        "close": [收盘价1, 收盘价2, ...]
                    },
                    "volume": [成交量1, 成交量2, ...],
                    "pct_change": [涨跌幅1, 涨跌幅2, ...]
                }
            }
        
        异常返回:
            {
                "error": "错误信息",
                "company_name": "请求的公司名称",
                "timestamp": "错误发生时间",
                "solution": "建议解决方案"
            }
        """
        try:
            logger.info(f"开始获取公司'{company_name}'的股票数据，请求天数: {days}")
            
            # 1. 根据公司名称查找股票代码
            symbol = self.__get_stock_symbol_by_company_name__(company_name)
            logger.info(f"公司'{company_name}'对应的股票代码: {symbol}")
            
            # 2. 验证和清理股票代码
            clean_symbol = symbol.split('.')[0]  # 去除交易所后缀
            if not clean_symbol.isdigit() or (len(clean_symbol) != 6 and len(clean_symbol) != 5):
                raise ValueError("股票代码必须为5-6位数字")
            
            # 3. 确定市场
            if clean_symbol.startswith(('6', '9')) or len(clean_symbol) == 5:
                market = "SH"  # 上交所或港股
            elif clean_symbol.startswith(('0', '2', '3')):
                market = "SZ"  # 深交所
            else:
                market = "SH"  # 默认
            
            logger.info(f"股票代码: {clean_symbol}, 市场: {market}")
            
            # 4. 获取数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')  # 多获取一些数据以确保准确性
            
            logger.info(f"请求数据日期范围: {start_date} 到 {end_date}")
            
            # 尝试多种数据获取方法
            df = None
            errors = []
            
            # 方法1: 使用后复权数据
            try:
                logger.info("尝试获取前复权数据")
                df = ak.stock_zh_a_hist(
                    symbol=clean_symbol,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"  # 后复权
                )
                if not df.empty:
                    logger.info("成功获取前复权数据")
            except Exception as e:
                error_msg = f"前复权数据获取失败: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
            
            
            # 如果所有方法都失败了
            if df is None or df.empty:
                error_message = f"未获取到公司 {company_name}({symbol}) 的数据，请检查代码是否正确或日期范围是否有效"
                if errors:
                    error_message += f" 错误详情: {'; '.join(errors)}"
                logger.error(error_message)
                raise ValueError(error_message)
            
            logger.info(f"成功获取到数据，原始数据条数: {len(df)}")
            
            # 5. 数据预处理
            # 只取最近的指定天数数据
            df = df.tail(days)
            df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
            df.set_index('日期', inplace=True)
            df = df.sort_index()  # 确保日期升序排列
            
            logger.info(f"处理后数据条数: {len(df)}")
            
            # 6. 计算技术指标（处理可能的NaN值）
            df['5日均线'] = df['收盘'].rolling(5, min_periods=1).mean().round(2)
            df['20日均线'] = df['收盘'].rolling(20, min_periods=1).mean().round(2)
            rsi_values = self.__calculate_rsi__(df['收盘'])
            
            logger.info("技术指标计算完成")
            
            # 7. 构建结果
            # 检查DataFrame是否为空
            if df.empty:
                error_msg = f"未获取到公司 {company_name}({symbol}) 的有效数据，请检查代码是否正确或日期范围是否有效"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 安全地提取技术指标
            sma5 = None
            sma20 = None
            rsi14 = None
            
            try:
                if len(df) > 0:
                    # 提取5日均线
                    if len(df) >= 5 and not pd.isna(df['5日均线'].iloc[-1]):
                        sma5 = round(df['5日均线'].iloc[-1], 2)
                    
                    # 提取20日均线
                    if len(df) >= 20 and not pd.isna(df['20日均线'].iloc[-1]):
                        sma20 = round(df['20日均线'].iloc[-1], 2)
                    
                    # 提取RSI
                    if len(rsi_values) > 0 and not pd.isna(rsi_values.iloc[-1]):
                        rsi14 = round(rsi_values.iloc[-1], 2)
            except Exception as e:
                logger.warning(f"提取技术指标时发生错误: {str(e)}")
            
            result = {
                "metadata": {
                    "company_name": company_name,
                    "symbol": f"{clean_symbol}.{'SS' if market == 'SH' else 'SZ'}",
                    "market": market,
                    "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "data_days": len(df),
                    "currency": "CNY"
                },
                "statistics": {
                    "close_price": {
                        "max": round(df['收盘'].max(), 2) if len(df) > 0 else 0,
                        "min": round(df['收盘'].min(), 2) if len(df) > 0 else 0,
                        "current": round(df['收盘'].iloc[-1], 2) if len(df) > 0 else 0,
                        "change_pct": round(df['涨跌幅'].iloc[-1] * 100, 2) if len(df) > 0 else 0
                    },
                    "volume": {
                        "total": int(df['成交量'].sum()) if len(df) > 0 else 0,
                        "avg": int(df['成交量'].mean()) if len(df) > 0 and not pd.isna(df['成交量'].mean()) else 0,
                        "latest": int(df['成交量'].iloc[-1]) if len(df) > 0 else 0
                    }
                },
                "technical_indicators": {
                    "sma5": sma5,
                    "sma20": sma20,
                    "rsi14": rsi14
                },
                "time_series": {
                    "dates": df.index.tolist(),
                    "ohlc": {
                        "open": df['开盘'].round(2).tolist(),
                        "high": df['最高'].round(2).tolist(),
                        "low": df['最低'].round(2).tolist(),
                        "close": df['收盘'].round(2).tolist()
                    },
                    "volume": df['成交量'].astype(int).tolist(),
                    "pct_change": df['涨跌幅'].round(4).tolist()
                }
            }
            
            logger.info(f"成功返回公司'{company_name}'的股票数据，数据天数: {result['metadata']['data_days']}")
            return result
    
        except Exception as e:
            error_msg = {
                "error": str(e),
                "company_name": company_name,
                "timestamp": datetime.now().isoformat(),
                "solution": "请检查: 1.公司名称是否正确 2.是否为交易日 3.网络连接"
            }
            logger.error(f"获取公司'{company_name}'股票数据时发生错误: {str(e)}")
            return error_msg
    
    def __get_stock_symbol_by_company_name__(self, company_name: str) -> str:
        """
        根据公司名称获取股票代码
        
        Args:
            company_name: 公司名称
            
        Returns:
            股票代码
        """
        logger.info(f"开始查找公司'{company_name}'的股票代码")
        try:
            # 获取股票列表
            logger.info("获取股票列表数据")
            stock_list = ak.stock_info_a_code_name()
            # 在股票列表中查找完全匹配的公司名称
            exact_match = stock_list[stock_list['name'] == company_name]
            
            if not exact_match.empty:
                # 如果找到完全匹配项，返回第一个
                symbol = exact_match.iloc[0]['code']
                logger.info(f"找到完全匹配的股票代码: {symbol}")
                # 确定市场
                if symbol.startswith(('6', '9')):
                    market = "SH"
                elif symbol.startswith(('0', '2', '3')):
                    market = "SZ"
                else:
                    market = "SH"  # 默认
                return f"{symbol}.{'SS' if market == 'SH' else 'SZ'}"
            
            # 如果没有完全匹配，尝试模糊匹配
            logger.info("未找到完全匹配项，尝试模糊匹配")
            fuzzy_match = stock_list[stock_list['name'].str.contains(company_name, case=False, na=False)]
            
            if not fuzzy_match.empty:
                # 如果找到模糊匹配项，返回第一个
                symbol = fuzzy_match.iloc[0]['code']
                logger.info(f"找到模糊匹配的股票代码: {symbol}")
                # 确定市场
                if symbol.startswith(('6', '9')):
                    market = "SH"
                elif symbol.startswith(('0', '2', '3')):
                    market = "SZ"
                else:
                    market = "SH"  # 默认
                return f"{symbol}.{'SS' if market == 'SH' else 'SZ'}"
            
            # 如果还是没有找到，尝试通过搜索引擎获取
            try:
                logger.info("尝试通过搜索引擎获取股票信息")
                # 获取更全面的股票信息
                stock_sh = ak.stock_sh_a_spot_em()  # 上海A股
                stock_sz = ak.stock_sz_a_spot_em()  # 深圳A股
                
                # 在上海股票中查找
                sh_match = stock_sh[stock_sh['名称'].str.contains(company_name, case=False, na=False)]
                if not sh_match.empty:
                    symbol = sh_match.iloc[0]['代码']
                    logger.info(f"在上海股票中找到匹配项: {symbol}")
                    return f"{symbol}.SS"
                
                # 在深圳股票中查找
                sz_match = stock_sz[stock_sz['名称'].str.contains(company_name, case=False, na=False)]
                if not sz_match.empty:
                    symbol = sz_match.iloc[0]['代码']
                    logger.info(f"在深圳股票中找到匹配项: {symbol}")
                    return f"{symbol}.SZ"
            except Exception as e:
                logger.warning(f"搜索引擎方法失败: {str(e)}")
                pass  # 忽略搜索引擎方法的错误，回退到抛出异常
            
            # 如果所有方法都失败了，抛出异常
            error_msg = f"未找到公司'{company_name}'对应的股票代码"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        except Exception as e:
            error_msg = f"查询公司'{company_name}'的股票代码失败: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def __calculate_rsi__(self, prices, window=14):
        """计算RSI指标"""
        logger.debug(f"开始计算RSI指标，窗口大小: {window}，数据点数: {len(prices)}")
        try:
            if len(prices) < window + 1:
                logger.warning(f"数据点数不足，需要至少{window + 1}个点，实际只有{len(prices)}个点")
                return pd.Series([None] * len(prices), index=prices.index)
            
            deltas = prices.diff()
            seed = deltas[:window+1]
            up = seed[seed >= 0].sum()/window
            down = -seed[seed < 0].sum()/window
            rs = up/down
            
            # 创建RSI序列，确保索引正确
            rsi = pd.Series(index=prices.index, dtype='float64')
            rsi.iloc[window] = 100. - (100./(1.+rs))
            
            for i in range(window+1, len(prices)):
                delta = deltas.iloc[i-1]  # 使用.iloc进行位置索引
                if delta > 0:
                    upval = delta
                    downval = 0.
                else:
                    upval = 0.
                    downval = -delta
                
                up = (up*(window-1) + upval)/window
                down = (down*(window-1) + downval)/window
                rs = up/down
                rsi.iloc[i] = 100. - (100./(1.+rs))
                
            logger.debug(f"RSI指标计算完成，结果长度: {len(rsi)}")
            return rsi
        except Exception as e:
            logger.error(f"RSI计算过程中发生错误: {str(e)}")
            # 返回空的RSI序列
            return pd.Series([None] * len(prices), index=prices.index)

# Define the fetch_stock_data tool for MCP
@app.tool()
async def fetch_stock_data(
    company_name: str,
    days: int = 30
) -> dict:
    """
    Fetch stock data for a given company name.
    
    Args:
        company_name: Company name to fetch stock data for (e.g., "工商银行", "贵州茅台")
        days: Number of days of historical data to fetch (default: 30)
        
    Returns:
        Dictionary containing stock data including metadata, statistics, 
        technical indicators, and time series data
    """
    logger.info(f"MCP工具被调用: fetch_stock_data(company_name='{company_name}', days={days})")
    collector = StockerDataCollector()
    # Run the synchronous function in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: collector.fetch_stock_data(
        company_name=company_name,
        days=days
    ))
    logger.info(f"MCP工具调用完成，返回结果类型: {type(result)}")
    return result


if __name__ == "__main__":
    #asyncio.run(main())
    app.run(transport='stdio')