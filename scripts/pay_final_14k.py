"""
Pay remaining ₹14,000 (1,400,000 units) on MST Testnet live before the mentor.

Usage:
    python scripts/pay_final_14k.py
"""

import os
import sys
from decimal import Decimal
from pathlib import Path

# Load .env
env_file = Path(__file__).resolve().parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"'))

from web3 import Web3

RPC_URL = os.environ.get("MST_RPC_URL", "https://testnetrpc.mstblockchain.com")
CHAIN_ID = int(os.environ.get("MST_CHAIN_ID", "91562037"))
PRIVATE_KEY = os.environ.get("MST_PRIVATE_KEY", "")
CONTRACT_ADDRESS = os.environ.get("MST_CONTRACT_ADDRESS", "")

if not PRIVATE_KEY or not CONTRACT_ADDRESS:
    print("ERROR: Missing MST_PRIVATE_KEY or MST_CONTRACT_ADDRESS in .env")
    sys.exit(1)

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
    {
        "inputs": [],
        "name": "getContractDetails",
        "outputs": [
            {"internalType": "address", "name": "_lender", "type": "address"},
            {"internalType": "address", "name": "_borrower", "type": "address"},
            {"internalType": "uint256", "name": "_principal", "type": "uint256"},
            {"internalType": "uint256", "name": "_interestRateBps", "type": "uint256"},
            {"internalType": "uint256", "name": "_maturityDate", "type": "uint256"},
            {"internalType": "bytes32", "name": "_actusHash", "type": "bytes32"},
            {"internalType": "uint8", "name": "_status", "type": "uint8"},
            {"internalType": "uint256", "name": "_totalPaid", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
account = w3.eth.account.from_key(PRIVATE_KEY)
wallet = account.address

checksum_addr = Web3.to_checksum_address(CONTRACT_ADDRESS)
contract = w3.eth.contract(address=checksum_addr, abi=ABI)

# Read current state
details = contract.functions.getContractDetails().call()
target_total = details[2]
status_before = details[6]
total_paid_before = details[7]

status_map = {0: "CREATED", 1: "ACTIVE", 2: "COMPLETED", 3: "DELINQUENT"}

print("=" * 60)
print("🚀 LIVE PAYMENT EXECUTION ON MST BLOCKCHAIN")
print("=" * 60)
print(f"Contract:      {checksum_addr}")
print(f"Target Total:  Rs {Decimal(target_total)/100:,.2f}")
print(f"Current Paid:  Rs {Decimal(total_paid_before)/100:,.2f}")
print(f"Pending Due:   Rs {Decimal(target_total - total_paid_before)/100:,.2f}")
print(f"Status Before: {status_map.get(status_before, str(status_before))}")
print("-" * 60)

# Payment of remaining amount (₹14,000 = 1,400,000 units)
remaining_units = target_total - total_paid_before
if remaining_units <= 0:
    print("Contract is already fully paid and completed!")
    sys.exit(0)

print(f"Broadcasting transaction: Paying final Rs {Decimal(remaining_units)/100:,.2f}...")

nonce = w3.eth.get_transaction_count(wallet)
tx = contract.functions.recordPayment(remaining_units).build_transaction({
    "from": wallet,
    "nonce": nonce,
    "gas": 200_000,
    "gasPrice": w3.to_wei("1", "gwei"),
    "chainId": CHAIN_ID,
})

signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

print(f"Transaction Hash: {tx_hash.hex()}")
print("Waiting for MST Blockchain block confirmation...")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

if receipt["status"] == 1:
    details_after = contract.functions.getContractDetails().call()
    status_after = details_after[6]
    total_paid_after = details_after[7]
    
    print("\n✅ TRANSACTION SUCCESSFUL & CONFIRMED ON-CHAIN!")
    print(f"Block Number:   {receipt['blockNumber']}")
    print(f"Total Paid:     Rs {Decimal(total_paid_after)/100:,.2f} / Rs {Decimal(target_total)/100:,.2f}")
    print(f"Status After:   {status_map.get(status_after, str(status_after))} 🟢")
    print(f"\n🔗 View on MSTScan Live:")
    print(f"👉 https://testnet.mstscan.com/tx/{tx_hash.hex()}")
    print("=" * 60)
else:
    print(f"❌ Transaction reverted: {receipt}")
    sys.exit(1)
