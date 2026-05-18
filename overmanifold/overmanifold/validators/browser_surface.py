"""
Overmanifold Browser-Native Validator Surfaces
WebAssembly/WebGPU validation framework for client-side state transition verification.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib
import base64

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.types import Hash, StateTransition, StateTransitionType
from merkle.proof import MerkleProof


class ValidationTarget(Enum):
    """Targets for browser-based validation."""
    STATE_TRANSITION = "state_transition"
    MERKLE_PROOF = "merkle_proof"
    SIGNATURE = "signature"
    CONSENSUS_PROOF = "consensus_proof"
    LIQUIDITY_PROOF = "liquidity_proof"
    GOVERNANCE_PROOF = "governance_proof"


class ComputeBackend(Enum):
    """Compute backends for validation."""
    CPU = "cpu"
    WEBGPU = "webgpu"
    WEBASSEMBLY = "wasm"
    HYBRID = "hybrid"


@dataclass
class ValidationTask:
    """A validation task to be executed in the browser."""
    task_id: str
    target: ValidationTarget
    data: Dict
    priority: int = 0
    timeout_ms: int = 5000
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "target": self.target.value,
            "data": self.data,
            "priority": self.priority,
            "timeout_ms": self.timeout_ms,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    task_id: str
    valid: bool
    confidence: float
    execution_time_ms: float
    backend_used: ComputeBackend
    error_message: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            "task_id": self.task_id,
            "valid": self.valid,
            "confidence": self.confidence,
            "execution_time_ms": self.execution_time_ms,
            "backend_used": self.backend_used.value,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


@dataclass
class ValidatorSurface:
    """
    A browser-native validator surface.
    Provides WebAssembly/WebGPU validation capabilities.
    """
    surface_id: str
    name: str
    supported_targets: List[ValidationTarget]
    compute_backend: ComputeBackend
    max_concurrent_tasks: int = 4
    active_tasks: int = 0
    total_validations: int = 0
    success_rate: float = 1.0
    average_execution_time_ms: float = 0.0
    last_heartbeat: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert surface to dictionary."""
        return {
            "surface_id": self.surface_id,
            "name": self.name,
            "supported_targets": [t.value for t in self.supported_targets],
            "compute_backend": self.compute_backend.value,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "active_tasks": self.active_tasks,
            "total_validations": self.total_validations,
            "success_rate": self.success_rate,
            "average_execution_time_ms": self.average_execution_time_ms,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }


class WebAssemblyValidator:
    """
    WebAssembly-based validator for high-performance validation.
    In production, this would load actual WASM modules.
    """
    
    def __init__(self):
        self.wasm_module = None
        self.loaded = False
        self.supported_operations = [
            ValidationTarget.STATE_TRANSITION,
            ValidationTarget.SIGNATURE,
            ValidationTarget.MERKLE_PROOF
        ]
    
    def load_wasm_module(self, wasm_bytes: bytes) -> bool:
        """Load WebAssembly module."""
        # In production, this would use WebAssembly.instantiate()
        # For now, we simulate successful loading
        self.wasm_module = hashlib.sha256(wasm_bytes).hexdigest()
        self.loaded = True
        return True
    
    def validate_state_transition(self, transition: Dict) -> ValidationResult:
        """Validate state transition using WASM."""
        start_time = datetime.utcnow()
        
        try:
            # Simulated WASM validation
            # In production, this would call actual WASM functions
            transition_hash = self._compute_transition_hash(transition)
            valid = len(transition_hash) == 64  # Simple validation
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ValidationResult(
                task_id=f"wasm_{datetime.utcnow().timestamp()}",
                valid=valid,
                confidence=0.95 if valid else 0.0,
                execution_time_ms=execution_time,
                backend_used=ComputeBackend.WEBASSEMBLY,
                metadata={"wasm_module": self.wasm_module}
            )
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ValidationResult(
                task_id=f"wasm_{datetime.utcnow().timestamp()}",
                valid=False,
                confidence=0.0,
                execution_time_ms=execution_time,
                backend_used=ComputeBackend.WEBASSEMBLY,
                error_message=str(e)
            )
    
    def _compute_transition_hash(self, transition: Dict) -> str:
        """Compute hash of state transition."""
        return hashlib.sha256(json.dumps(transition, sort_keys=True).encode()).hexdigest()


