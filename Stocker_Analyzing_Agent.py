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


async def main():
    r"""Main function to run the OWL system with an example question."""
    # Example research question
    #company = '云赛智联'
    #industry = 'AI算力'
    #company = '浪潮软件'
    #industry = '软件信息' 
    company = '工商银行'
    industry = '金融财政'   
    #company = '农业银行'
    #industry = '金融财政' 
    #company = '中芯国际'
    #industry = '芯片制造'   
    #default_task = f"搜索今天关于{company}以及相关{industry}新闻，根据新闻内容分析市场关于{company}未来股票走势的情绪，并结合近一个月{company}股票走势预测明天{company}股票走势,仅需要搜索一次新闻和股票信息就可以，不需要尝试反复搜索以求验证结果。分析预测完成整理成一份专业的股票分析报告"

    #检查是否有名为'result'的文件夹，如没有则创建
    result_dir = pathlib.Path(__file__).parent / "result"
    result_dir.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    today_dir = result_dir / today
    today_dir.mkdir(exist_ok=True)
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

    # Override default task if command line argument is provided
    task = sys.argv[1] if len(sys.argv) > 1 else default_task

    # Add MCP server
    mcp_toolkit = MCPToolkit(config_path="config/Fetch.json")

    try:
        # Connect to all configured MCP servers
        print ("Connect to MCP server...")
        await mcp_toolkit.connect()
        print ("Connect to MCP server successfully")

        tools = [*mcp_toolkit.get_tools()]
        tools.append(*FileWriteToolkit(output_dir="./").get_tools())

        # Construct and run the society
        society = await construct_society(task, tools)

        answer, chat_history, token_count = await arun_society(society)

        # Output the result
        print(f"\033[94mAnswer: {answer}\033[0m")
        #print ('正在运行OWL系统...')
        
        # 保存结果到文件
        # 1. 检查是否有名为'result'的文件夹，如没有则创建
        # result_dir = pathlib.Path(__file__).parent / "result"
        # result_dir.mkdir(exist_ok=True)
        
        # # 2. 在'result'文件夹下创建以今天日期命名的文件夹
        # today = datetime.now().strftime("%Y-%m-%d")
        # today_dir = result_dir / today
        # today_dir.mkdir(exist_ok=True)
        
        # # 3. 将结果保存到文件
        # current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        # filename = f"{company}_{industry}_{current_time}.txt"
        # result_file = today_dir / filename
        
        # with open(result_file, 'w', encoding='utf-8') as f:
        #     f.write(answer)
        
        #print(f"结果已保存到: {result_file}")
        
    finally:
        # Make sure to disconnect safely after all operations are completed.
        try:
            # Properly disconnect the MCP toolkit
            if 'mcp_toolkit' in locals() and mcp_toolkit is not None:
                # 使用更安全的方式断开连接，避免取消作用域问题
                try:
                    # 创建一个新的任务来处理断开连接
                    disconnect_task = asyncio.create_task(mcp_toolkit.disconnect())
                    # 等待断开连接完成，但使用更安全的超时处理
                    await asyncio.wait_for(disconnect_task, timeout=5.0)
                except asyncio.TimeoutError:
                    print("Warning: MCP toolkit disconnect timed out")
                except asyncio.CancelledError:
                    print("Warning: MCP toolkit disconnect was cancelled")
                except Exception as e:
                    print(f"Disconnect failed: {e}")
        except Exception as e:
            print(f"Error during disconnect cleanup: {e}")


if __name__ == "__main__":
    
    asyncio.run(main())