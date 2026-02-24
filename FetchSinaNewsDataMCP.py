import requests
from bs4 import BeautifulSoup
import time
import random
import re
from datetime import datetime, timedelta
import argparse
import json
from fake_useragent import UserAgent
import asyncio
import sys
import logging
import os
from mcp.server.fastmcp import FastMCP

# 导入logger_utils中的全局日志函数
from logger_utils import log_global_info, log_global_debug, log_global_warning, log_global_error, log_global_critical

# MCP imports
#from mcp.server import Server
#from mcp.types import Tool

# Remove legacy logging setup
# The following code was removed:
# # Set up logging
# # Ensure the log directory exists
# log_file_path = 'FetchStockerNewsLog.txt'
# try:
#     if not os.path.exists(os.path.dirname(log_file_path)):
#         os.makedirs(os.path.dirname(log_file_path))
# except Exception:
#     # If we can't create directories, just use the file name directly
#     pass
# 
# # Configure logging with both file and console handlers
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler(log_file_path, encoding='utf-8'),
#         logging.StreamHandler()  # Also print to console
#     ],
#     force=True  # Force reconfiguration in case logging was already configured
# )
# 
# logger = logging.getLogger(__name__)

log_global_info("FetchSinaNewsDataMCP模块已加载")

ua = UserAgent()

# Create MCP server
app = FastMCP("sina-news-fetcher")

