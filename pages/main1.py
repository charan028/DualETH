import streamlit as st
from dotenv import load_dotenv
import requests
import pymongo
import pandas as pd
import altair as alt
from web3 import Web3
from decimal import Decimal
import streamlit as st
import os
from collections.abc import MutableMapping
import streamlit as st
from auth import is_authenticated, logout
load_dotenv()
if not is_authenticated():
    st.warning("You must log in to access this page.")
    st.stop()  # Prevents execution of the dashboard
if st.button("Logout"):
    logout()
    st.rerun()

# ✅ Etherscan API & Web3 Setup
INFURA_URL = "https://sepolia.infura.io/v3/7b1bf99a4e7e4870940c7f799dff474e"
# ETHERSCAN_API_KEY = "7A4584DR7MY15Y44KCXB1M4Y9B77VRGR78"
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ✅ MongoDB Setup
MONGO_URI = "mongodb://localhost:27017"
client = pymongo.MongoClient(MONGO_URI)
db = client["ethereum_db"]
collection = db["transactions"]

# ✅ Ethereum Wallets
# ACCOUNT_A = "0xF5Ef9D9F28Dbb51A5CEFE286c1B7E1335b9eD9d8"
ACCOUNT_A=os.getenv("ACCOUNT_A")
ACCOUNT_B=os.getenv("ACCOUNT_B")
PRIVATE_KEY_A=os.getenv("PRIVATE_KEY_A")
PRIVATE_KEY_B=os.getenv("PRIVATE_KEY_B")

# ACCOUNT_B = "0x4aCD5757238cf023eB4712B074992BE383c388f0"
# PRIVATE_KEY_A = "c6dffa472133fd749620a96aa5df459aba27ad3e792d400f7d90841afb2e60ae"
# PRIVATE_KEY_B = "34484213dfd9037b98dd4abd06aee8a27c3a8309a0c7f0c22e48cb7aca8dd1cd"

