# Stock Analysis Intelligent Agent System

An intelligent agent system for stock analysis based on the OWL (Optimized Workforce Learning) framework that automatically retrieves news and stock data to generate professional stock analysis reports.

## Features

- Automatically retrieves the latest news about specified companies and industries
- Retrieves historical stock data for companies
- Analyzes news sentiment and technical stock indicators
- Generates professional stock analysis reports
- Supports automatic result saving to files

## Project Structure

```
.
├── Stocker_Analyzing_Agent.py     # Main program entry point
├── FetchSinaNewsDataMCP.py        # News data retrieval module
├── FetchStockerDataMCP.py         # Stock data retrieval module
├── test_fetch_news.py             # News data retrieval test script
├── test_fetch_stock.py            # Stock data retrieval test script
├── config/
│   └── Fetch.json                 # MCP configuration file
└── result/                        # Analysis report output directory
```

## Core Module Introduction

### 1. Stocker_Analyzing_Agent.py

The main program file responsible for coordinating various modules to complete stock analysis tasks.

Key features:
- Initializes MCP toolkit connections
- Builds intelligent agent societies
- Executes analysis tasks
- Saves results to files
- Handles network exceptions and retry mechanisms

### 2. FetchSinaNewsDataMCP.py

News data retrieval module responsible for searching relevant news from Sina News.

Key features:
- Searches news about specified companies or industries through Sina News API
- Supports pagination to retrieve multiple pages of search results
- Parses news titles, links, dates, and content
- Supports multiple date format parsing (e.g., "7 hours ago", "2025-11-20", etc.)
- Filters and deduplicates results by time

### 3. FetchStockerDataMCP.py

Stock data retrieval module responsible for obtaining historical stock data for specified companies.

Key features:
- Automatically finds stock codes based on company names
- Retrieves historical stock price data (open price, close price, high price, low price, volume, etc.)
- Calculates technical indicators (MA, MACD, RSI, etc.)
- Handles cases where adjusted data retrieval fails

## Installation and Configuration

1. Ensure OWL framework and related dependencies are installed:
```bash
pip install owl-sdk
```

2. Configure API keys:
Configure DeepSeek API key in the `.env` file:
```
DEEPSEEK_API_KEY="your-api-key"
```

3. Ensure required Python packages are installed:
```bash
pip install akshare requests beautifulsoup4 fake-useragent mcp-server-fastmcp
```

## Usage

### Running the Main Program

```bash
python Stocker_Analyzing_Agent.py
```

By default, it will analyze Agricultural Bank of China's stock. To analyze other companies, modify the code:
```python
company = 'Industrial and Commercial Bank of China'
industry = 'Financial Services'
```

### Running Test Scripts

Test news data retrieval:
```bash
python test_fetch_news.py
```

Test stock data retrieval:
```bash
python test_fetch_stock.py
```

## Output Results

Analysis reports are automatically saved in the `result/YYYY-MM-DD/` directory with the filename `{Company Name}_{Industry}_{Timestamp}.txt`.

## Error Handling

- Network connection exceptions will automatically retry (up to 3 times)
- Data retrieval failures will be logged and execution will continue
- Supports safe disconnection of MCP toolkits

## Logging

The system records logs in the following files:
- Console output
- FetchStockerNewsLog.txt (news and stock data retrieval logs)