class NewsDataCollector():
   
    def __init__(self):
        pass

    def __get_random_delay__(self):
        """获取2-5秒的随机延迟"""
        delay = random.uniform(2, 5)
        log_global_debug(f"随机延迟设置为: {delay:.2f}秒")
        return delay

    def __clean_text__(self, text):
        """清理文本中的乱码和多余空格"""
        if not text:
            return ""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 替换特殊空白字符
        text = text.replace('\u3000', ' ').replace('\xa0', ' ')
        # 移除连续换行和空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def __get_article_content__(self, url: str):
        """获取文章正文内容（完整版）"""
        try:
            log_global_debug(f"开始获取文章内容: {url}")
            
            headers = {
                "User-Agent": ua.random,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9"
            }
            
            # 处理新浪特殊URL
            if 'link.sina.com.cn' in url:
                log_global_debug(f"检测到新浪跳转链接: {url}")
                real_url = self.__get_sina_redirect_url__(url)
                if real_url:
                    url = real_url
                    log_global_debug(f"跳转到实际链接: {url}")
            
            delay = self.__get_random_delay__()
            time.sleep(delay)
            log_global_debug(f"延迟 {delay:.2f}秒后发起请求")
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=15)
            response_time = time.time() - start_time
            response.encoding = 'utf-8'  # 强制使用UTF-8编码
            
            log_global_debug(f"HTTP响应状态: {response.status_code}, 响应时间: {response_time:.2f}s, 内容长度: {len(response.text)}")
            
            if response.status_code != 200:
                log_global_warning(f"HTTP请求失败，状态码: {response.status_code}")
                return f"内容获取失败: HTTP {response.status_code}"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 移除不需要的元素
            for element in soup(['script', 'style', 'iframe', 'nav', 'footer', 'aside', 'header', 'button', 'a']):
                element.decompose()
            
            # 增强的内容选择器列表（按优先级排序）
            content_selectors = [
                {'selector': 'article', 'attrs': {}},  # 通用文章标签
                {'selector': '.article-content', 'attrs': {}},  # 新浪/网易
                {'selector': '.content', 'attrs': {}},  # 腾讯
                {'selector': '.main-content', 'attrs': {}},  # 搜狐
                {'selector': '.article-main', 'attrs': {}},  # 其他
                {'selector': '.text', 'attrs': {}},  # 通用
                {'selector': '#artibody', 'attrs': {}},  # 新浪另一种
                {'selector': 'div', 'attrs': {'class': 'article'}},  # 更精确匹配
                {'selector': 'div', 'attrs': {'id': 'article'}},  # ID匹配
                {'selector': 'div', 'attrs': {'class': 'content-wrapper'}},  # 新浪财经
                {'selector': '.article-body', 'attrs': {}},  # 新浪部分新闻
                {'selector': '.article-detail', 'attrs': {}},  # 新浪详情页
                {'selector': '.article-txt', 'attrs': {}}  # 新浪财经
            ]
            
            for idx, selector in enumerate(content_selectors):
                try:
                    content = soup.find(selector['selector'], **selector['attrs'])
                    if content:
                        text = content.get_text(separator='\n', strip=True)
                        text = self.__clean_text__(text)
                        if text:  # 只要有内容就返回
                            log_global_debug(f"成功从选择器 #{idx+1} 提取内容，长度: {len(text)} 字符")
                            return text
                except Exception as e:
                    log_global_debug(f"选择器 #{idx+1} 提取失败: {str(e)}")
                    continue
            
            # 最终回退方案：尝试获取整个body
            body = soup.find('body')
            if body:
                text = body.get_text(separator='\n', strip=True)
                text = self.__clean_text__(text)
                if text:
                    log_global_debug(f"从body提取内容，长度: {len(text)} 字符")
                    return text
            
            log_global_warning(f"未能从文章 {url} 中提取到有效内容")
            return "内容提取成功（但可能不完整）"
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            log_global_error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"内容获取失败: {str(e)}"
            log_global_error(error_msg)
            return error_msg
        
    def __get_sina_redirect_url__(self, url: str):
        """获取新浪跳转链接的真实URL（增强版）"""
        try:
            log_global_debug(f"解析新浪跳转链接: {url}")
            headers = {
                "User-Agent": ua.random,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Referer": "https://news.sina.com.cn/"
            }
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
            if response.status_code == 302 and 'Location' in response.headers:
                location = response.headers['Location']
                log_global_debug(f"跳转目标: {location}")
                if location.startswith('//'):
                    full_url = 'https:' + location
                    log_global_debug(f"补全协议后URL: {full_url}")
                    return full_url
                return location
            else:
                log_global_warning(f"未发现跳转或请求失败，状态码: {response.status_code}")
        except Exception as e:
            log_global_error(f"获取跳转链接失败: {str(e)}")
        return None

    def __parse_date_text__(self, date_text: str) -> str:
        """
        解析日期文本，支持多种格式
        支持格式如:
        - "新浪基金 2025-11-20 13:53:55"
        - "大众证券报 7小时前"
        - "XX网 1天前"
        - "XX新闻 2025-11-20"
        """
        if not date_text:
            return ""
        
        try:
            # 清理文本
            cleaned_text = self.__clean_text__(date_text).strip()
            if not cleaned_text:
                return ""
            
            log_global_debug(f"解析日期文本: {cleaned_text}")
            
            # 分割文本，获取时间部分
            parts = cleaned_text.split()
            if not parts:
                return ""
            
            # 获取最后一个部分作为时间信息
            time_part = parts[-1]
            
            # 处理相对时间格式（如"7小时前", "1天前"）
            if "小时前" in time_part:
                hours_ago = int(''.join(filter(str.isdigit, time_part)))
                target_time = datetime.now() - timedelta(hours=hours_ago)
                formatted_date = target_time.strftime("%Y-%m-%d %H:%M:%S")
                log_global_debug(f"解析相对时间（X小时前）: {formatted_date}")
                return formatted_date
            elif "天前" in time_part:
                days_ago = int(''.join(filter(str.isdigit, time_part)))
                target_time = datetime.now() - timedelta(days=days_ago)
                formatted_date = target_time.strftime("%Y-%m-%d %H:%M:%S")
                log_global_debug(f"解析相对时间（X天前）: {formatted_date}")
                return formatted_date
            elif "分钟前" in time_part:
                minutes_ago = int(''.join(filter(str.isdigit, time_part)))
                target_time = datetime.now() - timedelta(minutes=minutes_ago)
                formatted_date = target_time.strftime("%Y-%m-%d %H:%M:%S")
                log_global_debug(f"解析相对时间（X分钟前）: {formatted_date}")
                return formatted_date
            
            # 处理绝对时间格式（如"2025-11-20 13:53:55"）
            # 如果最后一个部分不是相对时间，则尝试解析整个文本中的日期
            import re
            # 查找日期时间模式 YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD HH:MM
            datetime_pattern = r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}|\d{4}-\d{2}-\d{2})'
            match = re.search(datetime_pattern, cleaned_text)
            if match:
                date_str = match.group(1)
                # 如果只有日期没有时间，补充默认时间
                if len(date_str) == 10:  # YYYY-MM-DD
                    date_str += " 00:00:00"
                elif len(date_str) == 16:  # YYYY-MM-DD HH:MM
                    date_str += ":00"
                log_global_debug(f"解析绝对时间: {date_str}")
                return date_str
            
            # 查找单独的日期模式 YYYY-MM-DD
            date_pattern = r'\d{4}-\d{2}-\d{2}'
            match = re.search(date_pattern, cleaned_text)
            if match:
                formatted_date = match.group(0) + " 00:00:00"
                log_global_debug(f"解析日期模式: {formatted_date}")
                return formatted_date
                
            # 如果无法解析，返回空字符串
            log_global_debug("无法解析日期文本")
            return ""
        except Exception as e:
            log_global_warning(f"解析日期文本失败: {date_text}, 错误: {str(e)}")
            return ""

    def __extract_source_from_date_text__(self, date_text: str) -> str:
        """
        从日期文本中提取新闻来源信息
        支持格式如:
        - "新浪基金 2025-11-20 13:53:55"
        - "大众证券报 7小时前"
        """
        if not date_text:
            return "新浪新闻"
        
        try:
            # 清理文本
            cleaned_text = self.__clean_text__(date_text).strip()
            if not cleaned_text:
                return "新浪新闻"
            
            log_global_debug(f"提取新闻来源: {cleaned_text}")
            
            # 分割文本
            parts = cleaned_text.split()
            if len(parts) >= 2:
                # 第一个部分通常是来源信息
                source = parts[0]
                # 清理来源信息，移除可能的特殊字符
                source = re.sub(r'[^\w\u4e00-\u9fff]', '', source)  # 保留中文和数字字母
                if source:
                    log_global_debug(f"提取到新闻来源: {source}")
                    return source
            
            # 如果无法提取来源，返回默认值
            return "新浪新闻"
        except Exception as e:
            log_global_warning(f"提取来源信息失败: {date_text}, 错误: {str(e)}")
            return "新浪新闻"

    async def __fetch_sina_news__(self, keyword: str, industry: str, start_date: str, end_date: str, max_results: int = 50):
        """获取新浪新闻数据"""
        log_global_info(f"开始从新浪新闻获取数据: keyword={keyword}, start_date={start_date}, end_date={end_date}")
        
        # 使用与FetchSinaNewsData.py相同的URL和参数
        search_url = "https://search.sina.com.cn/"
        headers = {
            "User-Agent": ua.random,
            "Referer": "https://news.sina.com.cn/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br"
        }
        
        news_items = []
        page = 1
        max_pages = min(5, (max_results // 20) + 1)  # 最多获取5页或根据需要的结果数量计算页数
        
        log_global_debug(f"预计最多获取 {max_pages} 页，每页最多20条新闻")
        
        while page <= max_pages and len(news_items) < max_results:
            # 构建搜索参数，与FetchSinaNewsData.py保持一致
            params = {
                'q': keyword,
                'c': 'news',
                'range': 'all',  # 搜索全部范围而不仅是标题
                'time': 'custom',
                'stime': start_date,
                'etime': end_date,
                'num': min(20, max_results - len(news_items)),  # 每页获取20条或剩余需要的数量
                'sort': 'time',
                'col': '1_7',  # 限定新闻频道
                'page': page  # 添加页码参数
            }
            
            try:
                log_global_debug(f"发送请求到新浪新闻搜索接口: {search_url}, 第 {page} 页")
                log_global_debug(f"请求参数: {params}")
                
                start_time = time.time()
                response = requests.get(search_url, headers=headers, params=params, timeout=20)
                request_time = time.time() - start_time
                
                response.encoding = 'utf-8'  # 强制使用UTF-8编码
                response.raise_for_status()
                
                log_global_debug(f"收到响应，状态码: {response.status_code}, 请求时间: {request_time:.2f}s, 响应大小: {len(response.text)} 字节")
                log_global_debug(f"响应URL: {response.url}")
                
                # 解析HTML响应
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 使用与FetchSinaNewsData.py相同的增强结果选择器
                results = soup.select('.box-result') or soup.select('.result') or soup.select('.search-result-item') or soup.select('.news-item')
                
                log_global_debug(f"第 {page} 页解析到 {len(results)} 条新闻数据")
                
                # 检查是否有结果，如果没有结果则停止翻页
                if not results:
                    log_global_info("未找到更多结果，停止翻页")
                    break
                
                # 处理当前页的所有结果
                page_items_count = 0
                for i, item in enumerate(results):
                    try:
                        log_global_debug(f"解析第 {page} 页第 {i+1} 条新闻")
                        
                        # 使用与FetchSinaNewsData.py相同的方式获取标题元素
                        title_elem = item.select_one('h2 a') or item.select_one('a[target="_blank"]') or item.select_one('a')
                        if not title_elem:
                            log_global_debug("未找到标题元素，跳过该新闻")
                            continue
                        
                        title = self.__clean_text__(title_elem.get_text(strip=True))
                        url = title_elem.get('href', '')
                        
                        # 确保URL是完整的
                        if 'link.sina.com.cn' in url:
                            real_url = self.__get_sina_redirect_url__(url)
                            if real_url:
                                url = real_url
                        elif url.startswith('//'):
                            url = 'https:' + url
                        elif url.startswith('/'):
                            url = 'https://news.sina.com.cn' + url
                        
                        log_global_debug(f"新闻标题: {title}")
                        log_global_debug(f"新闻链接: {url}")
                        
                        # 使用与FetchSinaNewsData.py相同的方式获取日期信息
                        source_elem = item.select_one('.source') or item.select_one('.fgray_time')
                        date_elem = item.select_one('.time') or item.select_one('.fgray_time')
                        
                        date_text = self.__clean_text__(date_elem.get_text(strip=True)) if date_elem else ""
                        # 提取日期部分，处理不同格式的日期信息
                        date = self.__parse_date_text__(date_text)
                        
                        log_global_debug(f"新闻日期: {date_text}, 解析后日期: {date}")
                        
                        # 获取详细内容
                        content = ""
                        if url:
                            log_global_debug(f"获取文章详细内容: {url}")
                            content = self.__get_article_content__(url)
                            log_global_debug(f"文章内容长度: {len(content)} 字符")
                        
                        news_item = {
                            'source': self.__extract_source_from_date_text__(date_text) if date_text else "新浪新闻",
                            'title': title,
                            'url': url,
                            'date': date,
                            'content': content,  # 包含详细内容
                            'search_term': keyword
                        }
                        
                        # 验证必要字段
                        if news_item['title'] and news_item['url']:
                            news_items.append(news_item)
                            page_items_count += 1
                            log_global_debug(f"成功添加新闻: {title}")
                        else:
                            log_global_debug("新闻缺少必要字段，跳过")
                            
                    except Exception as e:
                        log_global_warning(f"解析第 {page} 页第 {i+1} 条新闻时出错: {str(e)}")
                        continue
                
                log_global_info(f"第 {page} 页成功处理 {page_items_count} 条新闻")
                
                # 如果当前页没有新添加的新闻，停止翻页
                if page_items_count == 0:
                    log_global_info("当前页没有有效新闻，停止翻页")
                    break
                
                page += 1
                
                # 添加延迟以避免请求过于频繁
                if page <= max_pages and len(news_items) < max_results:
                    delay = self.__get_random_delay__()
                    log_global_debug(f"等待 {delay:.2f} 秒后继续获取下一页")
                    time.sleep(delay)
                
            except requests.exceptions.ConnectionError as e:
                log_global_error(f"连接新浪新闻接口失败: {str(e)}")
                # 实现重试机制
                retry_count = 0
                max_retries = 3
                while retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2 ** retry_count  # 指数退避
                    log_global_info(f"第 {retry_count} 次重试，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    
                    try:
                        response = requests.get(search_url, headers=headers, params=params, timeout=20)
                        response.encoding = 'utf-8'
                        response.raise_for_status()
                        log_global_info("重试成功")
                        break
                    except requests.exceptions.ConnectionError:
                        if retry_count >= max_retries:
                            log_global_error("多次重试后仍然连接失败，停止获取")
                            return news_items
                        continue
            except requests.exceptions.RequestException as e:
                log_global_error(f"请求新浪新闻接口失败: {str(e)}")
                break
            except Exception as e:
                log_global_error(f"获取新浪新闻时发生未知错误: {str(e)}")
                break
            
        # 时间过滤：只保留在指定时间范围内的新闻（只比较日期部分）
        filtered_news_items = []
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        
        for item in news_items:
            try:
                item_date_str = item.get('date', '')
                if item_date_str:
                    # 解析新闻日期（只比较日期部分）
                    if ' ' in item_date_str:
                        item_date_obj = datetime.strptime(item_date_str, "%Y-%m-%d %H:%M:%S")
                    else:
                        item_date_obj = datetime.strptime(item_date_str, "%Y-%m-%d")
                    
                    # 只比较日期部分
                    item_date_only = item_date_obj.date()
                    start_date_only = start_date_obj.date()
                    end_date_only = end_date_obj.date()
                    
                    # 检查是否在指定日期范围内
                    if start_date_only <= item_date_only <= end_date_only:
                        filtered_news_items.append(item)
                    else:
                        log_global_debug(f"过滤掉日期不在范围内的新闻: {item_date_str}")
                else:
                    # 如果没有日期信息，默认保留
                    filtered_news_items.append(item)
            except Exception as e:
                log_global_warning(f"过滤新闻时解析日期出错: {str(e)}, 保留该新闻")
                # 解析日期出错时，默认保留该新闻
                filtered_news_items.append(item)
        
        log_global_info(f"时间过滤后剩余 {len(filtered_news_items)} 条新闻")
        log_global_info(f"新浪新闻获取完成，共获取到 {len(filtered_news_items)} 条有效新闻")
        return filtered_news_items[:max_results]  # 返回限定数量的结果

    async def fetch_news(self, company: str = "", industry: str = "", days: int = 1, max_results: int = 50):
        """获取新浪新闻数据"""
        start_time = time.time()
        log_global_info(f"开始获取新闻数据: company={company}, industry={industry}, days={days}, max_results={max_results}")
        
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        log_global_info(f"搜索时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        
        sources = [self.__fetch_sina_news__]
        all_news = []
        
        search_terms = []
        if company:
            search_terms.append(company)
        if industry: 
            search_terms.append(industry)
        
        log_global_debug(f"搜索关键词: {search_terms}")
        
        for source in sources:
            for term in search_terms:
                try:
                    delay = self.__get_random_delay__()
                    log_global_info(f"等待 {delay:.2f} 秒后搜索关键词: {term}")
                    time.sleep(delay)
                    log_global_info(f"正在搜索关键词: {term}")
                    # 修复参数传递问题，正确传递keyword, industry, start_date, end_date
                    news = await source(term, industry, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                    all_news.extend(news)
                    log_global_info(f"获取到 {len(news)} 条结果")
                    
                    if len(all_news) >= max_results * 2:  # 放宽初步限制
                        log_global_info("已达到初步结果限制，停止搜索")
                        break
                except Exception as e:
                    error_msg = f"搜索 {term} 失败: {str(e)}"
                    log_global_error(error_msg)
                    continue
        
        # 去重并排序
        log_global_debug(f"开始去重处理，原始数量: {len(all_news)}")
        seen = set()
        unique_news = []
        for item in all_news:
            identifier = (item['title'], item['url'])
            if identifier not in seen:
                seen.add(identifier)
                unique_news.append(item)
        
        log_global_debug(f"去重后数量: {len(unique_news)}")
        
        # 按日期排序（最新的在前）
        unique_news.sort(key=lambda x: x['date'], reverse=True)
        
        # 限制结果数量
        final_results = unique_news[:max_results]
        
        # 转换为字典格式
        result_dict = {}
        for i, news_item in enumerate(final_results, 1):
            result_dict[f"新闻{i}"] = news_item
        
        execution_time = time.time() - start_time
        log_global_info(f"新闻获取完成，总共找到 {len(all_news)} 条新闻，去重后 {len(unique_news)} 条，返回 {len(final_results)} 条，耗时 {execution_time:.2f} 秒")
        return result_dict

# Define the fetch_news tool for MCP
@app.tool()
async def fetch_news(
    company: str = "",
    industry: str = "",
    days: int = 1,
    max_results: int = 100
) -> dict:
    """
    Fetch news about a company or industry from Sina News.
    
    Args:
        company: Company name to search for
        industry: Industry name to search for
        days: Number of days to look back for news (default: 1)
        max_results: Maximum number of results to return (default: 100)
        
    Returns:
        Dictionary of news items with keys "新闻1", "新闻2", etc.
        Each value contains source, title, url, date, content and search term
    """
    log_global_info(f"MCP工具被调用: fetch_news(company='{company}', industry='{industry}', days={days}, max_results={max_results})")
    collector = NewsDataCollector()

    result = await collector.fetch_news(
        company=company,
        industry=industry,
        days=days,
        max_results=max_results
    )
    
    log_global_info(f"MCP工具调用完成，返回结果数量: {len(result)}")
    return result

if __name__ == "__main__":
    # Run the MCP server
    app.run(transport='stdio')