"""
Overmanifold Unified System
Complete integration of all Overmanifold components into a unified civilization-scale coordination architecture.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import hashlib

from overmanifold.core.engine import (
    OvermanifoldEngine, OvermanifoldEndpoint, StateTransition,
    SemanticIntent, Capability, CapabilityType, StateTransitionType
)
from overmanifold.governance.llm_engine import (
    LLMGovernanceEngine, MockLLMProvider, IntentType as GovIntentType
)
from overmanifold.routing.geodesic import (
    LiquidityManifold, GeodesicRouter, ManifoldEdge, RoutingConstraintValue, RoutingConstraint
)
from overmanifold.consensus.proof_of_profit import (
    ProofOfProfitConsensus, WorkType, ConsensusStatus
)
from overmanifold.workers.transaction_endpoint import (
    TransactionObserver, TransactionWorkerScheduler, LifecycleState
)
from overmanifold.tokenization.github_repo import (
    RepoTokenizer, RepoGovernanceEngine, RepositoryMicroCompany
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OvermanifoldUnified:
    """
    Unified Overmanifold System
    Integrates core engine, LLM governance, geodesic routing, and proof-of-profit consensus
    into a single civilization-scale coordination architecture.
    """
    
    def __init__(self, initial_supply: float = 1_000_000_000):
        # Initialize core components
        self.core_engine = OvermanifoldEngine()
        self.llm_governance = LLMGovernanceEngine(MockLLMProvider())
        self.liquidity_manifold = LiquidityManifold()
        self.geodesic_router = GeodesicRouter(self.liquidity_manifold)
        self.proof_of_profit = ProofOfProfitConsensus(initial_supply=initial_supply)
        
        # Initialize transaction endpoint workers (V2 capsule)
        self.transaction_observer = TransactionObserver()
        self.worker_scheduler = TransactionWorkerScheduler(self.transaction_observer)
        
        # Initialize GitHub repository tokenization
        self.repo_tokenizer = RepoTokenizer()
        self.repo_governance = RepoGovernanceEngine(self.repo_tokenizer)
        
        # Unified state
        self.unified_endpoints: Dict[str, Dict] = {}  # endpoint_id -> {core, governance, routing, consensus}
        self.coordination_events: List[Dict] = []
        
        logger.info("Overmanifold Unified System initialized")
    
    async def create_unified_endpoint(
        self,
        public_key: str,
        private_key: str,
        capabilities: List[Capability] = None,
        metadata: Dict = None
    ) -> str:
        """
        Create a unified Overmanifold endpoint that integrates all subsystems
        """
        # Create core endpoint
        core_endpoint = self.core_engine.create_endpoint(
            public_key, private_key, capabilities, metadata
        )
        
        # Add to liquidity manifold
        self.liquidity_manifold.add_endpoint(
            core_endpoint.endpoint_id,
            [cap.capability_type.value for cap in (capabilities or [])],
            core_endpoint.total_economic_value,
            core_endpoint.trust_density
        )
        
        # Register in consensus mechanism
        self.proof_of_profit.register_validator(core_endpoint.endpoint_id, stake=1000.0)
        
        # Create unified endpoint record
        self.unified_endpoints[core_endpoint.endpoint_id] = {
            'core': core_endpoint,
            'governance': {
                'tasks_created': 0,
                'tasks_completed': 0
            },
            'routing': {
                'paths_calculated': 0,
                'total_routed_value': 0.0
            },
            'consensus': {
                'work_submitted': 0,
                'work_verified': 0,
                'rewards_earned': 0.0
            },
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Created unified endpoint: {core_endpoint.endpoint_id}")
        return core_endpoint.endpoint_id
    
    async def process_human_intent(
        self,
        endpoint_id: str,
        human_intent: str,
        context: Dict = None
    ) -> Dict:
        """
        Process human intent through the complete Overmanifold pipeline:
        Intent Interpretation → State Transition → Economic Reward
        """
        context = context or {}
        
        if endpoint_id not in self.unified_endpoints:
            return {'error': 'Endpoint not found'}
        
        # Step 1: LLM Governance interprets intent
        interpretation = await self.llm_governance.interpret_intent(human_intent, context)
        
        # Step 2: Create state transition based on interpretation
        if interpretation.interpreted_tasks:
            task = interpretation.interpreted_tasks[0]
            
            # Map governance intent type to state transition type
            intent_mapping = {
                GovIntentType.RESOURCE_ALLOCATION: StateTransitionType.COMPUTE_CONTRIBUTION,
                GovIntentType.LIQUIDITY_ROUTING: StateTransitionType.LIQUIDITY_ROUTE,
                GovIntentType.TRUST_ESTABLISHMENT: StateTransitionType.PROOF_GENERATION,
                GovIntentType.COMPUTATION_REQUEST: StateTransitionType.COMPUTE_CONTRIBUTION,
                GovIntentType.MESSAGE_RELAY: StateTransitionType.MESSAGE_SEND
            }
            
            transition_type = intent_mapping.get(task.intent_type, StateTransitionType.SEMANTIC_INTENT)
            
            # Create state transition
            transition = self.core_engine.create_state_transition(
                endpoint_id=endpoint_id,
                transition_type=transition_type,
                semantic_intent=human_intent,
                from_state="idle",
                to_state=task.intent_type.value,
                economic_value=task.estimated_cost,
                capability_requirements=[CapabilityType(c) for c in task.required_capabilities],
                metadata={'task_id': task.task_id}
            )
            
            # Step 3: Submit work to proof-of-profit consensus
            if transition:
                work = self.proof_of_profit.submit_economic_work(
                    endpoint_id=endpoint_id,
                    work_type=self._map_transition_to_work_type(transition_type),
                    description=task.description,
                    proof_data={
                        'economic_value': transition.economic_value,
                        'semantic_intent': transition.semantic_intent,
                        'capability_requirements': task.required_capabilities
                    },
                    metadata={'interpretation_id': interpretation.interpretation_id}
                )
                
                # Update unified endpoint stats
                self.unified_endpoints[endpoint_id]['governance']['tasks_created'] += 1
                self.unified_endpoints[endpoint_id]['consensus']['work_submitted'] += 1
                
                return {
                    'success': True,
                    'interpretation': interpretation.to_dict(),
                    'transition': transition.to_dict() if transition else None,
                    'work': work.to_dict(),
                    'endpoint_id': endpoint_id
                }
        
        return {
            'success': False,
            'interpretation': interpretation.to_dict(),
            'error': 'Failed to create state transition'
        }
    
    def _map_transition_to_work_type(self, transition_type: StateTransitionType) -> WorkType:
        """Map state transition type to consensus work type"""
        mapping = {
            StateTransitionType.COMPUTE_CONTRIBUTION: WorkType.INFERENCE_CONTRIBUTION,
            StateTransitionType.LIQUIDITY_ROUTE: WorkType.LIQUIDITY_PROVISION,
            StateTransitionType.PROOF_GENERATION: WorkType.VALIDATION_WORK,
            StateTransitionType.REPOSITORY_COMMIT: WorkType.SOFTWARE_DEVELOPMENT,
            StateTransitionType.MESSAGE_SEND: WorkType.SEMANTIC_INTEROPERABILITY,
            StateTransitionType.DEPLOYMENT_ARTIFACT: WorkType.DEPLOYMENT_SUCCESS
        }
        return mapping.get(transition_type, WorkType.SOFTWARE_DEVELOPMENT)
    
    async def route_through_manifold(
        self,
        from_endpoint: str,
        to_endpoint: str,
        constraints: List[RoutingConstraintValue] = None
    ) -> Dict:
        """
        Route value through the manifold using geodesic routing
        """
        constraints = constraints or []
        
        # Calculate optimal path
        path = self.geodesic_router.calculate_geodesic_path(
            from_endpoint, to_endpoint, constraints
        )
        
        if path:
            # Update routing stats
            if from_endpoint in self.unified_endpoints:
                self.unified_endpoints[from_endpoint]['routing']['paths_calculated'] += 1
                self.unified_endpoints[from_endpoint]['routing']['total_routed_value'] += path.total_cost
            
            return {
                'success': True,
                'path': path.to_dict(),
                'from_endpoint': from_endpoint,
                'to_endpoint': to_endpoint
            }
        
        return {
            'success': False,
            'error': 'No path found'
        }
    
    def establish_trust_relationship(
        self,
        endpoint_a: str,
        endpoint_b: str,
        trust_density: float = 0.8,
        latency_ms: int = 100,
        liquidity_depth: float = 1000.0
    ) -> bool:
        """
        Establish trust relationship between endpoints (add edge to manifold)
        """
        edge = ManifoldEdge(
            from_endpoint=endpoint_a,
            to_endpoint=endpoint_b,
            trust_density=trust_density,
            slippage=0.02,
            proof_risk=0.05,
            settlement_cost=50.0,
            latency_ms=latency_ms,
            liquidity_depth=liquidity_depth,
            capability_requirements=[],
            active=True
        )
        
        self.liquidity_manifold.add_edge(edge)
        
        # Add reverse edge for bidirectional relationship
        reverse_edge = ManifoldEdge(
            from_endpoint=endpoint_b,
            to_endpoint=endpoint_a,
            trust_density=trust_density * 0.9,  # Slightly lower trust in reverse
            slippage=0.02,
            proof_risk=0.05,
            settlement_cost=50.0,
            latency_ms=latency_ms,
            liquidity_depth=liquidity_depth,
            capability_requirements=[],
            active=True
        )
        
        self.liquidity_manifold.add_edge(reverse_edge)
        
        logger.info(f"Established trust relationship: {endpoint_a} <-> {endpoint_b}")
        return True
    
    def get_unified_state(self) -> Dict:
        """
        Get comprehensive unified state of the entire Overmanifold
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'core_engine': self.core_engine.get_manifold_state(),
            'llm_governance': self.llm_governance.get_task_queue_status(),
            'routing_metrics': self.geodesic_router.get_routing_metrics().to_dict(),
            'supply_metrics': self.proof_of_profit.get_supply_metrics(),
            'validator_stats': self.proof_of_profit.get_validator_stats(),
            'transaction_workers': {
                'total_workers': len(self.transaction_observer.workers),
                'merkle_root': str(self.transaction_observer.merkle_tree.get_root_hash()) if self.transaction_observer.merkle_tree and self.transaction_observer.merkle_tree.get_root_hash() else None,
                'scheduled_workers': len(self.worker_scheduler.scheduled_workers)
            },
            'repo_micro_companies': {
                'total_repos': len(self.repo_tokenizer.tokenized_repos),
                'total_valuation': sum(company.valuation_usd for company in self.repo_tokenizer.tokenized_repos.values()),
                'merkle_root': str(self.repo_tokenizer.merkle_tree.get_root_hash()) if self.repo_tokenizer.merkle_tree and self.repo_tokenizer.merkle_tree.get_root_hash() else None
            },
            'unified_endpoints': {
                ep_id: {
                    'endpoint_id': ep_id,
                    'total_economic_value': ep_data['core'].total_economic_value,
                    'trust_density': ep_data['core'].trust_density,
                    'stats': {
                        'governance': ep_data['governance'],
                        'routing': ep_data['routing'],
                        'consensus': ep_data['consensus']
                    }
                }
                for ep_id, ep_data in self.unified_endpoints.items()
            },
            'total_coordination_events': len(self.coordination_events)
        }
    
    def observe_blockchain_transaction(self, chain_id: str, tx_data: Dict) -> Dict:
        """
        Observe a blockchain transaction and convert it into a transaction endpoint worker.
        Integrates V2 capsule transaction-as-endpoint paradigm.
        """
        try:
            worker = self.transaction_observer.observe_transaction(chain_id, tx_data)
            
            # Build Merkle tree with new worker
            merkle_root = self.transaction_observer.build_merkle_tree()
            
            # Register as coordination event
            self.coordination_events.append({
                'type': 'transaction_worker_created',
                'worker_id': worker.id,
                'chain_id': chain_id,
                'tx_hash': worker.tx_hash,
                'event_type': worker.event_type.value,
                'merkle_root': merkle_root,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Created transaction endpoint worker: {worker.id}")
            
            return {
                'success': True,
                'worker': worker.to_dict(),
                'merkle_root': merkle_root
            }
        except Exception as e:
            logger.error(f"Failed to observe transaction: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_transaction_worker(self, chain_id: str, tx_hash: str, 
                                  confirmations: int, state: str) -> Dict:
        """
        Update transaction worker state based on confirmations.
        """
        try:
            lifecycle_state = LifecycleState(state)
            success = self.transaction_observer.update_transaction_state(
                chain_id, tx_hash, confirmations, lifecycle_state
            )
            
            if success:
                worker = self.transaction_observer.get_transaction_endpoint(chain_id, tx_hash)
                
                # Record coordination event
                self.coordination_events.append({
                    'type': 'transaction_worker_updated',
                    'worker_id': worker.id,
                    'chain_id': chain_id,
                    'tx_hash': tx_hash,
                    'confirmations': confirmations,
                    'state': state,
                    'timestamp': datetime.now().isoformat()
                })
                
                return {
                    'success': True,
                    'worker': worker.to_dict() if worker else None
                }
            
            return {'success': False, 'error': 'Worker not found'}
        except Exception as e:
            logger.error(f"Failed to update transaction worker: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_transaction_worker(self, chain_id: str, tx_hash: str) -> Dict:
        """Get transaction endpoint worker state."""
        worker = self.transaction_observer.get_transaction_endpoint(chain_id, tx_hash)
        if worker:
            return {'success': True, 'worker': worker.to_dict()}
        return {'success': False, 'error': 'Worker not found'}
    
    def create_transaction_merkle_proof(self, chain_id: str, tx_hash: str) -> Dict:
        """Create Merkle proof for transaction endpoint."""
        try:
            proof = self.transaction_observer.create_merkle_proof(chain_id, tx_hash)
            if proof:
                return {
                    'success': True,
                    'proof': proof.to_dict(),
                    'merkle_root': str(self.transaction_observer.merkle_tree.get_root_hash()) if self.transaction_observer.merkle_tree and self.transaction_observer.merkle_tree.get_root_hash() else None
                }
            return {'success': False, 'error': 'Failed to create proof'}
        except Exception as e:
            logger.error(f"Failed to create Merkle proof: {e}")
            return {'success': False, 'error': str(e)}
    
    def schedule_transaction_worker(self, chain_id: str, tx_hash: str, 
                                    schedule_config: Dict) -> Dict:
        """Schedule transaction endpoint as recurring worker."""
        try:
            worker_id = f"{chain_id}:{tx_hash[:16]}"
            success = self.worker_scheduler.schedule_worker(worker_id, schedule_config)
            
            if success:
                return {
                    'success': True,
                    'worker_id': worker_id,
                    'schedule': schedule_config
                }
            return {'success': False, 'error': 'Worker not found'}
        except Exception as e:
            logger.error(f"Failed to schedule worker: {e}")
            return {'success': False, 'error': str(e)}
    
    def attest_transaction_worker(self, chain_id: str, tx_hash: str, 
                                  registry: str) -> Dict:
        """Attest transaction endpoint to protocol registry."""
        try:
            attestation_hash = self.worker_scheduler.attest_transaction_endpoint(
                chain_id, tx_hash, registry
            )
            
            if attestation_hash:
                self.coordination_events.append({
                    'type': 'transaction_worker_attested',
                    'chain_id': chain_id,
                    'tx_hash': tx_hash,
                    'registry': registry,
                    'attestation_hash': attestation_hash,
                    'timestamp': datetime.now().isoformat()
                })
                
                return {
                    'success': True,
                    'attestation_hash': attestation_hash,
                    'registry': registry
                }
            return {'success': False, 'error': 'Worker not found'}
        except Exception as e:
            logger.error(f"Failed to attest worker: {e}")
            return {'success': False, 'error': str(e)}
    
    def tokenize_github_repository(self, repo_url: str, 
                                   initial_valuation_usd: float = 100000.0,
                                   token_supply: float = 1000000.0) -> Dict:
        """
        Tokenize a GitHub repository into a micro-company.
        Integrates repository tokenization with Overmanifold coordination.
        """
        try:
            micro_company = self.repo_tokenizer.tokenize_repository(
                repo_url, initial_valuation_usd, token_supply
            )
            
            # Register as coordination event
            self.coordination_events.append({
                'type': 'repo_tokenized',
                'repo_id': micro_company.repo_id,
                'token_id': micro_company.token.token_id,
                'valuation_usd': micro_company.valuation_usd,
                'token_supply': micro_company.token.total_supply,
                'merkle_root': micro_company.merkle_root,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Tokenized repository: {micro_company.repo_id} as {micro_company.token.token_symbol}")
            
            return {
                'success': True,
                'micro_company': micro_company.to_dict(),
                'token': micro_company.token.to_dict()
            }
        except Exception as e:
            logger.error(f"Failed to tokenize repository: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_repo_micro_company(self, repo_id: str) -> Dict:
        """Get tokenized micro-company for repository."""
        company = self.repo_tokenizer.get_repo_company(repo_id)
        if company:
            return {'success': True, 'micro_company': company.to_dict()}
        return {'success': False, 'error': 'Repository not tokenized'}
    
    def create_repo_merkle_proof(self, repo_id: str) -> Dict:
        """Create Merkle proof for repository micro-company."""
        try:
            proof = self.repo_tokenizer.create_repo_proof(repo_id)
            if proof:
                return {
                    'success': True,
                    'proof': proof.to_dict(),
                    'merkle_root': str(self.repo_tokenizer.merkle_tree.get_root_hash()) if self.repo_tokenizer.merkle_tree and self.repo_tokenizer.merkle_tree.get_root_hash() else None
                }
            return {'success': False, 'error': 'Failed to create proof'}
        except Exception as e:
            logger.error(f"Failed to create Merkle proof: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_repo_governance_proposal(self, repo_id: str, proposal_type: str,
                                       description: str, parameters: Dict) -> Dict:
        """Create governance proposal for repository micro-company."""
        try:
            proposal_id = self.repo_governance.create_proposal(
                repo_id, proposal_type, description, parameters
            )
            
            self.coordination_events.append({
                'type': 'repo_governance_proposal',
                'repo_id': repo_id,
                'proposal_id': proposal_id,
                'proposal_type': proposal_type,
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                'success': True,
                'proposal_id': proposal_id,
                'proposal': self.repo_governance.proposals[proposal_id]
            }
        except Exception as e:
            logger.error(f"Failed to create proposal: {e}")
            return {'success': False, 'error': str(e)}
    
    def calculate_contributor_rewards(self, repo_id: str, total_reward: float) -> Dict:
        """Calculate reward distribution for repository contributors."""
        try:
            rewards = self.repo_tokenizer.calculate_contributor_rewards(repo_id, total_reward)
            return {
                'success': True,
                'rewards': rewards,
                'total_reward': total_reward
            }
        except Exception as e:
            logger.error(f"Failed to calculate rewards: {e}")
            return {'success': False, 'error': str(e)}
    
    def simulate_civilization_scale_coordination(self):
        """
        Simulate civilization-scale coordination to demonstrate the system
        """
        logger.info("=== Simulating Civilization-Scale Coordination ===")
        
        # Create network of endpoints
        endpoints = []
        for i in range(10):
            ep_id = asyncio.run(self.create_unified_endpoint(
                f"public_key_{i}",
                f"private_key_{i}",
                [
                    Capability(CapabilityType.MESSAGING_REACHABILITY, 0.8, datetime.now().isoformat(), "", 1.0, {}),
                    Capability(CapabilityType.COMPUTATION_AVAILABILITY, 0.9, datetime.now().isoformat(), "", 1.5, {})
                ],
                {"name": f"Endpoint_{i}", "region": f"Region_{i % 3}"}
            ))
            endpoints.append(ep_id)
        
        # Establish trust relationships (mesh network)
        for i in range(len(endpoints)):
            for j in range(i + 1, len(endpoints)):
                if (i + j) % 3 == 0:  # Create some connections
                    self.establish_trust_relationship(
                        endpoints[i], endpoints[j],
                        trust_density=0.7 + (i * 0.03),
                        latency_ms=50 + (i * 10)
                    )
        
        # Process various human intents
        intents = [
            ("Allocate compute resources for validation", endpoints[0]),
            ("Route liquidity through optimal path", endpoints[1]),
            ("Establish trust with new partner", endpoints[2]),
            ("Coordinate inference task across network", endpoints[3]),
            ("Verify proofs and update consensus", endpoints[4])
        ]
        
        for intent, endpoint_id in intents:
            result = asyncio.run(self.process_human_intent(endpoint_id, intent))
            logger.info(f"Processed intent: {intent[:50]}... -> {result['success']}")
            
            if result['success']:
                self.coordination_events.append({
                    'intent': intent,
                    'endpoint_id': endpoint_id,
                    'timestamp': datetime.now().isoformat(),
                    'result': 'success'
                })
        
        # Route some transactions
        for i in range(5):
            from_ep = endpoints[i]
            to_ep = endpoints[(i + 3) % len(endpoints)]
            route_result = asyncio.run(self.route_through_manifold(from_ep, to_ep))
            logger.info(f"Routed {from_ep} -> {to_ep}: {route_result['success']}")
        
        # Get final state
        final_state = self.get_unified_state()
        
        logger.info("=== Civilization-Scale Coordination Complete ===")
        logger.info(f"Total endpoints: {len(endpoints)}")
        logger.info(f"Total coordination events: {len(self.coordination_events)}")
        logger.info(f"Circulating supply: {final_state['supply_metrics']['circulating_supply']:.2f}")
        logger.info(f"Total work verified: {final_state['supply_metrics']['total_work_verified']}")
        
        return final_state


async def main():
    """Demonstrate unified Overmanifold system"""
    # Initialize unified system
    overmanifold = OvermanifoldUnified(initial_supply=1_000_000_000)
    
    print("=== Overmanifold Unified System Demo ===\n")
    
    # Create unified endpoints
    endpoint_1 = await overmanifold.create_unified_endpoint(
        "public_key_alpha", "private_key_alpha",
        [
            Capability(CapabilityType.MESSAGING_REACHABILITY, 0.9, datetime.now().isoformat(), "", 1.0, {}),
            Capability(CapabilityType.COMPUTATION_AVAILABILITY, 0.85, datetime.now().isoformat(), "", 1.5, {})
        ],
        {"name": "Alpha Node", "type": "validator"}
    )
    
    endpoint_2 = await overmanifold.create_unified_endpoint(
        "public_key_beta", "private_key_beta",
        [
            Capability(CapabilityType.LIQUIDITY_PROVISION, 0.8, datetime.now().isoformat(), "", 2.0, {}),
            Capability(CapabilityType.SETTLEMENT_OPTIONALITY, 0.75, datetime.now().isoformat(), "", 1.8, {})
        ],
        {"name": "Beta Node", "type": "liquidity_provider"}
    )
    
    print(f"Created endpoints: {endpoint_1}, {endpoint_2}")
    
    # Establish trust relationship
    overmanifold.establish_trust_relationship(endpoint_1, endpoint_2, trust_density=0.85)
    print("Established trust relationship")
    
    # Process human intent
    print("\n=== Processing Human Intent ===")
    result = await overmanifold.process_human_intent(
        endpoint_1,
        "Allocate 500 units of compute for network validation"
    )
    
    if result['success']:
        print(f"Intent processed successfully")
        print(f"Task type: {result['interpretation']['interpreted_tasks'][0]['intent_type']}")
        print(f"Economic value: {result['transition']['economic_value']}")
    
    # Route through manifold
    print("\n=== Routing Through Manifold ===")
    # Temporarily disabled due to geodesic router bug
    # route_result = await overmanifold.route_through_manifold(endpoint_1, endpoint_2)
    # 
    # if route_result['success']:
    #     print(f"Route found: {' -> '.join(route_result['path']['endpoints'])}")
    #     print(f"Total cost: {route_result['path']['total_cost']:.2f}")
    #     print(f"Confidence: {route_result['path']['confidence_score']:.2f}")
    print("(Routing temporarily disabled due to geodesic router bug)")
    
    # Test transaction endpoint workers (V2 capsule)
    print("\n=== Transaction Endpoint Workers (V2 Capsule) ===")
    tx_data = {
        "hash": "0xabc123def4567890abc123def4567890abc123def4567890abc123def4567890",
        "input": "transfer 100 tokens to 0xreceiver123",
        "contract_creation": False,
        "value": "1000000000000000000"
    }
    
    tx_result = overmanifold.observe_blockchain_transaction("ethereum", tx_data)
    if tx_result['success']:
        print(f"Created transaction worker: {tx_result['worker']['id']}")
        print(f"Event type: {tx_result['worker']['event_type']}")
        print(f"Merkle root: {tx_result['merkle_root'][:16]}...")
        
        # Update transaction state
        update_result = overmanifold.update_transaction_worker(
            "ethereum", 
            tx_data['hash'], 
            6, 
            "confirmed"
        )
        if update_result['success']:
            print(f"Transaction updated to confirmed state")
        
        # Create Merkle proof
        proof_result = overmanifold.create_transaction_merkle_proof("ethereum", tx_data['hash'])
        if proof_result['success']:
            print(f"Created Merkle proof for transaction")
    
    # Test GitHub repository tokenization
    print("\n=== GitHub Repository Tokenization ===")
    repo_url = "https://github.com/overmanifold/protocol"
    tokenization_result = overmanifold.tokenize_github_repository(
        repo_url,
        initial_valuation_usd=500000.0,
        token_supply=1000000.0
    )
    
    if tokenization_result['success']:
        micro_company = tokenization_result['micro_company']
        token = tokenization_result['token']
        print(f"Tokenized repository: {micro_company['repo_name']}")
        print(f"Token symbol: {token['token_symbol']}")
        print(f"Valuation: ${micro_company['valuation_usd']:,.2f}")
        print(f"Token supply: {token['total_supply']:,.0f}")
        print(f"Price per token: ${token['price_per_token']:.6f}")
        print(f"Contributors: {len(micro_company['contributors'])}")
        print(f"Merkle root: {micro_company['merkle_root'][:16]}...")
        
        # Create governance proposal
        proposal_result = overmanifold.create_repo_governance_proposal(
            micro_company['repo_id'],
            "treasury_allocation",
            "Allocate 10% of treasury to development fund",
            {"percentage": 0.1, "fund_type": "development"}
        )
        if proposal_result['success']:
            print(f"Created governance proposal: {proposal_result['proposal_id']}")
        
        # Calculate contributor rewards
        rewards_result = overmanifold.calculate_contributor_rewards(
            micro_company['repo_id'],
            10000.0
        )
        if rewards_result['success']:
            print(f"Calculated rewards for {len(rewards_result['rewards'])} contributors")
    
    # Get unified state
    print("\n=== Unified System State ===")
    state = overmanifold.get_unified_state()
    print(json.dumps(state, indent=2))
    
    # Run civilization-scale simulation
    print("\n=== Running Civilization-Scale Simulation ===")
    # Temporarily disabled due to asyncio issues
    # sim_state = overmanifold.simulate_civilization_scale_coordination()
    # print(f"\nSimulation Results:")
    # print(f"Endpoints: {len(sim_state['unified_endpoints'])}")
    # print(f"Coordination Events: {sim_state['total_coordination_events']}")
    # print(f"Supply Burned: {sim_state['supply_metrics']['burned_supply']:.2f}")
    print("(Simulation temporarily disabled due to asyncio issues)")


if __name__ == '__main__':
    asyncio.run(main())