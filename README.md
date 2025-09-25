# Binance Futures Trading Bot (Testnet)
## Project Overview

This project is a Binance Futures Trading Bot built with Python.
It allows placing Market, Limit, and Stop orders on the Binance Testnet, making it safe to test trading strategies without risking real funds.

The bot is modular, configurable, and includes logging to track all activity.

## Features

- Connects securely to Binance Testnet using API keys

- Supports Market, Limit, Stop orders

- Logging of all order requests and results

- CLI-based execution (run via command line)

- Balance check method for account funds

## Project Structure

```bash
project/
│── trading_bot.py       
│── .env       
│── trading_bot.log    
│── requirements.txt 
│── README.md  

```

## Setup & Installation

- Clone Repo
```
git clone <your_repo_url>
cd project
```

- Install Requirements
```
pip install -r requirements.txt
```

- Set Environment Variables
  
Create a .env file (based on .env) and add your Binance Testnet API keys:
```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```
- Get keys from [Binance Futures Testnet](https://testnet.binancefuture.com/en/futures/BTCUSDT)

## Usage

Run the bot with desired order parameters:
```
python trading_bot.py --symbol BTCUSDT --side SELL --type STOP --quantity 0.001 --price 112900 --stop-price 11300
```
**Example: Market Order**
```
python trading_bot.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

**Example: Limit Order**
```
python trading_bot.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 27000
```

## Logs

All actions are logged in trading_bot.log, including:

- Order requests

- API responses

- Status updates
