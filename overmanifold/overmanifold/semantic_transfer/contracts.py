"""
Custom Network Smart Contract System in Python
Smart contracts for the semantic value transfer network
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import hashlib
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
import copy

from protocol import (
    SemanticValue, TransferPayload, TransferChannel, SemanticType,
    SemanticTransferSyntax
)

class ContractState(Enum):
    """Smart contract states"""
    DEPLOYED = "deployed"
    ACTIVE = "active"
    PAUSED = "paused"
    TERMINATED = "terminated"

class ContractType(Enum):
    """Types of smart contracts"""
    TOKEN = "token"
    PAYMENT = "payment"
    ESCROW = "escrow"
    MULTI_SIG = "multi_sig"
    SUBSCRIPTION = "subscription"
    REWARD = "reward"
    GOVERNANCE = "governance"
    ORACLE = "oracle"

@dataclass
class ContractCall:
    """Smart contract call structure"""
    contract_address: str
    function_name: str
    parameters: Dict[str, Any]
    caller: str
    gas_limit: int = 21000
    gas_price: float = 0.00001
    nonce: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_address": self.contract_address,
            "function_name": self.function_name,
            "parameters": self.parameters,
            "caller": self.caller,
            "gas_limit": self.gas_limit,
            "gas_price": self.gas_price,
            "nonce": self.nonce,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class ContractResult:
    """Smart contract execution result"""
    success: bool
    return_value: Any
    gas_used: int
    events: List[Dict[str, Any]]
    error_message: str = ""
    state_changes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "return_value": self.return_value,
            "gas_used": self.gas_used,
            "events": self.events,
            "error_message": self.error_message,
            "state_changes": self.state_changes
        }

class SmartContract:
    """Base smart contract class"""
    
    def __init__(self, address: str, contract_type: ContractType, creator: str):
        self.address = address
        self.contract_type = contract_type
        self.creator = creator
        self.state = ContractState.DEPLOYED
        self.storage: Dict[str, Any] = {}
        self.code_hash = self._calculate_code_hash()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Initialize default storage
        self._initialize_storage()
    
    def _calculate_code_hash(self) -> str:
        """Calculate hash of contract code"""
        code = f"{self.__class__.__name__}{self.__class__.__module__}"
        return hashlib.sha256(code.encode()).hexdigest()
    
    def _initialize_storage(self):
        """Initialize contract storage"""
        self.storage["owner"] = self.creator
        self.storage["balances"] = {}
        self.storage["allowances"] = {}
        self.storage["total_supply"] = Decimal("0")
        self.storage["nonce"] = 0
    
    def execute(self, call: ContractCall) -> ContractResult:
        """Execute contract call"""
        if self.state != ContractState.ACTIVE:
            return ContractResult(
                success=False,
                return_value=None,
                gas_used=0,
                events=[],
                error_message=f"Contract not active. Current state: {self.state.value}"
            )
        
        # Check if function exists
        if not hasattr(self, call.function_name):
            return ContractResult(
                success=False,
                return_value=None,
                gas_used=0,
                events=[],
                error_message=f"Function {call.function_name} not found"
            )
        
        # Execute function
        try:
            function = getattr(self, call.function_name)
            result = function(**call.parameters)
            
            self.updated_at = datetime.utcnow()
            self.storage["nonce"] += 1
            
            return ContractResult(
                success=True,
                return_value=result,
                gas_used=call.gas_limit,
                events=self._generate_events(call.function_name, call.parameters, result),
                state_changes={"nonce": self.storage["nonce"]}
            )
        except Exception as e:
            return ContractResult(
                success=False,
                return_value=None,
                gas_used=0,
                events=[],
                error_message=str(e)
            )
    
    def _generate_events(self, function_name: str, parameters: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Generate events for contract execution"""
        return [{
            "event_type": f"{self.__class__.__name__}.{function_name}",
            "contract_address": self.address,
            "timestamp": datetime.utcnow().isoformat(),
            "parameters": parameters,
            "result": result
        }]
    
    def get_storage(self, key: str) -> Any:
        """Get value from contract storage"""
        return self.storage.get(key)
    
    def set_storage(self, key: str, value: Any):
        """Set value in contract storage"""
        self.storage[key] = value
        self.updated_at = datetime.utcnow()

