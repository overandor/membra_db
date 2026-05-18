"""
Semantic Value Transfer Protocol (SVTP)
Universal syntax for semantic value transfer across SMS, email, links, domains, and endpoints
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import os
import re
import json
import hashlib
import time
from datetime import datetime, timedelta

class TransferChannel(Enum):
    """Supported transfer channels"""
    SMS = "sms"
    EMAIL = "email"
    LINK = "link"
    DOMAIN = "domain"
    ENDPOINT = "endpoint"

class SemanticType(Enum):
    """Types of semantic value"""
    PAYMENT = "payment"
    REQUEST = "request"
    INVOICE = "invoice"
    DONATION = "donation"
    SUBSCRIPTION = "subscription"
    REWARD = "reward"
    REFUND = "refund"
    ESCROW = "escrow"
    MULTI_SIG = "multi_sig"
    TIME_LOCKED = "time_locked"
    CONDITIONAL = "conditional"

@dataclass
class SemanticValue:
    """Core semantic value structure"""
    amount: float
    currency: str
    semantic_type: SemanticType
    sender: str
    recipient: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    conditions: List[str] = field(default_factory=list)
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount": self.amount,
            "currency": self.currency,
            "semantic_type": self.semantic_type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "metadata": self.metadata,
            "conditions": self.conditions,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticValue':
        return cls(
            amount=data["amount"],
            currency=data["currency"],
            semantic_type=SemanticType(data["semantic_type"]),
            sender=data["sender"],
            recipient=data["recipient"],
            metadata=data.get("metadata", {}),
            conditions=data.get("conditions", []),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            created_at=datetime.fromisoformat(data["created_at"])
        )

@dataclass
class TransferPayload:
    """Complete transfer payload for any channel"""
    semantic_value: SemanticValue
    channel: TransferChannel
    channel_address: str  # phone number, email, URL, domain, endpoint
    signature: str = ""
    nonce: str = ""
    network_id: str = "membra-mainnet"
    gas_limit: int = 21000
    gas_price: float = 0.00001
    
    def generate_signature(self, private_key: str) -> str:
        """Generate signature for the transfer"""
        payload_str = self.to_signing_string()
        signature_input = f"{private_key}{payload_str}"
        return hashlib.sha256(signature_input.encode()).hexdigest()
    
    def to_signing_string(self) -> str:
        """Convert to string for signing"""
        return f"{self.semantic_value.amount}{self.semantic_value.currency}{self.semantic_value.sender}{self.semantic_value.recipient}{self.nonce}{self.network_id}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "semantic_value": self.semantic_value.to_dict(),
            "channel": self.channel.value,
            "channel_address": self.channel_address,
            "signature": self.signature,
            "nonce": self.nonce,
            "network_id": self.network_id,
            "gas_limit": self.gas_limit,
            "gas_price": self.gas_price
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransferPayload':
        return cls(
            semantic_value=SemanticValue.from_dict(data["semantic_value"]),
            channel=TransferChannel(data["channel"]),
            channel_address=data["channel_address"],
            signature=data.get("signature", ""),
            nonce=data.get("nonce", ""),
            network_id=data.get("network_id", "membra-mainnet"),
            gas_limit=data.get("gas_limit", 21000),
            gas_price=data.get("gas_price", 0.00001)
        )

class SemanticTransferSyntax:
    """Parser and generator for semantic value transfer syntax"""
    
    # SMS Syntax: @pay:100.USD:to:+1234567890:for:services:ref:INV-001
    SMS_PATTERN = r'@(\w+):([\d.]+)\.(\w+):to:([^\s:]+)(?::for:([^\s:]+))?(?::ref:([^\s:]+))?(?::exp:(\d+))?'
    
    # Email Syntax: pay://100.USD/to/+1234567890@domain.com/for/services/ref/INV-001
    EMAIL_PATTERN = r'(\w+)://([\d.]+)\.(\w+)/to/([^\s/]+)(?:@([^\s/]+))?(?:/for/([^\s/]+))?(?:/ref/([^\s/]+))?(?:/exp/(\d+))?'
    
    # Link Syntax: https://pay.membra.io/100/USD/to/+1234567890/for/services/ref/INV-001
    LINK_PATTERN = r'https?://([^.]+)\.membra\.io/([\d.]+)/(\w+)/to/([^\s/]+)(?:/for/([^\s/]+))?(?:/ref/([^\s/]+))?(?:/exp/(\d+))?'
    
    # Domain Syntax: 100.USD.pay.membra.io:+1234567890:services:INV-001
    DOMAIN_PATTERN = r'([\d.]+)\.(\w+)\.([^.]+)\.membra\.io:([^\s:]+)(?::([^\s:]+))?(?::([^\s:]+))?'
    
    # Endpoint Syntax: POST /api/v1/transfer {"amount":100,"currency":"USD","to":"+1234567890","type":"payment","ref":"INV-001"}
    
    @classmethod
    def parse_sms(cls, sms_text: str) -> Optional[TransferPayload]:
        """Parse SMS semantic transfer syntax"""
        match = re.match(cls.SMS_PATTERN, sms_text)
        if not match:
            return None
        
        action, amount, currency, recipient, purpose, reference, expiry = match.groups()
        
        semantic_value = SemanticValue(
            amount=float(amount),
            currency=currency,
            semantic_type=cls._action_to_type(action),
            sender="unknown",  # Will be filled from context
            recipient=recipient,
            metadata={
                "purpose": purpose or "",
                "reference": reference or ""
            }
        )
        
        if expiry:
            semantic_value.expires_at = datetime.utcnow() + timedelta(seconds=int(expiry))
        
        return TransferPayload(
            semantic_value=semantic_value,
            channel=TransferChannel.SMS,
            channel_address=recipient,
            nonce=cls._generate_nonce()
        )
    
    @classmethod
    def parse_email(cls, email_text: str) -> Optional[TransferPayload]:
        """Parse email semantic transfer syntax"""
        match = re.match(cls.EMAIL_PATTERN, email_text)
        if not match:
            return None
        
        action, amount, currency, recipient, domain, purpose, reference, expiry = match.groups()
        
        semantic_value = SemanticValue(
            amount=float(amount),
            currency=currency,
            semantic_type=cls._action_to_type(action),
            sender="unknown",
            recipient=recipient,
            metadata={
                "domain": domain or "",
                "purpose": purpose or "",
                "reference": reference or ""
            }
        )
        
        if expiry:
            semantic_value.expires_at = datetime.utcnow() + timedelta(seconds=int(expiry))
        
        channel_address = f"{recipient}@{domain}" if domain else recipient
        
        return TransferPayload(
            semantic_value=semantic_value,
            channel=TransferChannel.EMAIL,
            channel_address=channel_address,
            nonce=cls._generate_nonce()
        )
    
    @classmethod
    def parse_link(cls, link_url: str) -> Optional[TransferPayload]:
        """Parse link semantic transfer syntax"""
        match = re.match(cls.LINK_PATTERN, link_url)
        if not match:
            return None
        
        subdomain, amount, currency, recipient, purpose, reference, expiry = match.groups()
        
        semantic_value = SemanticValue(
            amount=float(amount),
            currency=currency,
            semantic_type=SemanticType.PAYMENT,  # Links default to payment
            sender="unknown",
            recipient=recipient,
            metadata={
                "subdomain": subdomain,
                "purpose": purpose or "",
                "reference": reference or ""
            }
        )
        
        if expiry:
            semantic_value.expires_at = datetime.utcnow() + timedelta(seconds=int(expiry))
        
        return TransferPayload(
            semantic_value=semantic_value,
            channel=TransferChannel.LINK,
            channel_address=link_url,
            nonce=cls._generate_nonce()
        )
    
    @classmethod
    def parse_domain(cls, domain_text: str) -> Optional[TransferPayload]:
        """Parse domain semantic transfer syntax"""
        match = re.match(cls.DOMAIN_PATTERN, domain_text)
        if not match:
            return None
        
        amount, currency, action, recipient, purpose, reference = match.groups()
        
        semantic_value = SemanticValue(
            amount=float(amount),
            currency=currency,
            semantic_type=cls._action_to_type(action),
            sender="unknown",
            recipient=recipient,
            metadata={
                "purpose": purpose or "",
                "reference": reference or ""
            }
        )
        
        return TransferPayload(
            semantic_value=semantic_value,
            channel=TransferChannel.DOMAIN,
            channel_address=domain_text,
            nonce=cls._generate_nonce()
        )
    
    @classmethod
    def parse_endpoint(cls, endpoint_data: Union[str, Dict]) -> Optional[TransferPayload]:
        """Parse endpoint semantic transfer syntax"""
        if isinstance(endpoint_data, str):
            try:
                endpoint_data = json.loads(endpoint_data)
            except json.JSONDecodeError:
                return None
        
        if not isinstance(endpoint_data, dict):
            return None
        
        semantic_value = SemanticValue(
            amount=float(endpoint_data.get("amount", 0)),
            currency=endpoint_data.get("currency", "USD"),
            semantic_type=SemanticType(endpoint_data.get("type", "payment")),
            sender=endpoint_data.get("from", "unknown"),
            recipient=endpoint_data.get("to", "unknown"),
            metadata={
                k: v for k, v in endpoint_data.items() 
                if k not in ["amount", "currency", "type", "from", "to"]
            }
        )
        
        return TransferPayload(
            semantic_value=semantic_value,
            channel=TransferChannel.ENDPOINT,
            channel_address=endpoint_data.get("endpoint", "/api/v1/transfer"),
            nonce=cls._generate_nonce()
        )
    
    @classmethod
    def generate_sms(cls, payload: TransferPayload) -> str:
        """Generate SMS semantic transfer syntax"""
        action = cls._type_to_action(payload.semantic_value.semantic_type)
        purpose = payload.semantic_value.metadata.get("purpose", "")
        reference = payload.semantic_value.metadata.get("reference", "")
        expiry = ""
        
        if payload.semantic_value.expires_at:
            expiry_sec = int((payload.semantic_value.expires_at - datetime.utcnow()).total_seconds())
            expiry = f":exp:{expiry_sec}"
        
        parts = [f"@{action}", f"{payload.semantic_value.amount}.{payload.semantic_value.currency}", 
                f"to:{payload.channel_address}"]
        
        if purpose:
            parts.append(f"for:{purpose}")
        if reference:
            parts.append(f"ref:{reference}")
        if expiry:
            parts.append(expiry)
        
        return ":".join(parts)
    
    @classmethod
    def generate_email(cls, payload: TransferPayload) -> str:
        """Generate email semantic transfer syntax"""
        action = cls._type_to_action(payload.semantic_value.semantic_type)
        purpose = payload.semantic_value.metadata.get("purpose", "")
        reference = payload.semantic_value.metadata.get("reference", "")
        domain = payload.semantic_value.metadata.get("domain", "membra.io")
        expiry = ""
        
        if payload.semantic_value.expires_at:
            expiry_sec = int((payload.semantic_value.expires_at - datetime.utcnow()).total_seconds())
            expiry = f"/exp/{expiry_sec}"
        
        parts = [f"{action}://", f"{payload.semantic_value.amount}.{payload.semantic_value.currency}"]

        # Extract recipient from channel_address if it contains domain
        recipient = payload.channel_address
        if "@" in recipient:
            recipient = recipient.split("@")[0]
            domain_from_address = recipient.split("@")[1] if "@" in recipient else domain
            if domain_from_address:
                domain = domain_from_address

        parts.append(f"/to/{recipient}")
        parts.append(f"@{domain}")

        if purpose:
            parts.append(f"/for/{purpose}")
        if reference:
            parts.append(f"/ref/{reference}")
        if expiry:
            parts.append(expiry)

return "".join(parts)
        
        return "".join(parts)
    
    @classmethod
    def generate_link(cls, payload: TransferPayload) -> str:
        """Generate link semantic transfer syntax"""
        subdomain = payload.semantic_value.metadata.get("subdomain", "pay")
        purpose = payload.semantic_value.metadata.get("purpose", "")
        reference = payload.semantic_value.metadata.get("reference", "")
        expiry = ""
        
        if payload.semantic_value.expires_at:
            expiry_sec = int((payload.semantic_value.expires_at - datetime.utcnow()).total_seconds())
            expiry = f"/exp/{expiry_sec}"
        
        parts = [f"https://{subdomain}.membra.io/", f"{payload.semantic_value.amount}",
                payload.semantic_value.currency, "to", payload.channel_address]
        
        if purpose:
            parts.extend(["for", purpose])
        if reference:
            parts.extend(["ref", reference])
        if expiry:
            parts.append(expiry)
        
        return "/".join(parts)
    
    @classmethod
    def generate_domain(cls, payload: TransferPayload) -> str:
        """Generate domain semantic transfer syntax"""
        action = cls._type_to_action(payload.semantic_value.semantic_type)
        purpose = payload.semantic_value.metadata.get("purpose", "")
        reference = payload.semantic_value.metadata.get("reference", "")
        
        parts = [f"{payload.semantic_value.amount}.{payload.semantic_value.currency}.{action}.membra.io",
                payload.channel_address]
        
        if purpose:
            parts.append(purpose)
        if reference:
            parts.append(reference)
        
        return ":".join(parts)
    
    @classmethod
    def generate_endpoint(cls, payload: TransferPayload) -> Dict[str, Any]:
        """Generate endpoint semantic transfer syntax"""
        endpoint_data = {
            "amount": payload.semantic_value.amount,
            "currency": payload.semantic_value.currency,
            "type": payload.semantic_value.semantic_type.value,
            "from": payload.semantic_value.sender,
            "to": payload.channel_address,
            "endpoint": payload.channel_address,
            "nonce": payload.nonce,
            "network_id": payload.network_id
        }
        
        endpoint_data.update(payload.semantic_value.metadata)
        
        return endpoint_data
    
    @staticmethod
    def _action_to_type(action: str) -> SemanticType:
        """Convert action string to semantic type"""
        action_map = {
            "pay": SemanticType.PAYMENT,
            "request": SemanticType.REQUEST,
            "invoice": SemanticType.INVOICE,
            "donate": SemanticType.DONATION,
            "sub": SemanticType.SUBSCRIPTION,
            "reward": SemanticType.REWARD,
            "refund": SemanticType.REFUND,
            "escrow": SemanticType.ESCROW,
            "multisig": SemanticType.MULTI_SIG,
            "timelock": SemanticType.TIME_LOCKED,
            "conditional": SemanticType.CONDITIONAL
        }
        return action_map.get(action.lower(), SemanticType.PAYMENT)
    
    @staticmethod
    def _type_to_action(semantic_type: SemanticType) -> str:
        """Convert semantic type to action string"""
        type_map = {
            SemanticType.PAYMENT: "pay",
            SemanticType.REQUEST: "request",
            SemanticType.INVOICE: "invoice",
            SemanticType.DONATION: "donate",
            SemanticType.SUBSCRIPTION: "sub",
            SemanticType.REWARD: "reward",
            SemanticType.REFUND: "refund",
            SemanticType.ESCROW: "escrow",
            SemanticType.MULTI_SIG: "multisig",
            SemanticType.TIME_LOCKED: "timelock",
            SemanticType.CONDITIONAL: "conditional"
        }
        return type_map.get(semantic_type, "pay")
    
    @staticmethod
    def _generate_nonce() -> str:
        """Generate unique nonce"""
        import os
        return hashlib.sha256(f"{time.time()}{os.urandom(16).hex()}".encode()).hexdigest()[:16]