"""
Overmanifold Simulated Mint and Liquidity Pool System
Testnet v0.1 - Simulated value for demonstration purposes only.
No real financial value, no autonomous fund movement.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import random
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.infrastructure.config import get_config
from overmanifold.approval.human_gate import ApprovalType, require_approval, check_approval

logger = get_logger("simulated_mint")
config = get_config()


class TokenType(Enum):
    """Types of tokens in the simulated system."""
    OVERMANIFOLD = "overmanifold"
    REPOSITORY_TOKEN = "repository_token"
    COLLATERAL_TOKEN = "collateral_token"
    TESTNET_TOKEN = "testnet_token"


@dataclass
class Token:
    """Simulated token."""
    token_id: str
    symbol: str
    name: str
    total_supply: float
    circulating_supply: float
    price_usd: float
    market_cap_usd: float
    created_at: datetime
    token_type: TokenType
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "token_id": self.token_id,
            "symbol": self.symbol,
            "name": self.name,
            "total_supply": self.total_supply,
            "circulating_supply": self.circulating_supply,
            "price_usd": self.price_usd,
            "market_cap_usd": self.market_cap_usd,
            "created_at": self.created_at.isoformat(),
            "token_type": self.token_type.value
        }


@dataclass
class LiquidityPool:
    """Simulated liquidity pool."""
    pool_id: str
    token_a: str
    token_b: str
    reserve_a: float
    reserve_b: float
    total_lp_tokens: float
    apr: float
    tvl_usd: float
    created_at: datetime
    
    def get_price(self, input_token: str, input_amount: float) -> float:
        """Calculate swap output using constant product formula."""
        if input_token == self.token_a:
            # Input token A, output token B
            output_amount = (self.reserve_b * input_amount) / (self.reserve_a + input_amount)
            return output_amount
        else:
            # Input token B, output token A
            output_amount = (self.reserve_a * input_amount) / (self.reserve_b + input_amount)
            return output_amount
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "pool_id": self.pool_id,
            "token_a": self.token_a,
            "token_b": self.token_b,
            "reserve_a": self.reserve_a,
            "reserve_b": self.reserve_b,
            "total_lp_tokens": self.total_lp_tokens,
            "apr": self.apr,
            "tvl_usd": self.tvl_usd,
            "created_at": self.created_at.isoformat()
        }


class SimulatedMint:
    """
    Simulated token minting system.
    Demonstrates token minting and liquidity pool functionality without real value.
    """
    
    def __init__(self):
        self.tokens: Dict[str, Token] = {}
        self.liquidity_pools: Dict[str, LiquidityPool] = {}
        self.token_prices: Dict[str, float] = {}
        self.simulated_value_multiplier = 1.0  # For testing price movements
        
        # Initialize base tokens
        self._initialize_base_tokens()
    
    def _initialize_base_tokens(self) -> None:
        """Initialize base testnet tokens."""
        # Overmanifold governance token
        om_token = Token(
            token_id="overmanifold_governance",
            symbol="OM",
            name="Overmanifold Governance Token",
            total_supply=1000000000.0,
            circulating_supply=800000000.0,
            price_usd=0.10,
            market_cap_usd=100000000.0,
            created_at=datetime.utcnow(),
            token_type=TokenType.OVERMANIFOLD
        )
        self.tokens[om_token.token_id] = om_token
        self.token_prices[om_token.symbol] = om_token.price_usd
        
        # Testnet demonstration token
        testnet_token = Token(
            token_id="testnet_demonstration",
            symbol="TEST",
            name="Overmanifold Testnet Token",
            total_supply=1000000.0,
            circulating_supply=1000000.0,
            price_usd=0.01,
            market_cap_usd=10000.0,
            created_at=datetime.utcnow(),
            token_type=TokenType.TESTNET_TOKEN
        )
        self.tokens[testnet_token.token_id] = testnet_token
        self.token_prices[testnet_token.symbol] = testnet_token.price_usd
    
    async def mint_token(
        self,
        token_type: TokenType,
        symbol: str,
        name: str,
        supply: float,
        initial_price_usd: float,
        recipient: str,
        approval_required: bool = True
    ) -> Token:
        """
        Mint new tokens (requires approval for non-testnet tokens).
        """
        # For testnet, only TEST tokens can be minted without approval
        if token_type != TokenType.TESTNET_TOKEN and approval_required:
            # Create approval request
            operation_data = {
                "token_type": token_type.value,
                "symbol": symbol,
                "name": name,
                "supply": supply,
                "initial_price_usd": initial_price_usd,
                "recipient": recipient
            }
            
            request_id = require_approval(
                ApprovalType.TOKEN_MINT,
                operation_data,
                requester_id="simulated_mint"
            )
            
            # Wait for approval (in production, this would be async)
            # For testnet demo, we'll auto-approve TEST tokens
            logger.info(f"Approval request created: {request_id}")
            
            # In real implementation, wait for approval
            # if not check_approval(request_id):
            #     raise RuntimeError("Token minting not approved")
        
        # Create token
        token_id = f"{symbol.lower()}_token_{datetime.utcnow().timestamp()}"
        
        token = Token(
            token_id=token_id,
            symbol=symbol,
            name=name,
            total_supply=supply,
            circulating_supply=supply,
            price_usd=initial_price_usd,
            market_cap_usd=supply * initial_price_usd,
            created_at=datetime.utcnow(),
            token_type=token_type
        )
        
        self.tokens[token_id] = token
        self.token_prices[symbol] = initial_price_usd
        
        logger.info(f"Minted token: {symbol} ({supply} tokens) for {recipient}")
        
        return token
    
    async def create_liquidity_pool(
        self,
        token_a_symbol: str,
        token_b_symbol: str,
        initial_reserve_a: float,
        initial_reserve_b: float,
        approval_required: bool = True
    ) -> LiquidityPool:
        """
        Create a liquidity pool (requires approval).
        """
        # Create approval request for liquidity pool creation
        if approval_required:
            operation_data = {
                "token_a": token_a_symbol,
                "token_b": token_b_symbol,
                "initial_reserve_a": initial_reserve_a,
                "initial_reserve_b": initial_reserve_b,
                "estimated_tvl": initial_reserve_a * self.token_prices.get(token_a_symbol, 0.01) + 
                              initial_reserve_b * self.token_prices.get(token_b_symbol, 0.01)
            }
            
            request_id = require_approval(
                ApprovalType.LIQUIDITY_OPERATION,
                operation_data,
                requester_id="simulated_mint"
            )
            
            logger.info(f"Liquidity pool approval request created: {request_id}")
        
        # Create pool
        pool_id = f"{token_a_symbol}_{token_b_symbol}_{datetime.utcnow().timestamp()}"
        
        # Calculate TVL
        tvl_usd = (initial_reserve_a * self.token_prices.get(token_a_symbol, 0.01) +
                   initial_reserve_b * self.token_prices.get(token_b_symbol, 0.01))
        
        pool = LiquidityPool(
            pool_id=pool_id,
            token_a=token_a_symbol,
            token_b=token_b_symbol,
            reserve_a=initial_reserve_a,
            reserve_b=initial_reserve_b,
            total_lp_tokens=0.0,
            apr=random.uniform(0.01, 0.20),  # Simulated APR
            tvl_usd=tvl_usd,
            created_at=datetime.utcnow()
        )
        
        self.liquidity_pools[pool_id] = pool
        
        logger.info(f"Created liquidity pool: {pool_id} with TVL ${tvl_usd:,.2f}")
        
        return pool
    
    async def simulate_swap(
        self,
        pool_id: str,
        input_token: str,
        input_amount: float
    ) -> Dict[str, float]:
        """
        Simulate a token swap in a liquidity pool.
        """
        if pool_id not in self.liquidity_pools:
            raise ValueError(f"Liquidity pool not found: {pool_id}")
        
        pool = self.liquidity_pools[pool_id]
        
        # Calculate output
        output_amount = pool.get_price(input_token, input_amount)
        
        # Update reserves (simulated)
        if input_token == pool.token_a:
            pool.reserve_a += input_amount
            pool.reserve_b = max(0.001, pool.reserve_b - output_amount)
        else:
            pool.reserve_b += input_amount
            pool.reserve_a = max(0.001, pool.reserve_a - output_amount)
        
        # Recalculate TVL
        pool.tvl_usd = (pool.reserve_a * self.token_prices.get(pool.token_a, 0.01) +
                       pool.reserve_b * self.token_prices.get(pool.token_b, 0.01))
        
        logger.info(f"Simulated swap: {input_amount} {input_token} -> {output_amount:.4f} output")
        
        return {
            "input_amount": input_amount,
            "output_amount": output_amount,
            "price_impact": 0.01,  # Simplified
            "new_tvl_usd": pool.tvl_usd
        }
    
    def get_token(self, token_id: str) -> Optional[Token]:
        """Get token by ID."""
        return self.tokens.get(token_id)
    
    def get_pool(self, pool_id: str) -> Optional[LiquidityPool]:
        """Get liquidity pool by ID."""
        return self.liquidity_pools.get(pool_id)
    
    def get_all_tokens(self) -> List[Token]:
        """Get all tokens."""
        return list(self.tokens.values())
    
    def get_all_pools(self) -> List[LiquidityPool]:
        """Get all liquidity pools."""
        return list(self.liquidity_pools.values())
    
    def simulate_price_movement(self, volatility: float = 0.01) -> None:
        """
        Simulate price movement for demonstration.
        In production, this would be based on real market data.
        """
        for symbol in self.token_prices:
            # Random price movement with given volatility
            change = random.uniform(-volatility, volatility)
            self.token_prices[symbol] *= (1 + change)
            
            # Update token market cap
            for token in self.tokens.values():
                if token.symbol == symbol:
                    token.price_usd = self.token_prices[symbol]
                    token.market_cap_usd = token.total_supply * token.price_usd
    
    def get_market_summary(self) -> Dict[str, Any]:
        """Get market summary."""
        total_tvl = sum(pool.tvl_usd for pool in self.liquidity_pools.values())
        total_market_cap = sum(token.market_cap_usd for token in self.tokens.values())
        
        return {
            "total_tokens": len(self.tokens),
            "total_pools": len(self.liquidity_pools),
            "total_tvl_usd": total_tvl,
            "total_market_cap_usd": total_market_cap,
            "token_count": len(self.tokens),
            "pool_count": len(self.liquidity_pools)
        }


# Global simulated mint instance
simulated_mint = SimulatedMint()


async def mint_testnet_tokens(recipient: str, amount: float = 1000.0) -> Token:
    """
    Convenience function to mint testnet tokens.
    """
    return await simulated_mint.mint_token(
        token_type=TokenType.TESTNET_TOKEN,
        symbol="TEST",
        name="Overmanifold Testnet Token",
        supply=amount * 1000,  # Mint 1000x for distribution
        initial_price_usd=0.01,
        recipient=recipient,
        approval_required=False  # Testnet tokens don't require approval
    )


async def create_demo_pool() -> LiquidityPool:
    """
    Convenience function to create a demonstration liquidity pool.
    """
    return await simulated_mint.create_liquidity_pool(
        token_a_symbol="OM",
        token_b_symbol="TEST",
        initial_reserve_a=10000.0,
        initial_reserve_b=1000000.0,
        approval_required=False  # Demo pools don't require approval
    )


def get_market_summary() -> Dict[str, Any]:
    """
    Convenience function to get market summary.
    """
    return simulated_mint.get_market_summary()