class TokenContract(SmartContract):
    """ERC20-like token contract"""
    
    def __init__(self, address: str, creator: str, name: str, symbol: str, initial_supply: Decimal):
        super().__init__(address, ContractType.TOKEN, creator)
        self.storage["name"] = name
        self.storage["symbol"] = symbol
        self.storage["decimals"] = 18
        self.storage["total_supply"] = initial_supply
        self.storage["balances"][creator] = initial_supply
    
    def transfer(self, to: str, amount: Decimal) -> bool:
        """Transfer tokens"""
        from_balance = self.storage["balances"].get(self.storage["owner"], Decimal("0"))
        
        if from_balance < amount:
            raise ValueError("Insufficient balance")
        
        self.storage["balances"][self.storage["owner"]] = from_balance - amount
        self.storage["balances"][to] = self.storage["balances"].get(to, Decimal("0")) + amount
        
        return True
    
    def balance_of(self, account: str) -> Decimal:
        """Get balance of account"""
        return self.storage["balances"].get(account, Decimal("0"))
    
    def approve(self, spender: str, amount: Decimal) -> bool:
        """Approve spender to spend tokens"""
        self.storage["allowances"][self.storage["owner"]] = {
            spender: amount
        }
        return True
    
    def transfer_from(self, from_: str, to: str, amount: Decimal) -> bool:
        """Transfer tokens from one account to another"""
        from_balance = self.storage["balances"].get(from_, Decimal("0"))
        
        if from_balance < amount:
            raise ValueError("Insufficient balance")
        
        allowance = self.storage["allowances"].get(from_, {}).get(self.storage["owner"], Decimal("0"))
        if allowance < amount:
            raise ValueError("Insufficient allowance")
        
        self.storage["balances"][from_] = from_balance - amount
        self.storage["balances"][to] = self.storage["balances"].get(to, Decimal("0")) + amount
        self.storage["allowances"][from_][self.storage["owner"]] = allowance - amount
        
        return True

class PaymentContract(SmartContract):
    """Payment processing contract"""
    
    def __init__(self, address: str, creator: str, token_contract: str):
        super().__init__(address, ContractType.PAYMENT, creator)
        self.storage["token_contract"] = token_contract
        self.storage["payment_count"] = 0
        self.storage["total_volume"] = Decimal("0")
    
    def process_payment(self, payload: TransferPayload) -> bool:
        """Process semantic payment"""
        # Validate payload
        if payload.semantic_value.amount <= 0:
            raise ValueError("Invalid amount")
        
        # Check expiry
        if payload.semantic_value.expires_at and payload.semantic_value.expires_at < datetime.utcnow():
            raise ValueError("Payment expired")
        
        # Process payment
        self.storage["payment_count"] += 1
        self.storage["total_volume"] += Decimal(str(payload.semantic_value.amount))
        
        # Store payment record
        payment_id = f"payment_{self.storage['payment_count']}"
        self.storage[payment_id] = payload.to_dict()
        
        return True
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status"""
        return self.storage.get(payment_id, {})
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get payment statistics"""
        return {
            "payment_count": self.storage["payment_count"],
            "total_volume": str(self.storage["total_volume"]),
            "token_contract": self.storage["token_contract"]
        }

