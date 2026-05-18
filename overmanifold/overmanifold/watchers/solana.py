"""
Overmanifold Solana Watcher (Read-Only)
Observes Solana mainnet transactions without signing capabilities.
Testnet v0.1 - No private keys, no autonomous value transfer.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

try:
    from solana.rpc.async_api import AsyncClient
    from solana.transaction import Transaction
    from solana.publickey import PublicKey
except ImportError:
    AsyncClient = None
    Transaction = None
    PublicKey = None

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.infrastructure.config import get_config
from overmanifold.workers.transaction_endpoint import (
    TransactionObserver, LifecycleState, EventType
)

logger = get_logger("solana_watcher")
config = get_config()


@dataclass
class SolanaTransaction:
    """Solana transaction data."""
    signature: str
    slot: int
    block_time: Optional[datetime]
    fee: int
    status: str
    error: Optional[str]
    accounts: List[str]
    instructions: List[Dict]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "signature": self.signature,
            "slot": self.slot,
            "block_time": self.block_time.isoformat() if self.block_time else None,
            "fee": self.fee,
            "status": self.status,
            "error": self.error,
            "accounts": self.accounts,
            "instructions": self.instructions
        }


class SolanaWatcher:
    """
    Read-only Solana blockchain watcher.
    Observes transactions and creates transaction endpoint workers.
    """
    
    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL")
        self.client: Optional[AsyncClient] = None
        self.transaction_observer = TransactionObserver()
        self.is_connected = False
        self.confirmations_required = int(os.getenv("SOLANA_CONFIRMATIONS_REQUIRED", "32"))
        self.read_only = os.getenv("SOLANA_READ_ONLY", "true").lower() == "true"
        
        if not self.read_only:
            logger.warning("Solana watcher is not in read-only mode - this violates testnet security boundaries")
        
        self._connect()
    
    def _connect(self) -> bool:
        """Connect to Solana RPC (read-only)."""
        if not AsyncClient:
            logger.error("Solana library not installed - cannot connect to Solana")
            return False
        
        try:
            self.client = AsyncClient(self.rpc_url)
            
            # Test connection
            version = asyncio.run(self.client.get_version())
            if version:
                logger.info(f"Connected to Solana network. Version: {version}")
                self.is_connected = True
                return True
            else:
                logger.error("Failed to connect to Solana network")
                return False
                
        except Exception as e:
            logger.error(f"Solana connection error: {str(e)}")
            return False
    
    async def watch_slots(self) -> None:
        """Watch for new slots and transactions."""
        if not self.is_connected:
            logger.error("Cannot watch slots - not connected to Solana")
            return
        
        logger.info("Starting Solana slot watcher")
        
        last_slot = None
        
        while True:
            try:
                # Get current slot
                slot_info = await self.client.get_slot()
                current_slot = slot_info['result']
                
                if last_slot is None:
                    last_slot = current_slot
                elif current_slot > last_slot:
                    # Process new slots
                    for slot_num in range(last_slot + 1, current_slot + 1):
                        await self._process_slot(slot_num)
                    
                    last_slot = current_slot
                
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                logger.error(f"Error watching slots: {str(e)}")
                await asyncio.sleep(10)
    
    async def _process_slot(self, slot_number: int) -> None:
        """Process a single slot and its transactions."""
        try:
            # Get confirmed block for this slot
            block = await self.client.get_confirmed_block(slot_number)
            
            if not block or 'result' not in block:
                return
            
            block_data = block['result']
            transactions = block_data.get('transactions', [])
            
            for tx in transactions:
                if 'transaction' in tx:
                    await self._process_transaction(tx['transaction'], slot_number)
                
        except Exception as e:
            logger.error(f"Error processing slot {slot_number}: {str(e)}")
    
    async def _process_transaction(self, tx: Dict, slot_number: int) -> None:
        """Process a Solana transaction and create endpoint worker."""
        try:
            signature = tx.get('signatures', [''])[0] if isinstance(tx, dict) else str(tx)
            
            if not signature:
                return
            
            # Get transaction details
            tx_detail = await self.client.get_confirmed_transaction(signature)
            
            if not tx_detail or 'result' not in tx_detail:
                return
            
            tx_data = tx_detail['result']
            
            # Convert to our format
            tx_dict = {
                "hash": signature,
                "slot": slot_number,
                "fee": tx_data.get('meta', {}).get('fee', 0),
                "status": "confirmed" if tx_data.get('meta') else "pending",
                "accounts": [str(acc) for acc in tx_data.get('message', {}).get('accountKeys', [])],
                "instructions": self._parse_instructions(tx_data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Create transaction endpoint worker
            worker = self.transaction_observer.observe_transaction("solana", tx_dict)
            
            # Update lifecycle state
            self.transaction_observer.update_transaction_state(
                "solana", 
                signature, 
                self.confirmations_required,
                LifecycleState.INCLUDED.value
            )
            
            logger.info(f"Processed Solana transaction: {signature} -> included")
            
        except Exception as e:
            logger.error(f"Error processing Solana transaction: {str(e)}")
    
    def _parse_instructions(self, tx_data: Dict) -> List[Dict]:
        """Parse transaction instructions."""
        instructions = []
        
        try:
            message = tx_data.get('message', {})
            ix_list = message.get('instructions', [])
            
            for ix in ix_list:
                instructions.append({
                    "program_id": str(ix.get('programIdIndex', '')),
                    "accounts": ix.get('accounts', []),
                    "data": ix.get('data', '')
                })
        except Exception as e:
            logger.error(f"Error parsing instructions: {str(e)}")
        
        return instructions
    
    async def get_transaction(self, signature: str) -> Optional[Dict]:
        """Get transaction by signature (read-only)."""
        if not self.is_connected:
            return None
        
        try:
            tx_detail = await self.client.get_confirmed_transaction(signature)
            
            if tx_detail and 'result' in tx_detail:
                tx_data = tx_detail['result']
                
                return {
                    "signature": signature,
                    "slot": tx_data.get('slot'),
                    "fee": tx_data.get('meta', {}).get('fee', 0),
                    "status": "confirmed",
                    "accounts": [str(acc) for acc in tx_data.get('message', {}).get('accountKeys', [])]
                }
        except Exception as e:
            logger.error(f"Error getting Solana transaction {signature}: {str(e)}")
        
        return None
    
    async def get_balance(self, address: str) -> Optional[int]:
        """Get balance for address (read-only)."""
        if not self.is_connected:
            return None
        
        try:
            balance = await self.client.get_balance(PublicKey(address))
            return balance['result'] if 'result' in balance else None
        except Exception as e:
            logger.error(f"Error getting Solana balance for {address}: {str(e)}")
            return None
    
    async def get_slot(self) -> Optional[int]:
        """Get current slot (read-only)."""
        if not self.is_connected:
            return None
        
        try:
            slot_info = await self.client.get_slot()
            return slot_info['result'] if 'result' in slot_info else None
        except Exception as e:
            logger.error(f"Error getting Solana slot: {str(e)}")
            return None
    
    def verify_no_private_keys(self) -> bool:
        """Verify that no private keys are accessible (security check)."""
        # This is a critical security check for testnet
        # Solana AsyncClient doesn't have direct account access by default
        # But we should still verify our configuration
        
        if not self.read_only:
            logger.critical("SECURITY VIOLATION: Solana watcher is not in read-only mode")
            return False
        
        # Check for any keypair files or environment variables
        if os.getenv("SOLANA_PRIVATE_KEY"):
            logger.critical("SECURITY VIOLATION: Solana private key found in environment")
            return False
        
        keyfile_paths = [
            "~/.config/solana/id.json",
            "~/keypairs.json",
            "./keypairs.json"
        ]
        
        for keyfile_path in keyfile_paths:
            expanded_path = os.path.expanduser(keyfile_path)
            if os.path.exists(expanded_path):
                logger.critical(f"SECURITY VIOLATION: Solana keyfile found at {expanded_path}")
                return False
        
        logger.info("Solana watcher security check passed - no private keys found")
        return True
    
    async def start(self) -> None:
        """Start the Solana watcher."""
        if not self.verify_no_private_keys():
            raise RuntimeError("Security check failed: Solana watcher has private key access")
        
        logger.info("Starting Solana watcher in read-only mode")
        
        # Start slot watcher
        await self.watch_slots()


if __name__ == "__main__":
    async def main():
        watcher = SolanaWatcher()
        await watcher.start()
    
    asyncio.run(main())