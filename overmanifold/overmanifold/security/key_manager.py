"""
Overmanifold Key Management System
Securely manages API keys, private keys, and sensitive credentials.
"""

import os
import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from overmanifold.infrastructure.logging_config import get_logger

logger = get_logger("key_manager")


class KeyManager:
    """
    Secure key management system for production use
    Handles encryption, storage, and retrieval of sensitive keys
    """
    
    def __init__(self, master_password: Optional[str] = None):
        """
        Initialize key manager
        
        Args:
            master_password: Master password for encryption (if None, uses environment variable)
        """
        self.master_password = master_password or os.getenv("KEY_MANAGER_PASSWORD", "")
        if not self.master_password:
            raise ValueError("KEY_MANAGER_PASSWORD environment variable must be set")
        
        self.key_file = os.getenv("KEY_FILE_PATH", "keys.enc")
        self.cipher_suite = self._create_cipher_suite()
        self.keys: Dict[str, str] = {}
        
        # Load existing keys if available
        if os.path.exists(self.key_file):
            self._load_keys()
    
    def _create_cipher_suite(self) -> Fernet:
        """Create encryption cipher suite from master password"""
        password_bytes = self.master_password.encode()
        salt = b'overmanifold_salt'  # In production, use random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)
    
    def _load_keys(self) -> None:
        """Load encrypted keys from storage"""
        try:
            with open(self.key_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            self.keys = json.loads(decrypted_data.decode())
            logger.info(f"Loaded {len(self.keys)} encrypted keys")
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")
            self.keys = {}
    
    def _save_keys(self) -> None:
        """Save encrypted keys to storage"""
        try:
            encrypted_data = self.cipher_suite.encrypt(
                json.dumps(self.keys).encode()
            )
            
            with open(self.key_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
            logger.info(f"Saved {len(self.keys)} encrypted keys")
        except Exception as e:
            logger.error(f"Failed to save keys: {e}")
            raise
    
    def set_key(self, key_name: str, key_value: str, encrypt: bool = True) -> None:
        """
        Store a key securely
        
        Args:
            key_name: Name/identifier for the key
            key_value: The actual key value
            encrypt: Whether to encrypt the key (default True)
        """
        if encrypt:
            self.keys[key_name] = key_value
            self._save_keys()
        else:
            # For non-encrypted storage (not recommended for production)
            self.keys[key_name] = key_value
        
        logger.info(f"Stored key: {key_name}")
    
    def get_key(self, key_name: str) -> Optional[str]:
        """
        Retrieve a key
        
        Args:
            key_name: Name/identifier for the key
            
        Returns:
            The key value or None if not found
        """
        return self.keys.get(key_name)
    
    def delete_key(self, key_name: str) -> bool:
        """
        Delete a key
        
        Args:
            key_name: Name/identifier for the key
            
        Returns:
            True if deleted, False if not found
        """
        if key_name in self.keys:
            del self.keys[key_name]
            self._save_keys()
            logger.info(f"Deleted key: {key_name}")
            return True
        return False
    
    def get_llm_api_key(self, provider: str = "openai") -> str:
        """
        Get LLM API key for specified provider
        
        Args:
            provider: LLM provider (openai, anthropic)
            
        Returns:
            API key for the provider
        """
        key_name = f"{provider}_api_key"
        api_key = self.get_key(key_name)
        
        if not api_key:
            # Try environment variable as fallback
            env_var = f"{provider.upper()}_API_KEY"
            api_key = os.getenv(env_var)
            
            if not api_key:
                raise ValueError(f"{provider} API key not found in key manager or environment")
        
        return api_key
    
    def get_blockchain_private_key(self, chain: str = "ethereum") -> str:
        """
        Get blockchain private key for specified chain
        
        Args:
            chain: Blockchain network (ethereum, solana)
            
        Returns:
            Private key for the blockchain
        """
        key_name = f"{chain}_private_key"
        private_key = self.get_key(key_name)
        
        if not private_key:
            # Try environment variable as fallback
            env_var = f"{chain.upper()}_PRIVATE_KEY"
            private_key = os.getenv(env_var)
            
            if not private_key:
                raise ValueError(f"{chain} private key not found in key manager or environment")
        
        return private_key
    
    def get_rpc_url(self, chain: str = "ethereum") -> str:
        """
        Get RPC URL for specified blockchain
        
        Args:
            chain: Blockchain network (ethereum, solana)
            
        Returns:
            RPC URL for the blockchain
        """
        key_name = f"{chain}_rpc_url"
        rpc_url = self.get_key(key_name)
        
        if not rpc_url:
            # Try environment variable as fallback
            env_var = f"{chain.upper()}_RPC_URL"
            rpc_url = os.getenv(env_var)
            
            if not rpc_url:
                raise ValueError(f"{chain} RPC URL not found in key manager or environment")
        
        return rpc_url
    
    def initialize_from_environment(self) -> None:
        """
        Initialize key manager with keys from environment variables
        Useful for initial setup
        """
        env_mappings = {
            "openai_api_key": "OPENAI_API_KEY",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
            "ethereum_private_key": "ETHEREUM_PRIVATE_KEY",
            "ethereum_rpc_url": "ETHEREUM_RPC_URL",
            "solana_private_key": "SOLANA_PRIVATE_KEY",
            "solana_rpc_url": "SOLANA_RPC_URL",
            "github_token": "GITHUB_TOKEN",
        }
        
        for key_name, env_var in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value and env_value != "" and not env_value.startswith("your_"):
                self.set_key(key_name, env_value)
                logger.info(f"Initialized key from environment: {key_name}")
    
    def validate_required_keys(self) -> Dict[str, bool]:
        """
        Validate that all required keys are present
        
        Returns:
            Dictionary mapping key names to availability status
        """
        required_keys = [
            "openai_api_key",
            "ethereum_private_key",
            "ethereum_rpc_url"
        ]
        
        validation_results = {}
        for key_name in required_keys:
            validation_results[key_name] = self.get_key(key_name) is not None
        
        return validation_results


def create_production_key_manager() -> KeyManager:
    """
    Create a key manager for production use
    Requires KEY_MANAGER_PASSWORD environment variable to be set
    """
    master_password = os.getenv("KEY_MANAGER_PASSWORD")
    if not master_password:
        raise ValueError(
            "KEY_MANAGER_PASSWORD environment variable must be set for production key management"
        )
    
    key_manager = KeyManager(master_password)
    
    # Initialize from environment if keys are available
    key_manager.initialize_from_environment()
    
    # Validate required keys
    validation = key_manager.validate_required_keys()
    missing_keys = [k for k, v in validation.items() if not v]
    
    if missing_keys:
        logger.warning(f"Missing required keys: {missing_keys}")
    
    return key_manager