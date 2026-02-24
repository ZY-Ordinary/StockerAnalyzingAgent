# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========

# To run this file, you need to configure the DeepSeek API key
# You can obtain your API key from DeepSeek platform: https://platform.deepseek.com/api_keys
# Set it as DEEPSEEK_API_KEY="your-api-key" in your .env file or add it to your environment variables

import sys
from dotenv import load_dotenv

from camel.models import ModelFactory
from camel.toolkits import (
    ExcelToolkit,
    SearchToolkit,
    FileWriteToolkit,
    CodeExecutionToolkit,
)
from camel.types import ModelPlatformType, ModelType
#from camel.societies import RolePlaying
from camel.logger import set_log_level

import asyncio
#from camel.toolkits.mcp_toolkit import MCPToolkit, MCPClient
from camel.toolkits import FunctionTool, MCPToolkit
from owl.utils.enhanced_role_playing import OwlRolePlaying, arun_society

from owl.utils import run_society

import pathlib
import functools
import os
from datetime import datetime

# 导入logger_utils中的全局日志函数
from logger_utils import log_global_info, log_global_debug, log_global_warning, log_global_error, log_global_critical

# 开关：控制是否保存chat_history到文件
SAVE_CHAT_HISTORY_TO_FILE = True  # 设置为False可以禁用此功能

#set_log_level(level="DEBUG")
set_log_level(level="INFO")

base_dir = pathlib.Path(__file__).parent.parent
env_path = base_dir / "owl" / ".env"
load_dotenv(dotenv_path=str(env_path))



async def construct_society(question: str, tools: list[FunctionTool]) -> OwlRolePlaying:
    r"""Construct a society of agents based on the given question.

    Args:
        question (str): The task or question to be addressed by the society.

    Returns:
        RolePlaying: A configured society of agents ready to address the question.
    """

    # Create models for different components
    models = {
        "user": ModelFactory.create(
            model_platform=ModelPlatformType.DEEPSEEK,
            model_type=ModelType.DEEPSEEK_CHAT,
            model_config_dict={"temperature": 0},
        ),
        "assistant": ModelFactory.create(
            model_platform=ModelPlatformType.DEEPSEEK,
            model_type=ModelType.DEEPSEEK_CHAT,
            model_config_dict={"temperature": 0},
        ),
    }

    # Configure toolkits
    # tools = [
    #     #*CodeExecutionToolkit(sandbox="subprocess", verbose=True).get_tools(),
    #     *LocalTools,
    #     #SearchToolkit().search_baidu,
    #     *ExcelToolkit().get_tools(),
    #     *FileWriteToolkit(output_dir="./").get_tools(),
    # ]

    # Configure agent roles and parameters
    user_agent_kwargs = {"model": models["user"]}
    assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}

    # Configure task parameters
    task_kwargs = {
        "task_prompt": question,
        "with_task_specify": False,
    }

    # Create and return the society
    society = OwlRolePlaying(
        **task_kwargs,
        user_role_name="user",
        user_agent_kwargs=user_agent_kwargs,
        assistant_role_name="assistant",
        assistant_agent_kwargs=assistant_agent_kwargs,
        output_language="Chinese",
    )

    return society


def save_chat_history_to_md(chat_history, company_name):
    """
    将chat_history保存为markdown格式的文件
    :param chat_history: 聊天历史记录
    :param company_name: 公司名称
    """
    try:
        # 确保文件名安全 - 移除或替换非法字符
        safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # 创建result目录（如果不存在）
        result_dir = pathlib.Path(__file__).parent / "result"
        result_dir.mkdir(exist_ok=True)
        
        # 生成文件名，包含公司名称和时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{safe_company_name}_{timestamp}.md"
        filepath = result_dir / filename
        
        # 写入markdown文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Chat History for {company_name}\n\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # for idx, message in enumerate(chat_history):
            #     role = message.get("role", "Unknown")
            #     content = message.get("content", "")
                
            #     # 根据角色设置标题
            #     if role.lower() == "user":
            #         f.write(f"## 用户提问 {idx+1}:\n{content}\n\n")
            #     elif role.lower() == "assistant":
            #         f.write(f"## AI回复 {idx+1}:\n{content}\n\n")
            #     elif role.lower() == "system":
            #         f.write(f"## 系统提示 {idx+1}:\n{content}\n\n")
            #     else:
            #         f.write(f"## {role} {idx+1}:\n{content}\n\n")
            f.write(f"{chat_history}\n\n")
        log_global_info(f"聊天历史已保存到: {filepath}")
        
    except Exception as e:
        log_global_error(f"保存聊天历史时发生错误: {str(e)}")


