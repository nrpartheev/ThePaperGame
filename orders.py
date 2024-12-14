import os
import pandas as pd
import requests
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import pytz

load_dotenv(dotenv_path=".env")


mongoDBURL = os.getenv("MONGODB_URL")
csvfile = os.getenv("CSV_FILE_PATH")

client = MongoClient(mongoDBURL)
db = client['PaperProfit']
users_collection = db['users']

symbols = pd.read_csv(csvfile, usecols=[0], names=["SYMBOL"]).dropna()

def live_price(stock):
    return requests.get(f'https://groww.in/v1/api/stocks_data/v1/tr_live_prices/exchange/NSE/segment/CASH/{stock}/latest').json()['ltp']

def is_market_open():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    if now.weekday() >= 0 and now.weekday() <= 4: 
        market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        return market_open <= now <= market_close
    return False

def process_order(order, client_name):
    try:
        if not is_market_open():
            return {"error": "Please trade only during market hours (9:00 AM to 3:30 PM IST)."}
        
        order_parts = order.split(' ')
        if len(order_parts) != 3:
            return {'error':'Wrong format'}

        order_type, stock, quantity = order_parts[0].upper(), order_parts[1].upper(), order_parts[2]
        quantity = int(quantity)

        if stock not in symbols['SYMBOL'].values:
            return {"error": f"Stock '{stock}' not found."}

        client_data = users_collection.find_one({"name": client_name})
        if not client_data:
            if order_type == "BUY":
                price = live_price(stock)
                cost = quantity * price
                if 100000 >= cost:
                    wallet_amount = round(100000 - cost, 2)
                    users_collection.insert_one({
                        "name": client_name,
                        "wallet_amount": wallet_amount,
                        "stocks": [{"stock": stock, "quantity": quantity}]
                    })
                    return {"success": f"Purchased {quantity} shares of {stock} each at {price} with a {cost}, Remaining Balance: {wallet_amount}"}
                else:
                    return {"error": "Insufficient funds"}
            else:
                return {"error": "No shares in your account"}
        else:
            if order_type == "BUY":
                wallet_amount = client_data['wallet_amount']
                price = live_price(stock)
                cost = quantity * price
                if wallet_amount >= cost:
                    wallet_amount = round(wallet_amount - cost, 2)
                    users_collection.update_one(
                        {"name": client_data['name'], "stocks.stock": stock},
                        {"$inc": {"stocks.$.quantity": quantity}, "$set": {"wallet_amount": wallet_amount}},
                        upsert=False
                    )
                    users_collection.update_one(
                        {"name": client_data['name'], "stocks.stock": {"$ne": stock}},
                        {"$set": {"wallet_amount": wallet_amount}, "$push": {"stocks": {"stock": stock, "quantity": quantity}}},
                        upsert=False
                    )
                    return {"success": f"Purchased {quantity} shares of {stock} each at {price} with a {cost}, Remaining Balance: {wallet_amount}"}
                else:
                    return {"error": "Insufficient funds"}
            else:
                quantity_available = next((item['quantity'] for item in client_data['stocks'] if item['stock'] == stock), 0)
                if quantity > quantity_available:
                    return {'error': "Can't sell what you don't have :("}
                else:
                    price = live_price(stock)
                    cost = quantity * price
                    wallet_amount = round(client_data["wallet_amount"] + cost)
                    users_collection.update_one(
                        {"name": client_data['name'], "stocks.stock": stock},
                        {"$inc": {"stocks.$.quantity": -quantity}, "$set": {"wallet_amount": wallet_amount}}
                    )
                    return {"success": f"Sold {quantity} shares of {stock} each at {price} with a {cost}, Balance: {wallet_amount}"}
    except Exception as e:
        return {"error": "Please ensure if you provided the correct format"}

def process_user(client_name):
    try:
        client_data = users_collection.find_one({"name": client_name})
        if not client_data:
            return {'error': 'No data found under this name'}
        else:
            stocks = client_data['stocks']
            table_comment = """
|  Stocks  | Quantity |
|----------|----------|
"""
            shareworth = 0
            for stock in stocks:
                shareworth += stock['quantity'] * live_price(stock['stock'])
                table_comment += f"| {stock['stock']} | {stock['quantity']} |\n"
            table_comment += f"| CASH-LEFT | {client_data['wallet_amount']} |\n"
            total_worth = shareworth + client_data['wallet_amount']
            table_comment += f"|  | Total: {total_worth} |\n"
            return table_comment
    except Exception as e:
        return {"error": str(e)}

