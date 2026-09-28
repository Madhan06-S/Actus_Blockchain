"""Custom exception definitions for blockchain operations and error handling."""


class BlockchainError(Exception):
    """Base exception class for all blockchain integration errors."""

    def __init__(self, message: str, code: str = "BLOCKCHAIN_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class BlockchainNotConfiguredError(BlockchainError):
    """Raised when blockchain RPC configuration is missing or incomplete."""

    def __init__(self, message: str = "Blockchain RPC is not configured.") -> None:
        super().__init__(message, code="BLOCKCHAIN_NOT_CONFIGURED")


class BlockchainRPCError(BlockchainError):
    """Raised when communication with MST RPC fails or times out."""

    def __init__(self, message: str = "Failed to communicate with MST RPC node.") -> None:
        super().__init__(message, code="BLOCKCHAIN_RPC_UNAVAILABLE")


class BlockchainWrongChainError(BlockchainError):
    """Raised when connected network chain ID does not match expected MST chain ID."""

    def __init__(self, expected_chain_id: int, actual_chain_id: int) -> None:
        message = f"Connected chain ID {actual_chain_id} does not match expected MST chain ID {expected_chain_id}."
        super().__init__(message, code="BLOCKCHAIN_WRONG_CHAIN")


class ContractNotFoundError(BlockchainError):
    """Raised when no contract bytecode or state exists at the specified address."""

    def __init__(self, address: str) -> None:
        super().__init__(f"No contract found at address '{address}'.", code="CONTRACT_NOT_FOUND")


class InvalidContractAddressError(BlockchainError):
    """Raised when a contract address string is malformed or invalid."""

    def __init__(self, address: str) -> None:
        super().__init__(f"Invalid EVM contract address format '{address}'.", code="INVALID_CONTRACT_ADDRESS")


class InvalidActusHashError(BlockchainError):
    """Raised when an ACTUS hash string or bytes32 conversion is invalid."""

    def __init__(self, message: str = "Invalid ACTUS hash format.") -> None:
        super().__init__(message, code="INVALID_ACTUS_HASH")


class ContractNotLinkedError(BlockchainError):
    """Raised when a FinancialContract ID has not been linked to an on-chain address."""

    def __init__(self, contract_id: str) -> None:
        super().__init__(f"FinancialContract ID '{contract_id}' is not linked to a blockchain contract address.", code="CONTRACT_NOT_LINKED")


class EventQueryFailedError(BlockchainError):
    """Raised when querying PaymentRecorded events fails."""

    def __init__(self, message: str = "Failed to query payment events from blockchain.") -> None:
        super().__init__(message, code="EVENT_QUERY_FAILED")