class WebGPUValidator:
    """
    WebGPU-based validator for parallel proof verification.
    In production, this would use actual WebGPU compute shaders.
    """
    
    def __init__(self):
        self.gpu_device = None
        self.compute_shaders = {}
        self.loaded = False
        self.supported_operations = [
            ValidationTarget.MERKLE_PROOF,
            ValidationTarget.CONSENSUS_PROOF,
            ValidationTarget.LIQUIDITY_PROOF
        ]
    
    def initialize_gpu(self) -> bool:
        """Initialize WebGPU device."""
        # In production, this would use navigator.gpu.requestAdapter()
        # For now, we simulate successful initialization
        self.gpu_device = f"simulated_gpu_{hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:8]}"
        self.loaded = True
        return True
    
    def validate_merkle_proof_parallel(self, proof: MerkleProof, 
                                      expected_root: str) -> ValidationResult:
        """Validate Merkle proof using WebGPU parallel computation."""
        start_time = datetime.utcnow()
        
        try:
            # Simulated WebGPU validation
            # In production, this would use compute shaders for parallel hash verification
            current_hash = proof.leaf_hash
            
            for sibling_hash, is_left in proof.proof_path:
                if is_left:
                    combined = sibling_hash.value + current_hash.value
                else:
                    combined = current_hash.value + sibling_hash.value
                
                current_hash = Hash.from_data(combined)
            
            valid = current_hash.value == expected_root
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ValidationResult(
                task_id=f"webgpu_{datetime.utcnow().timestamp()}",
                valid=valid,
                confidence=0.98 if valid else 0.0,
                execution_time_ms=execution_time,
                backend_used=ComputeBackend.WEBGPU,
                metadata={"gpu_device": self.gpu_device, "proof_path_length": len(proof.proof_path)}
            )
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ValidationResult(
                task_id=f"webgpu_{datetime.utcnow().timestamp()}",
                valid=False,
                confidence=0.0,
                execution_time_ms=execution_time,
                backend_used=ComputeBackend.WEBGPU,
                error_message=str(e)
            )
    
    def validate_batch_proofs(self, proofs: List[MerkleProof], 
                             roots: List[str]) -> List[ValidationResult]:
        """Validate multiple proofs in parallel using WebGPU."""
        start_time = datetime.utcnow()
        results = []
        
        for proof, root in zip(proofs, roots):
            result = self.validate_merkle_proof_parallel(proof, root)
            results.append(result)
        
        return results