class EscrowContract(SmartContract):
    """Escrow contract for conditional payments"""
    
    def __init__(self, address: str, creator: str):
        super().__init__(address, ContractType.ESCROW, creator)
        self.storage["escrows"] = {}
        self.storage["escrow_count"] = 0
    
    def create_escrow(self, payload: TransferPayload, conditions: List[str]) -> str:
        """Create escrow"""
        escrow_id = f"escrow_{self.storage['escrow_count'] + 1}"
        
        escrow_data = {
            "payload": payload.to_dict(),
            "conditions": conditions,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "released_at": None,
            "refunded_at": None
        }
        
        self.storage["escrows"][escrow_id] = escrow_data
        self.storage["escrow_count"] += 1
        
        return escrow_id
    
    def release_escrow(self, escrow_id: str, releaser: str) -> bool:
        """Release escrow funds"""
        escrow = self.storage["escrows"].get(escrow_id)
        if not escrow:
            raise ValueError("Escrow not found")
        
        if escrow["status"] != "pending":
            raise ValueError("Escrow not in pending state")
        
        escrow["status"] = "released"
        escrow["released_at"] = datetime.utcnow().isoformat()
        escrow["releaser"] = releaser
        
        self.storage["escrows"][escrow_id] = escrow
        
        return True
    
    def refund_escrow(self, escrow_id: str, refunder: str) -> bool:
        """Refund escrow funds"""
        escrow = self.storage["escrows"].get(escrow_id)
        if not escrow:
            raise ValueError("Escrow not found")
        
        if escrow["status"] != "pending":
            raise ValueError("Escrow not in pending state")
        
        escrow["status"] = "refunded"
        escrow["refunded_at"] = datetime.utcnow().isoformat()
        escrow["refunder"] = refunder
        
        self.storage["escrows"][escrow_id] = escrow
        
        return True
    
    def get_escrow_status(self, escrow_id: str) -> Dict[str, Any]:
        """Get escrow status"""
        return self.storage["escrows"].get(escrow_id, {})