# ✅ Contract Details
CONTRACT_ADDRESS=os.getenv("CONTRACT_ADDRESS")
# CONTRACT_ADDRESS = "0x9992f74F908C7768d3E76BEbC17c0246F65fE5ef"
ABI = [
	{
		"inputs": [],
		"name": "buyTokens",
		"outputs": [],
		"stateMutability": "payable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "amount",
				"type": "uint256"
			}
		],
		"name": "sellTokens",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_to",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "transfer",
		"outputs": [
			{
				"internalType": "bool",
				"name": "success",
				"type": "bool"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_initialSupply",
				"type": "uint256"
			}
		],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"internalType": "address",
				"name": "from",
				"type": "address"
			},
			{
				"indexed": True,
				"internalType": "address",
				"name": "to",
				"type": "address"
			},
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "value",
				"type": "uint256"
			}
		],
		"name": "Transfer",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "balanceOf",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "decimals",
		"outputs": [
			{
				"internalType": "uint8",
				"name": "",
				"type": "uint8"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getContractBalance",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "name",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "price",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "symbol",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "totalSupply",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]

# ✅ Initialize the Smart Contract
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# ✅ Helper Functions
def get_nonce(account):
    return w3.eth.get_transaction_count(account, 'pending')

def get_dynamic_gas_price():
    return int(w3.eth.gas_price * 1.1)  # 🚀 Lowered multiplier to prevent replacement errors

# ✅ Convert Decimal to Float (for MongoDB)
def convert_decimals_to_float(data):
    if isinstance(data, dict):
        return {k: convert_decimals_to_float(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_decimals_to_float(i) for i in data]
    elif isinstance(data, Decimal):
        return float(data)
    return data

# 🚀 **Fetch ETH Balance from Etherscan API**
@st.cache_data(ttl=30)  # Cache balance for 30 seconds
def get_eth_balance(address):
    url = f"https://api-sepolia.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url).json()
    return Web3.from_wei(int(response["result"]), "ether") if "result" in response else 0

# 🚀 **Function to Retry API Calls (Exponential Backoff)**
def safe_request(url, max_retries=5, delay=2):
    for i in range(max_retries):
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:  # Too Many Requests
            wait_time = delay * (2 ** i)
            print(f"⚠️ Rate limit hit. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            response.raise_for_status()
    raise Exception("🚨 Max retries reached.")

# 🚀 **Fetch Transaction History**
@st.cache_data(ttl=60)  # Cache transactions for 1 minute
def get_transactions(address):
    url = f"https://api-sepolia.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"
    response = safe_request(url)

    if "result" in response and isinstance(response["result"], list):
        return [
            {
                "Block": int(tx["blockNumber"]),
                "Hash": tx["hash"],
                "From": tx["from"],
                "To": tx["to"],
                "Value (ETH)": Web3.from_wei(int(tx["value"]), "ether"),
                "Gas (ETH)": Web3.from_wei(int(tx["gasPrice"]) * int(tx["gasUsed"]), "ether"),
                "Status": "Success" if tx["isError"] == "0" else "Failed"
            }
            for tx in response["result"]
        ]
    return []

# 🛒 **Buy Tokens with ETH (Account A)**
# 🛒 Buy Tokens with ETH (Account A)
# 🛒 Buy Tokens with ETH (Account A)
def buy_tokens():
    try:
        nonce = get_nonce(ACCOUNT_A)
        tx = contract.functions.buyTokens().build_transaction({
            'from': ACCOUNT_A,
            'value': w3.to_wei(0.0001, 'ether'),
            'gas': 150000,
            'gasPrice': get_dynamic_gas_price(),
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY_A)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)  # ✅ Fixed attribute

        return f"✅ Buy Transaction Sent! Hash: {tx_hash.hex()}"

    except Exception as e:
        error_message = str(e)
        if "insufficient funds for gas" in error_message:
            return "❌ Out of ETH to buy tokens!"
        else:
            return f"⚠️ Buy Transaction Failed: {error_message}"



# 🔄 **Transfer Tokens from A → B**
# 🔄 Transfer Tokens to Account B
# 🔄 Transfer Tokens from A → B
def transfer_tokens(amount):
    try:
        nonce = get_nonce(ACCOUNT_A)
        tx = contract.functions.transfer(ACCOUNT_B, amount).build_transaction({
            'from': ACCOUNT_A,
            'gas': 100000,
            'gasPrice': get_dynamic_gas_price(),
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY_A)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)  # ✅ Fixed attribute

        return f"✅ Tokens Sent to {ACCOUNT_B}! Hash: {tx_hash.hex()}"

    except Exception as e:
        error_message = str(e)
        if "insufficient funds for gas" in error_message:
            return "❌ Out of ETH to transfer tokens!"
        elif "execution reverted" in error_message:
            return "❌ Not enough tokens to transfer!"
        else:
            return f"⚠️ Transfer Transaction Failed: {error_message}"



# 💸 **Sell Tokens from Account B**# 💸 Sell Tokens from Account B & Get ETH
def sell_tokens(amount):
    try:
        nonce = get_nonce(ACCOUNT_B)
        tx = contract.functions.sellTokens(amount).build_transaction({
            'from': ACCOUNT_B,
            'gas': 150000,
            'gasPrice': get_dynamic_gas_price(),
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY_B)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)  # ✅ Fixed attribute

        return f"✅ Sell Transaction Sent! Hash: {tx_hash.hex()}"

    except Exception as e:
        error_message = str(e)
        if "insufficient funds for gas" in error_message:
            return "❌ Out of tokens or ETH to perform this transaction!"
        else:
            return f"⚠️ Sell Transaction Failed: {error_message}"

# ✅ **Streamlit UI**
st.title("📊 Ethereum Dual-Account Exchange")

eth_balance_a = get_eth_balance(ACCOUNT_A)
eth_balance_b = get_eth_balance(ACCOUNT_B)

st.write(f"🔹 **Account A Balance:** `{eth_balance_a:.6f} ETH`")
st.write(f"🔹 **Account B Balance:** `{eth_balance_b:.6f} ETH`")

# 🛒 Buy Tokens
if st.button("🛒 Buy Tokens"):
    st.success(buy_tokens())

# 🔄 Transfer Tokens
token_amount = st.number_input("🔄 Enter token amount to send:", min_value=1, step=1)
if st.button("🔄 Send Tokens"):
    st.success(transfer_tokens(token_amount))

# 💸 Sell Tokens
if st.button("💸 Sell Tokens"):
    st.success(sell_tokens(token_amount))
#✅ Load Transactions
transactions_a = get_transactions(ACCOUNT_A)
transactions_b = get_transactions(ACCOUNT_B)

# ✅ Merge & Sort Transactions
df_a = pd.DataFrame(transactions_a)
df_b = pd.DataFrame(transactions_b)
df_combined = pd.concat([df_a, df_b]).sort_values(by="Block")

# ✅ Convert Block Numbers to Integer
df_combined["Block"] = df_combined["Block"].astype(int)

st.subheader("📜 Transaction History (Both Accounts)")

# ✅ Fix Transaction Table Display
if not df_combined.empty:
    st.write(df_combined)  # Improved over st.dataframe()
else:
    st.warning("⚠️ No transactions found.")

# ✅ 📊 Improve Graph Readability
st.subheader("📈 ETH Transactions Over Time")

if not df_combined.empty:
    chart = (
        alt.Chart(df_combined)
        .mark_line(point=True)
        .encode(
            x=alt.X("Block:Q", title="Block Number", scale=alt.Scale(zero=False)), 
            y=alt.Y("Value (ETH):Q", title="ETH Transferred", scale=alt.Scale(zero=False)), 
            color="From:N",
            tooltip=["Block", "Value (ETH)", "From", "To"]
        )
        .properties(width=900, height=500, title="Ethereum Transactions Over Time")
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.warning("⚠️ No transactions available to display.")

# 🏆 **Ethereum Market Trends**
st.title("📊 Ethereum Market Trends")

# ✅ Function to fetch Ethereum market price and trends
# ✅ Function to fetch Ethereum market price and trends
# ✅ Function to fetch ETH market price safely
# ✅ Cache the ETH price for 5 minutes
@st.cache_data(ttl=300)
def get_eth_market_data():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd&include_24hr_change=true"
    
    try:
        response = requests.get(url).json()
        
        # Debugging: Print API response
        print("Coingecko API Response:", response)

        # Check for errors in API response
        if "status" in response and "error_code" in response["status"]:
            st.warning(f"⚠️ API Limit Exceeded: {response['status']['error_message']}")
            return "N/A", "N/A"

        # Validate response structure
        if isinstance(response, dict) and "ethereum" in response:
            eth_price = response["ethereum"].get("usd", 0)
            eth_change = response["ethereum"].get("usd_24h_change", 0)
            return eth_price, eth_change

    except Exception as e:
        st.error(f"🚨 API Error: {e}")
    
    return "N/A", "N/A"
eth_price, eth_change = get_eth_market_data()

# Convert to float only if values are numbers
eth_price_display = f"${float(eth_price):,.2f}" if isinstance(eth_price, (int, float)) else "N/A"
eth_change_display = f"{float(eth_change):.2f}%" if isinstance(eth_change, (int, float)) else "N/A"

st.metric(label="💰 Current ETH Price (USD)", value=eth_price_display, delta=eth_change_display)
@st.cache_data(ttl=60)  # Cache gas fees for 1 minute
def get_gas_fees():
    url = f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={ETHERSCAN_API_KEY}"
    
    try:
        response = requests.get(url).json()
        
        # Debugging: Print API response
        print("Etherscan Gas API Response:", response)

        # Check for rate limits
        if response.get("status") == "0":
            st.warning(f"⚠️ API Limit Exceeded: {response.get('message')}")
            return {"Low Gas": "N/A", "Average Gas": "N/A", "High Gas": "N/A"}

        # Validate response structure
        if "result" in response and isinstance(response["result"], dict):
            return {
                "Low Gas": response["result"].get("SafeGasPrice", "N/A"),
                "Average Gas": response["result"].get("ProposeGasPrice", "N/A"),
                "High Gas": response["result"].get("FastGasPrice", "N/A"),
            }

    except Exception as e:
        st.error(f"🚨 API Error: {e}")
    
    return {"Low Gas": "N/A", "Average Gas": "N/A", "High Gas": "N/A"}

# Fetch Ethereum price and trends
eth_price, eth_change = get_eth_market_data()
gas_fees = get_gas_fees()

# Display Ethereum price and percentage change
st.metric(label="💰 Current ETH Price (USD)", value=f"${eth_price:,.2f}", delta=f"{eth_change:.2f}%")

# Display gas fee trends
if gas_fees:
    st.subheader("⛽ Current Ethereum Gas Fees")
    col1, col2, col3 = st.columns(3)
    col1.metric(label="🟢 Low Gas", value=f"{gas_fees['Low Gas']} Gwei")
    col2.metric(label="🟡 Average Gas", value=f"{gas_fees['Average Gas']} Gwei")
    col3.metric(label="🔴 High Gas", value=f"{gas_fees['High Gas']} Gwei")

import requests
import pandas as pd
import altair as alt
import streamlit as st

# 📈 **Fetch ETH price data for the last 2 days (to get hourly intervals)**
@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_eth_price_history():
    url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=2"

    try:
        response = requests.get(url).json()

        # Debugging: Print API response
        print("Coingecko ETH Price History Response:", response)

        # Check if API returned an error (e.g., rate limit)
        if "status" in response and "error_code" in response["status"]:
            st.warning(f"⚠️ API Limit Exceeded: {response['status']['error_message']}")
            return pd.DataFrame()

        # Validate response structure
        if "prices" in response:
            prices = response["prices"]
            df = pd.DataFrame(prices, columns=["Timestamp", "Price"])
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms")

            # Filter last 24 hours of data
            last_24h = df[df["Timestamp"] >= (pd.Timestamp.now() - pd.Timedelta(hours=24))]
            return last_24h

    except Exception as e:
        st.error(f"🚨 API Error: {e}")

    return pd.DataFrame()  # Return an empty DataFrame on error

# ✅ **Load ETH price history**
df_eth_trend = get_eth_price_history()

# ✅ **Display ETH Price Trend Graph (Interactive)**
st.subheader("📈 ETH Price Trend (Last 24 Hours)")

if not df_eth_trend.empty:
    chart = (
        alt.Chart(df_eth_trend)
        .mark_line(point=True)  # Adds points for better readability
        .encode(
            x=alt.X("Timestamp:T", title="Time"),
            y=alt.Y("Price:Q", title="ETH Price (USD)"),
            tooltip=["Timestamp:T", "Price:Q"],
        )
        .properties(
            width=800,
            height=400,
            title="Ethereum Price Trend (24H)"
        )
    )

    st.altair_chart(chart, use_container_width=True)
else:
    st.warning("⚠️ Unable to fetch ETH price history. API limit may be reached.")