class BrowserValidatorSurface:
    """
    Manager for browser-native validator surfaces.
    Coordinates WebAssembly and WebGPU validation.
    """
    
    def __init__(self):
        self.surfaces: Dict[str, ValidatorSurface] = {}
        self.validation_queue: List[ValidationTask] = []
        self.results: Dict[str, ValidationResult] = {}
        self.wasm_validator = WebAssemblyValidator()
        self.webgpu_validator = WebGPUValidator()
        self.task_callbacks: Dict[str, Callable] = {}
        
        # Initialize default surfaces
        self._initialize_default_surfaces()
    
    def _initialize_default_surfaces(self) -> None:
        """Initialize default validator surfaces."""
        # WebAssembly surface
        wasm_surface = ValidatorSurface(
            surface_id="wasm_primary",
            name="Primary WebAssembly Validator",
            supported_targets=self.wasm_validator.supported_operations,
            compute_backend=ComputeBackend.WEBASSEMBLY,
            max_concurrent_tasks=8
        )
        self.surfaces[wasm_surface.surface_id] = wasm_surface
        
        # WebGPU surface
        webgpu_surface = ValidatorSurface(
            surface_id="webgpu_primary",
            name="Primary WebGPU Validator",
            supported_targets=self.webgpu_validator.supported_operations,
            compute_backend=ComputeBackend.WEBGPU,
            max_concurrent_tasks=4
        )
        self.surfaces[webgpu_surface.surface_id] = webgpu_surface
    
    def register_surface(self, surface: ValidatorSurface) -> bool:
        """Register a new validator surface."""
        self.surfaces[surface.surface_id] = surface
        return True
    
    def submit_validation_task(self, task: ValidationTask, 
                               callback: Optional[Callable] = None) -> ValidationResult:
        """Submit a validation task for execution."""
        task.task_id = f"task_{datetime.utcnow().timestamp()}_{len(self.validation_queue)}"
        self.validation_queue.append(task)
        
        if callback:
            self.task_callbacks[task.task_id] = callback
        
        # Execute task immediately for demo
        result = self._execute_task(task)
        
        return result
    
    def _execute_task(self, task: ValidationTask) -> ValidationResult:
        """Execute a validation task on appropriate surface."""
        # Find suitable surface
        surface = self._find_suitable_surface(task.target)
        
        if not surface:
            return ValidationResult(
                task_id=task.task_id,
                valid=False,
                confidence=0.0,
                execution_time_ms=0.0,
                backend_used=ComputeBackend.CPU,
                error_message="No suitable validator surface found"
            )
        
        # Update surface stats
        surface.active_tasks += 1
        surface.last_heartbeat = datetime.utcnow()
        
        # Execute validation based on backend
        result = None
        if surface.compute_backend == ComputeBackend.WEBASSEMBLY:
            if task.target == ValidationTarget.STATE_TRANSITION:
                result = self.wasm_validator.validate_state_transition(task.data)
            elif task.target == ValidationTarget.SIGNATURE:
                result = self._validate_signature_wasm(task.data)
            elif task.target == ValidationTarget.MERKLE_PROOF:
                result = self._validate_merkle_wasm(task.data)
        elif surface.compute_backend == ComputeBackend.WEBGPU:
            if task.target == ValidationTarget.MERKLE_PROOF:
                result = self._validate_merkle_webgpu(task.data)
            elif task.target == ValidationTarget.CONSENSUS_PROOF:
                result = self._validate_consensus_webgpu(task.data)
        
        # Fallback to CPU if no result
        if not result:
            result = self._validate_cpu(task)
        
        # Update surface stats
        surface.active_tasks -= 1
        surface.total_validations += 1
        
        # Update success rate and average time
        if surface.total_validations > 0:
            surface.success_rate = (surface.success_rate * (surface.total_validations - 1) + 
                                  (1.0 if result.valid else 0.0)) / surface.total_validations
            surface.average_execution_time_ms = (
                surface.average_execution_time_ms * (surface.total_validations - 1) + 
                result.execution_time_ms
            ) / surface.total_validations
        
        # Store result
        self.results[task.task_id] = result
        
        # Execute callback if registered
        if task.task_id in self.task_callbacks:
            self.task_callbacks[task.task_id](result)
            del self.task_callbacks[task.task_id]
        
        return result
    
    def _find_suitable_surface(self, target: ValidationTarget) -> Optional[ValidatorSurface]:
        """Find a validator surface that supports the target."""
        for surface in self.surfaces.values():
            if target in surface.supported_targets and surface.active_tasks < surface.max_concurrent_tasks:
                return surface
        return None
    
    def _validate_signature_wasm(self, data: Dict) -> ValidationResult:
        """Validate signature using WASM."""
        start_time = datetime.utcnow()
        # Simplified signature validation
        valid = "signature" in data and "public_key" in data
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return ValidationResult(
            task_id=f"wasm_sig_{datetime.utcnow().timestamp()}",
            valid=valid,
            confidence=0.9 if valid else 0.0,
            execution_time_ms=execution_time,
            backend_used=ComputeBackend.WEBASSEMBLY
        )
    
    def _validate_merkle_wasm(self, data: Dict) -> ValidationResult:
        """Validate Merkle proof using WASM."""
        start_time = datetime.utcnow()
        # Simplified Merkle validation
        valid = "leaf_hash" in data and "root_hash" in data
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return ValidationResult(
            task_id=f"wasm_merkle_{datetime.utcnow().timestamp()}",
            valid=valid,
            confidence=0.85 if valid else 0.0,
            execution_time_ms=execution_time,
            backend_used=ComputeBackend.WEBASSEMBLY
        )
    
    def _validate_merkle_webgpu(self, data: Dict) -> ValidationResult:
        """Validate Merkle proof using WebGPU."""
        start_time = datetime.utcnow()
        # Simplified WebGPU Merkle validation
        valid = "proof_path" in data and len(data.get("proof_path", [])) > 0
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return ValidationResult(
            task_id=f"webgpu_merkle_{datetime.utcnow().timestamp()}",
            valid=valid,
            confidence=0.95 if valid else 0.0,
            execution_time_ms=execution_time,
            backend_used=ComputeBackend.WEBGPU
        )
    
    def _validate_consensus_webgpu(self, data: Dict) -> ValidationResult:
        """Validate consensus proof using WebGPU."""
        start_time = datetime.utcnow()
        # Simplified consensus validation
        valid = "work_proof" in data and "validator_signature" in data
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return ValidationResult(
            task_id=f"webgpu_consensus_{datetime.utcnow().timestamp()}",
            valid=valid,
            confidence=0.92 if valid else 0.0,
            execution_time_ms=execution_time,
            backend_used=ComputeBackend.WEBGPU
        )
    
    def _validate_cpu(self, task: ValidationTask) -> ValidationResult:
        """Fallback CPU validation."""
        start_time = datetime.utcnow()
        # Simplified CPU validation
        valid = bool(task.data)
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        return ValidationResult(
            task_id=task.task_id,
            valid=valid,
            confidence=0.7 if valid else 0.0,
            execution_time_ms=execution_time,
            backend_used=ComputeBackend.CPU
        )
    
    def get_validation_result(self, task_id: str) -> Optional[ValidationResult]:
        """Get result of a validation task."""
        return self.results.get(task_id)
    
    def get_surface_stats(self) -> Dict[str, Dict]:
        """Get statistics for all validator surfaces."""
        return {surface_id: surface.to_dict() for surface_id, surface in self.surfaces.items()}
    
    def generate_javascript_bindings(self) -> str:
        """
        Generate JavaScript bindings for browser integration.
        This would be used in actual browser environments.
        """
        js_code = """
class OvermanifoldValidator {
    constructor() {
        this.surfaces = {};
        this.taskQueue = [];
        this.results = {};
    }
    
    async validateStateTransition(transition) {
        const taskId = 'task_' + Date.now();
        const task = {
            taskId: taskId,
            target: 'state_transition',
            data: transition,
            priority: 0
        };
        
        // In production, this would communicate with WebAssembly/WebGPU
        const result = await this.executeValidation(task);
        this.results[taskId] = result;
        return result;
    }
    
    async validateMerkleProof(proof, expectedRoot) {
        const taskId = 'task_' + Date.now();
        const task = {
            taskId: taskId,
            target: 'merkle_proof',
            data: { proof, expectedRoot },
            priority: 1
        };
        
        const result = await this.executeValidation(task);
        this.results[taskId] = result;
        return result;
    }
    
    async executeValidation(task) {
        // Simulated validation - in production would use actual WASM/WebGPU
        return {
            taskId: task.taskId,
            valid: true,
            confidence: 0.95,
            executionTimeMs: 15.5,
            backendUsed: 'wasm'
        };
    }
    
    getSurfaceStats() {
        return this.surfaces;
    }
}

// Export for browser use
if (typeof window !== 'undefined') {
    window.OvermanifoldValidator = OvermanifoldValidator;
}
"""
        return js_code


