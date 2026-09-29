"""
Setup fresh demo FinancialContractV2 on MST Testnet for ₹1,00,000 + ₹14,000 ACTUS Plan.

Steps performed:
1. Compiles FinancialContractV2 Solidity contract.
2. Deploys contract with Total Expected Repayment = ₹1,14,000 (11,400,000 units).
3. Activates the contract (Status -> ACTIVE).
4. Records initial principal payment of ₹1,00,000 (10,000,000 units).
   --> Result: Total Paid = ₹1,00,000 | Pending = ₹14,000 | Status = ACTIVE.
5. Updates .env with the new MST_CONTRACT_ADDRESS.
"""

import os
import sys
import time
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

import solcx
from web3 import Web3

RPC_URL = os.environ.get("MST_RPC_URL", "https://testnetrpc.mstblockchain.com")
CHAIN_ID = int(os.environ.get("MST_CHAIN_ID", "91562037"))
PRIVATE_KEY = os.environ.get("MST_PRIVATE_KEY", "")

if not PRIVATE_KEY:
    print("ERROR: MST_PRIVATE_KEY is missing in .env")
    sys.exit(1)

print(f"Connecting to MST Testnet: {RPC_URL}...")
w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
account = w3.eth.account.from_key(PRIVATE_KEY)
wallet = account.address
print(f"Connected! Wallet: {wallet} | Balance: {w3.from_wei(w3.eth.get_balance(wallet), 'ether')} MST")

# 1. Compile contract
print("Compiling FinancialContractV2.sol...")
contract_source_path = Path(__file__).resolve().parent.parent / "v2-contract.txt"
try:
    contract_source = contract_source_path.read_text(encoding="utf-16")
except Exception:
    contract_source = contract_source_path.read_text(encoding="utf-8")

compiled = solcx.compile_source(
    contract_source,
    output_values=["abi", "bin"],
    solc_version="0.8.28"
)
contract_id, contract_interface = compiled.popitem()
abi = contract_interface["abi"]
bytecode = contract_interface["bin"]

# 2. Prepare constructor parameters
# Total principal/target: ₹1,14,000 (114000.00 -> 11400000 units)
principal_units = 11_400_000
interest_rate_bps = 1400  # 14.00%
maturity_date = int(time.time()) + (365 * 24 * 3600)  # 1 year from now
actus_hash = Web3.keccak(text="ACTUS_PAM_100K_14K_LOAN_CONTRACT_SCHEDULE")

print(f"\nDeploying FinancialContractV2...")
print(f"  Borrower: {wallet}")
print(f"  Total Repayment Target: Rs 1,14,000.00 ({principal_units} units)")
print(f"  Interest: 14.00% ({interest_rate_bps} bps)")

contract_factory = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(wallet)

construct_tx = contract_factory.constructor(
    wallet,
    principal_units,
    interest_rate_bps,
    maturity_date,
    actus_hash
).build_transaction({
    "from": wallet,
    "nonce": nonce,
    "gas": 1_500_000,
    "gasPrice": w3.to_wei("1", "gwei"),
    "chainId": CHAIN_ID,
})

signed_tx = w3.eth.account.sign_transaction(construct_tx, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print(f"Deployment TX broadcast: {tx_hash.hex()}")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

new_contract_address = receipt.contractAddress
print(f"Contract DEPLOYED at: {new_contract_address}")
print(f"Explorer link: https://testnet.mstscan.com/address/{new_contract_address}")

contract_instance = w3.eth.contract(address=new_contract_address, abi=abi)

# 3. Activate contract
print("\nActivating contract...")
nonce = w3.eth.get_transaction_count(wallet)
activate_tx = contract_instance.functions.activateContract().build_transaction({
    "from": wallet,
    "nonce": nonce,
    "gas": 200_000,
    "gasPrice": w3.to_wei("1", "gwei"),
    "chainId": CHAIN_ID,
})
signed_activate = w3.eth.account.sign_transaction(activate_tx, private_key=PRIVATE_KEY)
act_hash = w3.eth.send_raw_transaction(signed_activate.raw_transaction)
w3.eth.wait_for_transaction_receipt(act_hash, timeout=120)
print("Contract ACTIVATED! Status = ACTIVE")

# 4. Record initial Rs 1,00,000 payment
print("\nRecording initial Rs 1,00,000 payment (10,000,000 units)...")
initial_payment = 10_000_000
nonce = w3.eth.get_transaction_count(wallet)
pay_tx = contract_instance.functions.recordPayment(initial_payment).build_transaction({
    "from": wallet,
    "nonce": nonce,
    "gas": 200_000,
    "gasPrice": w3.to_wei("1", "gwei"),
    "chainId": CHAIN_ID,
})
signed_pay = w3.eth.account.sign_transaction(pay_tx, private_key=PRIVATE_KEY)
pay_hash = w3.eth.send_raw_transaction(signed_pay.raw_transaction)
w3.eth.wait_for_transaction_receipt(pay_hash, timeout=120)

total_paid = contract_instance.functions.totalPaid().call()
status_val = contract_instance.functions.status().call()
status_str = {0: "CREATED", 1: "ACTIVE", 2: "COMPLETED", 3: "DELINQUENT"}.get(status_val, str(status_val))

print(f"\n================ DEMO READY STATE ================")
print(f"Contract Address: {new_contract_address}")
print(f"Total Repayment Target: Rs 1,14,000.00")
print(f"Total Paid So Far:      Rs {Decimal(total_paid)/100:,.2f}")
print(f"Pending Remaining:      Rs 14,000.00")
print(f"Contract Status:        {status_str}")
print(f"MSTScan Explorer:       https://testnet.mstscan.com/address/{new_contract_address}")
print(f"===================================================")

# 5. Update .env
env_lines = env_file.read_text(encoding="utf-8").splitlines()
new_lines = []
for line in env_lines:
    if line.startswith("MST_CONTRACT_ADDRESS="):
        new_lines.append(f"MST_CONTRACT_ADDRESS={new_contract_address}")
    else:
        new_lines.append(line)

env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print("\nUpdated .env with MST_CONTRACT_ADDRESS.")