class MultiSigContract(SmartContract):
    """Multi-signature wallet contract"""
    
    def __init__(self, address: str, creator: str, owners: List[str], required: int):
        super().__init__(address, ContractType.MULTI_SIG, creator)
        self.storage["owners"] = owners
        self.storage["required"] = required
        self.storage["proposals"] = {}
        self.storage["proposal_count"] = 0
    
    def submit_proposal(self, payload: TransferPayload, proposer: str) -> str:
        """Submit transaction proposal"""
        proposal_id = f"proposal_{self.storage['proposal_count'] + 1}"
        
        proposal_data = {
            "payload": payload.to_dict(),
            "proposer": proposer,
            "approvals": [],
            "executed": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.storage["proposals"][proposal_id] = proposal_data
        self.storage["proposal_count"] += 1
        
        return proposal_id
    
    def approve_proposal(self, proposal_id: str, approver: str) -> bool:
        """Approve transaction proposal"""
        proposal = self.storage["proposals"].get(proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")
        
        if approver not in self.storage["owners"]:
            raise ValueError("Not an owner")
        
        if approver in proposal["approvals"]:
            raise ValueError("Already approved")
        
        proposal["approvals"].append(approver)
        self.storage["proposals"][proposal_id] = proposal
        
        # Check if we have enough approvals
        if len(proposal["approvals"]) >= self.storage["required"]:
            return self.execute_proposal(proposal_id)
        
        return True
    
    def execute_proposal(self, proposal_id: str) -> bool:
        """Execute approved proposal"""
        proposal = self.storage["proposals"].get(proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")
        
        if len(proposal["approvals"]) < self.storage["required"]:
            raise ValueError("Insufficient approvals")
        
        if proposal["executed"]:
            raise ValueError("Already executed")
        
        proposal["executed"] = True
        proposal["executed_at"] = datetime.utcnow().isoformat()
        
        self.storage["proposals"][proposal_id] = proposal
        
        return True
    
    def get_proposal_status(self, proposal_id: str) -> Dict[str, Any]:
        """Get proposal status"""
        return self.storage["proposals"].get(proposal_id, {})

class SubscriptionContract(SmartContract):
    """Subscription payment contract"""
    
    def __init__(self, address: str, creator: str):
        super().__init__(address, ContractType.SUBSCRIPTION, creator)
        self.storage["subscriptions"] = {}
        self.storage["subscription_count"] = 0
    
    def create_subscription(self, subscriber: str, amount: Decimal, interval_days: int) -> str:
        """Create subscription"""
        subscription_id = f"sub_{self.storage['subscription_count'] + 1}"
        
        subscription_data = {
            "subscriber": subscriber,
            "amount": str(amount),
            "interval_days": interval_days,
            "next_payment": (datetime.utcnow() + timedelta(days=interval_days)).isoformat(),
            "active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.storage["subscriptions"][subscription_id] = subscription_data
        self.storage["subscription_count"] += 1
        
        return subscription_id
    
    def process_subscription_payment(self, subscription_id: str) -> bool:
        """Process subscription payment"""
        subscription = self.storage["subscriptions"].get(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        
        if not subscription["active"]:
            raise ValueError("Subscription not active")
        
        # Update next payment date
        next_payment = datetime.fromisoformat(subscription["next_payment"])
        new_next_payment = next_payment + timedelta(days=subscription["interval_days"])
        subscription["next_payment"] = new_next_payment.isoformat()
        subscription["last_payment"] = datetime.utcnow().isoformat()
        
        self.storage["subscriptions"][subscription_id] = subscription
        
        return True
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel subscription"""
        subscription = self.storage["subscriptions"].get(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        
        subscription["active"] = False
        subscription["cancelled_at"] = datetime.utcnow().isoformat()
        
        self.storage["subscriptions"][subscription_id] = subscription
        
        return True
    
    def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription status"""
        return self.storage["subscriptions"].get(subscription_id, {})

class CustomNetwork:
    """Custom network for managing smart contracts"""
    
    def __init__(self, network_id: str = "membra-custom"):
        self.network_id = network_id
        self.contracts: Dict[str, SmartContract] = {}
        self.block_number = 0
        self.transaction_count = 0
        self.semantic_syntax = SemanticTransferSyntax()
    
    def deploy_contract(self, contract: SmartContract) -> str:
        """Deploy smart contract to network"""
        contract.state = ContractState.ACTIVE
        self.contracts[contract.address] = contract
        
        self.block_number += 1
        
        return contract.address
    
    def execute_contract(self, call: ContractCall) -> ContractResult:
        """Execute contract call"""
        contract = self.contracts.get(call.contract_address)
        if not contract:
            return ContractResult(
                success=False,
                return_value=None,
                gas_used=0,
                events=[],
                error_message="Contract not found"
            )
        
        result = contract.execute(call)
        
        if result.success:
            self.transaction_count += 1
        
        return result
    
    def process_semantic_transfer(self, payload: TransferPayload) -> ContractResult:
        """Process semantic value transfer"""
        # Route to appropriate contract based on semantic type
        if payload.semantic_value.semantic_type == SemanticType.PAYMENT:
            return self._process_payment(payload)
        elif payload.semantic_value.semantic_type == SemanticType.ESCROW:
            return self._process_escrow(payload)
        elif payload.semantic_value.semantic_type == SemanticType.MULTI_SIG:
            return self._process_multi_sig(payload)
        elif payload.semantic_value.semantic_type == SemanticType.SUBSCRIPTION:
            return self._process_subscription(payload)
        else:
            return self._process_generic_transfer(payload)
    
    def _process_payment(self, payload: TransferPayload) -> ContractResult:
        """Process payment transfer"""
        # Find or create payment contract
        payment_contract = self._get_or_create_payment_contract()
        
        call = ContractCall(
            contract_address=payment_contract.address,
            function_name="process_payment",
            parameters={"payload": payload},
            caller=payload.semantic_value.sender
        )
        
        return self.execute_contract(call)
    
    def _process_escrow(self, payload: TransferPayload) -> ContractResult:
        """Process escrow transfer"""
        escrow_contract = self._get_or_create_escrow_contract()
        
        call = ContractCall(
            contract_address=escrow_contract.address,
            function_name="create_escrow",
            parameters={
                "payload": payload,
                "conditions": payload.semantic_value.conditions
            },
            caller=payload.semantic_value.sender
        )
        
        return self.execute_contract(call)
    
    def _process_multi_sig(self, payload: TransferPayload) -> ContractResult:
        """Process multi-sig transfer"""
        multi_sig_contract = self._get_or_create_multi_sig_contract()
        
        call = ContractCall(
            contract_address=multi_sig_contract.address,
            function_name="submit_proposal",
            parameters={"payload": payload, "proposer": payload.semantic_value.sender},
            caller=payload.semantic_value.sender
        )
        
        return self.execute_contract(call)
    
    def _process_subscription(self, payload: TransferPayload) -> ContractResult:
        """Process subscription transfer"""
        subscription_contract = self._get_or_create_subscription_contract()
        
        call = ContractCall(
            contract_address=subscription_contract.address,
            function_name="create_subscription",
            parameters={
                "subscriber": payload.semantic_value.recipient,
                "amount": Decimal(str(payload.semantic_value.amount)),
                "interval_days": 30  # Default 30 days
            },
            caller=payload.semantic_value.sender
        )
        
        return self.execute_contract(call)
    
    def _process_generic_transfer(self, payload: TransferPayload) -> ContractResult:
        """Process generic transfer"""
        # For other semantic types, create a simple token transfer
        token_contract = self._get_or_create_token_contract()
        
        call = ContractCall(
            contract_address=token_contract.address,
            function_name="transfer",
            parameters={
                "to": payload.semantic_value.recipient,
                "amount": Decimal(str(payload.semantic_value.amount))
            },
            caller=payload.semantic_value.sender
        )
        
        return self.execute_contract(call)
    
    def _get_or_create_payment_contract(self) -> PaymentContract:
        """Get or create payment contract"""
        address = "payment_contract_001"
        if address not in self.contracts:
            token_contract = self._get_or_create_token_contract()
            contract = PaymentContract(address, "network", token_contract.address)
            self.deploy_contract(contract)
        return self.contracts[address]
    
    def _get_or_create_escrow_contract(self) -> EscrowContract:
        """Get or create escrow contract"""
        address = "escrow_contract_001"
        if address not in self.contracts:
            contract = EscrowContract(address, "network")
            self.deploy_contract(contract)
        return self.contracts[address]
    
    def _get_or_create_multi_sig_contract(self) -> MultiSigContract:
        """Get or create multi-sig contract"""
        address = "multisig_contract_001"
        if address not in self.contracts:
            contract = MultiSigContract(address, "network", 
                                       ["owner1", "owner2", "owner3"], 2)
            self.deploy_contract(contract)
        return self.contracts[address]
    
    def _get_or_create_subscription_contract(self) -> SubscriptionContract:
        """Get or create subscription contract"""
        address = "subscription_contract_001"
        if address not in self.contracts:
            contract = SubscriptionContract(address, "network")
            self.deploy_contract(contract)
        return self.contracts[address]
    
    def _get_or_create_token_contract(self) -> TokenContract:
        """Get or create token contract"""
        address = "token_contract_001"
        if address not in self.contracts:
            contract = TokenContract(address, "network", "Membra Token", "MEMBRA", 
                                   Decimal("1000000000"))
            self.deploy_contract(contract)
        return self.contracts[address]
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get network status"""
        return {
            "network_id": self.network_id,
            "block_number": self.block_number,
            "transaction_count": self.transaction_count,
            "contract_count": len(self.contracts),
            "contracts": {
                address: {
                    "type": contract.contract_type.value,
                    "state": contract.state.value,
                    "creator": contract.creator
                }
                for address, contract in self.contracts.items()
            }
        }