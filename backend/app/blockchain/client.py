"""Client abstraction layer for interacting with MST Blockchain via Web3 RPC."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Any
from web3 import Web3
from web3.exceptions import Web3Exception

from app.blockchain.abi import FINANCIAL_CONTRACT_V2_ABI
from app.blockchain.exceptions import (
    BlockchainNotConfiguredError,
    BlockchainRPCError,
    BlockchainWrongChainError,
    ContractNotFoundError,
    EventQueryFailedError,
    InvalidContractAddressError,
)
from app.blockchain.models import ActualPayment, BlockchainContractState, BlockchainStatus
from app.blockchain.utils import bytes32_to_sha256, contract_units_to_decimal
from app.core.config import settings


class MSTBlockchainClient:
    """Client wrapper for querying on-chain FinancialContractV2 state and event logs on MST Blockchain."""

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        chain_id: Optional[int] = None,
    ) -> None:
        self.rpc_url = rpc_url if rpc_url is not None else settings.MST_RPC_URL
        self.expected_chain_id = chain_id if chain_id is not None else settings.MST_CHAIN_ID
        self._w3: Optional[Web3] = None


    def _get_w3(self) -> Web3:
        """Lazy initialization and validation of Web3 HTTP provider."""
        if not self.rpc_url or not self.rpc_url.strip():
            raise BlockchainNotConfiguredError("MST RPC URL is missing or empty in configuration.")

        if self._w3 is None:
            try:
                self._w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 10}))
            except Exception as exc:
                raise BlockchainRPCError(f"Failed to initialize Web3 provider for '{self.rpc_url}': {str(exc)}") from exc
        return self._w3

    def check_connection(self) -> Tuple[bool, int]:
        """Check connection to MST RPC endpoint and verify chain ID."""
        w3 = self._get_w3()
        try:
            is_connected = w3.is_connected()
        except Exception as exc:
            raise BlockchainRPCError(f"Failed to connect to MST RPC node at '{self.rpc_url}': {str(exc)}") from exc

        if not is_connected:
            raise BlockchainRPCError(f"MST RPC node at '{self.rpc_url}' is un-reachable.")

        try:
            actual_chain_id = w3.eth.chain_id
        except Exception as exc:
            raise BlockchainRPCError(f"Failed to query chain ID from MST RPC node: {str(exc)}") from exc

        if self.expected_chain_id and actual_chain_id != self.expected_chain_id:
            raise BlockchainWrongChainError(
                expected_chain_id=self.expected_chain_id,
                actual_chain_id=actual_chain_id,
            )

        return True, actual_chain_id

    def validate_address(self, address: str) -> str:
        """Validate EVM address format and return checksummed address."""
        if not address or not isinstance(address, str):
            raise InvalidContractAddressError(str(address))
        clean_addr = address.strip()
        if not Web3.is_address(clean_addr):
            raise InvalidContractAddressError(clean_addr)
        return Web3.to_checksum_address(clean_addr)

    def get_contract_state(self, contract_address: str) -> BlockchainContractState:
        """Query on-chain FinancialContractV2 state details by contract address."""
        checksum_addr = self.validate_address(contract_address)
        w3 = self._get_w3()

        # Check code at address
        try:
            code = w3.eth.get_code(checksum_addr)
        except Exception as exc:
            raise BlockchainRPCError(f"Failed to query contract bytecode at address '{checksum_addr}': {str(exc)}") from exc

        if not code or code == b"" or code == bytes.fromhex(""):
            raise ContractNotFoundError(checksum_addr)

        contract = w3.eth.contract(address=checksum_addr, abi=FINANCIAL_CONTRACT_V2_ABI)

        try:
            details = contract.functions.getContractDetails().call()
            lender, borrower, principal_units, interest_bps, maturity_ts, actus_h, status_uint, total_paid_units = details
        except Exception as exc:
            raise BlockchainRPCError(f"Failed to call getContractDetails() on contract '{checksum_addr}': {str(exc)}") from exc

        # Convert values
        principal_dec = contract_units_to_decimal(principal_units)
        total_paid_dec = contract_units_to_decimal(total_paid_units)
        maturity_dt = datetime.fromtimestamp(maturity_ts, tz=timezone.utc)
        actus_sha256 = bytes32_to_sha256(actus_h)
        status_enum = BlockchainStatus.from_solidity_uint(status_uint)

        return BlockchainContractState(
            contract_address=checksum_addr,
            lender=Web3.to_checksum_address(lender),
            borrower=Web3.to_checksum_address(borrower),
            principal=principal_dec,
            interest_rate_bps=int(interest_bps),
            maturity_date=maturity_dt,
            actus_hash=actus_sha256,
            status=status_enum,
            total_paid=total_paid_dec,
            chain_id=self.expected_chain_id or w3.eth.chain_id,
        )

    def get_payment_events(self, contract_address: str) -> List[ActualPayment]:
        """Query PaymentRecorded event logs for a given FinancialContractV2 contract address."""
        checksum_addr = self.validate_address(contract_address)
        w3 = self._get_w3()

        contract = w3.eth.contract(address=checksum_addr, abi=FINANCIAL_CONTRACT_V2_ABI)

        try:
            event_filter = contract.events.PaymentRecorded.create_filter(from_block=0, to_block="latest")
            events = event_filter.get_all_entries()
        except Exception as exc:
            # Fallback using get_logs if filter fails
            try:
                event_template = contract.events.PaymentRecorded()
                events = event_template.get_logs(from_block=0, to_block="latest")
            except Exception as inner_exc:
                raise EventQueryFailedError(f"Failed to query PaymentRecorded events for '{checksum_addr}': {str(exc)} / {str(inner_exc)}") from inner_exc

        actual_payments: List[ActualPayment] = []
        for ev in events:
            tx_hash = ev.get("transactionHash", b"").hex() if isinstance(ev.get("transactionHash"), bytes) else str(ev.get("transactionHash", ""))
            if tx_hash and not tx_hash.startswith("0x"):
                tx_hash = f"0x{tx_hash}"

            block_num = int(ev.get("blockNumber", 0))
            log_idx = int(ev.get("logIndex", 0))
            args = ev.get("args", {})

            amount_units = int(args.get("amount", 0))
            payment_ts = int(args.get("paymentDate", 0))
            total_paid_units = int(args.get("totalPaid", 0))

            amount_dec = contract_units_to_decimal(amount_units)
            total_paid_dec = contract_units_to_decimal(total_paid_units)

            # Convert payment date timestamp
            if payment_ts > 0:
                payment_dt = datetime.fromtimestamp(payment_ts, tz=timezone.utc)
            else:
                # Fallback to block timestamp if paymentDate arg is 0
                try:
                    block = w3.eth.get_block(block_num)
                    payment_dt = datetime.fromtimestamp(block["timestamp"], tz=timezone.utc)
                except Exception:
                    payment_dt = datetime.now(timezone.utc)

            actual_payments.append(
                ActualPayment(
                    transaction_hash=tx_hash,
                    block_number=block_num,
                    log_index=log_idx,
                    amount=amount_dec,
                    payment_date=payment_dt,
                    cumulative_total_paid=total_paid_dec,
                )
            )

        # Deterministic sorting by payment_date, then block_number, then log_index
        actual_payments.sort(key=lambda p: (p.payment_date, p.block_number, p.log_index))
        return actual_payments

    def record_payment(
        self,
        contract_address: Optional[str] = None,
        amount_inr: Decimal = Decimal("4614.49"),
        private_key: Optional[str] = None,
    ) -> dict:
        """Execute a real recordPayment transaction on MST Blockchain."""
        addr = contract_address or settings.MST_CONTRACT_ADDRESS
        if not addr:
            raise BlockchainNotConfiguredError("Contract address is missing.")
        priv_key = private_key or settings.MST_PRIVATE_KEY
        if not priv_key:
            raise BlockchainNotConfiguredError("MST_PRIVATE_KEY is missing.")

        checksum_addr = self.validate_address(addr)
        w3 = self._get_w3()
        account = w3.eth.account.from_key(priv_key)
        wallet = account.address
        amount_units = int(amount_inr * 100)

        contract = w3.eth.contract(address=checksum_addr, abi=FINANCIAL_CONTRACT_V2_ABI)
        nonce = w3.eth.get_transaction_count(wallet)
        chain_id = self.expected_chain_id or w3.eth.chain_id

        tx = contract.functions.recordPayment(amount_units).build_transaction({
            "from": wallet,
            "nonce": nonce,
            "gas": 200_000,
            "gasPrice": w3.to_wei("1", "gwei"),
            "chainId": chain_id,
        })
        signed = w3.eth.account.sign_transaction(tx, private_key=priv_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        tx_hex = tx_hash.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = f"0x{tx_hex}"

        return {
            "status": "SUCCESS" if receipt["status"] == 1 else "FAILED",
            "transaction_hash": tx_hex,
            "block_number": int(receipt["blockNumber"]),
            "contract_address": checksum_addr,
            "amount": float(amount_inr),
            "explorer_url": f"https://testnet.mstscan.com/tx/{tx_hex}",
        }


# Global client instance
blockchain_client = MSTBlockchainClient()