class ValidatorSurfaceIntegration:
    """
    Integration layer for validator surfaces with Overmanifold unified system.
    """
    
    def __init__(self, browser_validator: BrowserValidatorSurface):
        self.browser_validator = browser_validator
        self.integration_stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "average_confidence": 0.0,
            "backend_distribution": {}
        }
    
    def integrate_with_unified_system(self, unified_system) -> None:
        """Integrate validator surfaces with unified Overmanifold system."""
        # Register validator hooks with unified system
        unified_system.validator_integration = self
    
    def validate_unified_state_transition(self, transition: Dict) -> ValidationResult:
        """Validate a state transition from the unified system."""
        task = ValidationTask(
            task_id="",
            target=ValidationTarget.STATE_TRANSITION,
            data=transition,
            priority=1
        )
        
        result = self.browser_validator.submit_validation_task(task)
        self._update_integration_stats(result)
        
        return result
    
    def _update_integration_stats(self, result: ValidationResult) -> None:
        """Update integration statistics."""
        self.integration_stats["total_validations"] += 1
        if result.valid:
            self.integration_stats["successful_validations"] += 1
        
        # Update average confidence
        total = self.integration_stats["total_validations"]
        current_avg = self.integration_stats["average_confidence"]
        self.integration_stats["average_confidence"] = (
            (current_avg * (total - 1) + result.confidence) / total
        )
        
        # Update backend distribution
        backend = result.backend_used.value
        if backend not in self.integration_stats["backend_distribution"]:
            self.integration_stats["backend_distribution"][backend] = 0
        self.integration_stats["backend_distribution"][backend] += 1
    
    def get_integration_stats(self) -> Dict:
        """Get integration statistics."""
        return self.integration_stats