async def main(company, industry):
    r"""Main function to run the OWL system with an example question."""

    log_global_info(f"开始执行 {company} ({industry}) 的股票分析任务")
    
    #检查是否有名为'result'的文件夹，如没有则创建
    result_dir = pathlib.Path(__file__).parent / "result"
    result_dir.mkdir(exist_ok=True)
    log_global_debug(f"确保结果目录存在: {result_dir}")

    today = datetime.now().strftime("%Y-%m-%d")
    today_dir = result_dir / today
    today_dir.mkdir(exist_ok=True)
    log_global_debug(f"确保当天目录存在: {today_dir}")
    
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{company}_{industry}_{current_time}.md"

    default_task = f'''请作为专业金融分析师，执行以下任务:
    1.数据获取
        a. 搜索今日关于 {company}（公司名称）及所属 {industry}（行业）的最新新闻与市场动态。
        b. 获取 {company} 近两个月的股票历史价格数据(如开盘价、收盘价、最高价、最低价、成交量)。
        注意:仅需执行一次搜索, 无需重复验证。调用工具时，请严格使用{company}和{industry}，不要加额外定语修饰。
    2.情绪与趋势分析
        新闻情绪分析：基于今日新闻，判断市场对 {company} 的情绪倾向（积极/消极/中性），并提取关键事件（如财报发布、政策变动、行业动态等）及其潜在影响。技术面分析：结合近一个月股价走势，识别关键支撑位、阻力位、趋势形态（如上升/下降/盘整), 并分析成交量变化。
    3. 预测与报告生成
        明日股价预测：综合新闻情绪与技术面分析，预测明日 {company} 股票的潜在走势（如上涨/下跌概率、波动范围），并说明预测逻辑与风险因素。
    报告格式要求：
        标题：《{company}股票分析报告》
        结构包括：
            摘要：核心结论与预测概要
            新闻内容：主要参考的新闻内容（总结参考了哪些新闻，并总结列出新闻的摘要）
            新闻情绪分析：事件摘要与市场情绪解读
            技术分析：股价走势图表描述（无需实际图表）与关键位点分析
            综合预测：明日走势判断及依据
            风险提示：潜在不确定性（如市场波动、新闻时效性）
        要求：
            语言简洁专业，避免主观臆断，结论需基于数据与事实。
            若信息不足或存在矛盾，明确说明局限性。
    最终报告保存在./result/{today}文件夹下，文件名为{filename}'''

    task = default_task

    # Add MCP server
    mcp_toolkit = MCPToolkit(config_path="config/Fetch.json")
    log_global_debug("MCP Toolkit初始化完成")

    try:
        # Connect to all configured MCP servers
        log_global_info("开始连接MCP服务器...")
        await mcp_toolkit.connect()
        log_global_info("MCP服务器连接成功")

        # Get tools from MCP toolkit and add FileWriteToolkit
        mcp_tools = mcp_toolkit.get_tools()  # 直接使用返回的工具列表
        file_tools = FileWriteToolkit(output_dir="./").get_tools()
        
        # 合并工具列表
        tools = mcp_tools + file_tools
        log_global_debug(f"加载了 {len(tools)} 个工具")

        # Construct and run the society
        log_global_info("开始构建智能体社会...")
        society = await construct_society(task, tools)
        log_global_info("智能体社会构建完成")

        log_global_info("开始运行智能体社会...")
        answer, chat_history, token_count = await arun_society(society)
        log_global_info("智能体社会运行完成")

        # 如果开关打开，则保存chat_history到文件
        if SAVE_CHAT_HISTORY_TO_FILE:
            save_chat_history_to_md(chat_history, company)

        log_global_info(answer)
        
    except Exception as e:
        log_global_error(f"执行股票分析任务时发生错误: {str(e)}")
        raise
        
    finally:
        # Make sure to disconnect safely after all operations are completed.
        try:
            # Properly disconnect the MCP toolkit
            if 'mcp_toolkit' in locals() and mcp_toolkit is not None:
                # 使用更安全的方式断开连接，避免取消作用域问题
                try:
                    # 创建一个新的任务来处理断开连接
                    log_global_debug("开始断开MCP toolkit连接...")
                    disconnect_task = asyncio.create_task(mcp_toolkit.disconnect())
                    # 等待断开连接完成，但使用更安全的超时处理
                    await asyncio.wait_for(disconnect_task, timeout=5.0)
                    log_global_info("MCP toolkit断开连接成功")
                except asyncio.TimeoutError:
                    log_global_warning("MCP toolkit断开连接超时")
                except asyncio.CancelledError:
                    log_global_warning("MCP toolkit断开连接被取消")
                except Exception as e:
                    log_global_error(f"MCP toolkit断开连接失败: {e}")
        except Exception as e:
            log_global_error(f"断开连接清理过程中发生错误: {e}")

    log_global_info(f"完成 {company} ({industry}) 的股票分析任务")


if __name__ == "__main__":
    log_global_info("启动股票分析代理系统")

    # 定义公司和行业列表
    companies_and_industries = [
       {"company": "云赛智联", "industry": "AI算力"},
       # {"company": "浪潮软件", "industry": "软件信息"},
       {"company": "工商银行", "industry": "金融财政"},
       #{"company": "农业银行", "industry": "金融财政"},
       {"company": "中芯国际", "industry": "芯片制造"},
       {"company": "上海电气", "industry": "电力"},
       {"company": "药明康德", "industry": "医药行业"},
       {"company": "中国核电", "industry": "电力行业"}
    ]
    
    log_global_info(f"开始批量处理 {len(companies_and_industries)} 个公司的股票分析任务")
    
    # 遍历公司和行业列表，逐个进行分析
    for idx, item in enumerate(companies_and_industries, 1):
        company = item["company"]
        industry = item["industry"]
        
        log_global_info(f"[{idx}/{len(companies_and_industries)}] 开始分析 {company} ({industry}) 的股票...")
        
        try:
            # 为每个公司调用main函数
            asyncio.run(main(company=company, industry=industry))
            log_global_info(f"[{idx}/{len(companies_and_industries)}] 完成分析 {company} ({industry}) 的股票")
            
            # 添加延迟以避免请求过于频繁
            import time
            log_global_debug(f"等待5秒后处理下一个公司...")
            time.sleep(5)  # 等待5秒再处理下一个公司
            
        except Exception as e:
            log_global_error(f"分析 {company} ({industry}) 时发生错误: {e}")
            continue  # 继续处理下一个公司
    
    log_global_info("所有公司的股票分析任务已完成")