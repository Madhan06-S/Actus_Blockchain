"""
Record a payment on MST Testnet.

Usage:
    python scripts/record_payment.py

Set these in your .env file before running:
    MST_PRIVATE_KEY=0x...your private key...
    MST_CONTRACT_ADDRESS=0x89dbdf7AB208496f3527e97a5434e4eB34c76168
    MST_PAYMENT_AMOUNT=4614.49       (optional, defaults to 4614.49)
"""

import os
import sys
from decimal import Decimal
from pathlib import Path

# Load .env manually (no external lib needed)
env_file = Path(__file__).resolve().parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"'))

from web3 import Web3

# ── Configuration ──────────────────────────────────────────────────────────────
RPC_URL            = os.environ.get("MST_RPC_URL", "https://testnetrpc.mstblockchain.com")
CHAIN_ID           = int(os.environ.get("MST_CHAIN_ID", "91562037"))
PRIVATE_KEY        = os.environ.get("MST_PRIVATE_KEY", "")
CONTRACT_ADDRESS   = os.environ.get("MST_CONTRACT_ADDRESS", "")

# Amount in INR (e.g. 4614.49 for a monthly installment)
# Contract stores amounts as uint256 * 100 (2 decimal precision)
PAYMENT_AMOUNT_INR = Decimal(os.environ.get("MST_PAYMENT_AMOUNT", "4614.49"))

# ── Validate ───────────────────────────────────────────────────────────────────
if not PRIVATE_KEY:
    print("ERROR: MST_PRIVATE_KEY is not set in .env")
    print("  Add: MST_PRIVATE_KEY=0x<your-private-key>")
    sys.exit(1)

if not CONTRACT_ADDRESS:
    print("ERROR: MST_CONTRACT_ADDRESS is not set in .env")
    print("  Add: MST_CONTRACT_ADDRESS=0x89dbdf7AB208496f3527e97a5434e4eB34c76168")
    sys.exit(1)

# ── Minimal ABI (only what we need) ──────────────────────────────────────────
ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}],
        "name": "recordPayment",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalPaid",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "status",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# ── Connect ────────────────────────────────────────────────────────────────────
print(f"Connecting to MST Testnet: {RPC_URL}")
w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))

if not w3.is_connected():
    print("ERROR: Cannot connect to MST RPC. Check your internet / RPC URL.")
    sys.exit(1)

chain_id = w3.eth.chain_id
print(f"Connected. Chain ID: {chain_id}")

# ── Wallet ─────────────────────────────────────────────────────────────────────
account = w3.eth.account.from_key(PRIVATE_KEY)
wallet  = account.address
balance = w3.eth.get_balance(wallet)
print(f"Wallet:  {wallet}")
print(f"Balance: {w3.from_wei(balance, 'ether')} ETH")

# ── Contract ───────────────────────────────────────────────────────────────────
checksum_addr = Web3.to_checksum_address(CONTRACT_ADDRESS)
contract = w3.eth.contract(address=checksum_addr, abi=ABI)

try:
    status_uint = contract.functions.status().call()
    status_map  = {0: "CREATED", 1: "ACTIVE", 2: "COMPLETED", 3: "DELINQUENT"}
    print(f"Contract status: {status_map.get(status_uint, str(status_uint))}")
    total_paid  = contract.functions.totalPaid().call()
    print(f"Total paid so far: Rs {Decimal(total_paid) / 100:.2f}")
except Exception as e:
    print(f"Warning - could not read contract state: {e}")

# ── Build & send transaction ───────────────────────────────────────────────────
amount_units = int(PAYMENT_AMOUNT_INR * 100)
print(f"\nRecording payment of Rs {PAYMENT_AMOUNT_INR} ({amount_units} units)...")

nonce = w3.eth.get_transaction_count(wallet)

try:
    tx = contract.functions.recordPayment(amount_units).build_transaction({
        "from":     wallet,
        "nonce":    nonce,
        "gas":      200_000,
        "gasPrice": w3.to_wei("1", "gwei"),
        "chainId":  chain_id,
    })
except Exception as e:
    print(f"ERROR: Failed to build transaction: {e}")
    sys.exit(1)

signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)

try:
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Sent! TX Hash: {tx_hash.hex()}")
    print("Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt["status"] == 1:
        print(f"SUCCESS - Payment confirmed in block {receipt['blockNumber']}")
        print(f"TX: https://testnet.mstscan.com/tx/{tx_hash.hex()}")
        total_paid_after = contract.functions.totalPaid().call()
        print(f"Updated total paid: Rs {Decimal(total_paid_after) / 100:.2f}")
    else:
        print(f"FAILED - Transaction reverted. Receipt: {receipt}")
        sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
