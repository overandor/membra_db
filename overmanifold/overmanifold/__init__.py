"""
Overmanifold Integration Package
Unified integration of all Overmanifold components into a civilization-scale coordination system.
"""

from overmanifold.core.engine import (
    OvermanifoldEngine,
    OvermanifoldEndpoint,
    StateTransition,
    SemanticIntent,
    Capability,
    RoutingSurface,
    SettlementMapping,
    Handler,
    StateTransitionType,
    CapabilityType,
    MerkleProof
)

from overmanifold.governance.llm_engine import (
    LLMGovernanceEngine,
    EconomicTask,
    IntentInterpretation,
    GovernanceDecision,
    IntentType,
    TaskPriority,
    TaskStatus,
    LLMProvider,
    MockLLMProvider
)

from overmanifold.routing.geodesic import (
    GeodesicRouter,
    LiquidityManifold,
    GeodesicPath,
    ManifoldEdge,
    RoutingConstraint,
    RoutingConstraintValue,
    RoutingMetrics
)

from overmanifold.consensus.proof_of_profit import (
    ProofOfProfitConsensus,
    EconomicWork,
    ProofOfProfit,
    InverseMiningOperation,
    TreasuryDeflation,
    WorkType,
    ConsensusStatus
)

__version__ = "0.1.0"
__author__ = "Overmanifold Protocol Foundation"

__all__ = [
    # Core Engine
    'OvermanifoldEngine',
    'OvermanifoldEndpoint',
    'StateTransition',
    'SemanticIntent',
    'Capability',
    'RoutingSurface',
    'SettlementMapping',
    'Handler',
    'StateTransitionType',
    'CapabilityType',
    'MerkleProof',
    
    # LLM Governance
    'LLMGovernanceEngine',
    'EconomicTask',
    'IntentInterpretation',
    'GovernanceDecision',
    'IntentType',
    'TaskPriority',
    'TaskStatus',
    'LLMProvider',
    'MockLLMProvider',
    
    # Geodesic Routing
    'GeodesicRouter',
    'LiquidityManifold',
    'GeodesicPath',
    'ManifoldEdge',
    'RoutingConstraint',
    'RoutingConstraintValue',
    'RoutingMetrics',
    
    # Proof of Profit Consensus
    'ProofOfProfitConsensus',
    'EconomicWork',
    'ProofOfProfit',
    'InverseMiningOperation',
    'TreasuryDeflation',
    'WorkType',
    'ConsensusStatus'
]