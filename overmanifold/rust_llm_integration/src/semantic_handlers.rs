//! Rust Semantic Value Transfer Handlers
//! Handles SMS, email, link, domain, and endpoint semantic transfers

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc, Duration};
use regex::Regex;
use sha2::{Sha256, Digest};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{info, error, debug};

/// Transfer channels
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TransferChannel {
    #[serde(rename = "sms")]
    Sms,
    #[serde(rename = "email")]
    Email,
    #[serde(rename = "link")]
    Link,
    #[serde(rename = "domain")]
    Domain,
    #[serde(rename = "endpoint")]
    Endpoint,
}

/// Semantic value types
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SemanticType {
    #[serde(rename = "payment")]
    Payment,
    #[serde(rename = "request")]
    Request,
    #[serde(rename = "invoice")]
    Invoice,
    #[serde(rename = "donation")]
    Donation,
    #[serde(rename = "subscription")]
    Subscription,
    #[serde(rename = "reward")]
    Reward,
    #[serde(rename = "refund")]
    Refund,
    #[serde(rename = "escrow")]
    Escrow,
    #[serde(rename = "multi_sig")]
    MultiSig,
    #[serde(rename = "time_locked")]
    TimeLocked,
    #[serde(rename = "conditional")]
    Conditional,
}

/// Semantic value structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SemanticValue {
    pub amount: f64,
    pub currency: String,
    pub semantic_type: SemanticType,
    pub sender: String,
    pub recipient: String,
    pub metadata: HashMap<String, String>,
    pub conditions: Vec<String>,
    pub expires_at: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
}

impl SemanticValue {
    pub fn new(
        amount: f64,
        currency: String,
        semantic_type: SemanticType,
        sender: String,
        recipient: String,
    ) -> Self {
        Self {
            amount,
            currency,
            semantic_type,
            sender,
            recipient,
            metadata: HashMap::new(),
            conditions: Vec::new(),
            expires_at: None,
            created_at: Utc::now(),
        }
    }
}

/// Transfer payload
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransferPayload {
    pub semantic_value: SemanticValue,
    pub channel: TransferChannel,
    pub channel_address: String,
    pub signature: String,
    pub nonce: String,
    pub network_id: String,
    pub gas_limit: u64,
    pub gas_price: f64,
}

impl TransferPayload {
    pub fn new(semantic_value: SemanticValue, channel: TransferChannel, channel_address: String) -> Self {
        Self {
            semantic_value,
            channel,
            channel_address,
            signature: String::new(),
            nonce: Self::generate_nonce(),
            network_id: "membra-mainnet".to_string(),
            gas_limit: 21000,
            gas_price: 0.00001,
        }
    }
    
    fn generate_nonce() -> String {
        let mut hasher = Sha256::new();
        let timestamp = Utc::now().timestamp();
        let random: u64 = rand::random();
        hasher.update(format!("{}{}", timestamp, random).as_bytes());
        format!("{:x}", hasher.finalize())[..16].to_string()
    }
}

/// SMS Handler
pub struct SmsHandler {
    sms_pattern: Regex,
}

impl SmsHandler {
    pub fn new() -> Self {
        // @pay:100.USD:to:+1234567890:for:services:ref:INV-001
        let sms_pattern = Regex::new(r"@(\w+):([\d.]+)\.(\w+):to:([^\s:]+)(?::for:([^\s:]+))?(?::ref:([^\s:]+))?(?::exp:(\d+))?").unwrap();
        Self { sms_pattern }
    }
    
    pub fn parse(&self, sms_text: &str) -> Option<TransferPayload> {
        let captures = self.sms_pattern.captures(sms_text)?;
        
        let action = captures.get(1)?.as_str()?;
        let amount: f64 = captures.get(2)?.as_str()?.parse().ok()?;
        let currency = captures.get(3)?.as_str()?.to_string();
        let recipient = captures.get(4)?.as_str()?.to_string();
        let purpose = captures.get(5).map(|m| m.as_str().to_string());
        let reference = captures.get(6).map(|m| m.as_str().to_string());
        let expiry = captures.get(7).and_then(|m| m.as_str().parse::<i64>().ok());
        
        let mut semantic_value = SemanticValue::new(
            amount,
            currency,
            self.action_to_type(action),
            "unknown".to_string(),
            recipient.clone(),
        );
        
        if let Some(purpose) = purpose {
            semantic_value.metadata.insert("purpose".to_string(), purpose);
        }
        if let Some(reference) = reference {
            semantic_value.metadata.insert("reference".to_string(), reference);
        }
        
        if let Some(expiry_sec) = expiry {
            semantic_value.expires_at = Some(Utc::now() + Duration::seconds(expiry_sec));
        }
        
        Some(TransferPayload::new(semantic_value, TransferChannel::Sms, recipient))
    }
    
    pub fn generate(&self, payload: &TransferPayload) -> String {
        let action = self.type_to_action(&payload.semantic_value.semantic_type);
        let purpose = payload.semantic_value.metadata.get("purpose").cloned().unwrap_or_default();
        let reference = payload.semantic_value.metadata.get("reference").cloned().unwrap_or_default();
        
        let mut parts = vec![
            format!("@{}", action),
            format!("{}.{}", payload.semantic_value.amount, payload.semantic_value.currency),
            format!("to:{}", payload.channel_address),
        ];
        
        if !purpose.is_empty() {
            parts.push(format!("for:{}", purpose));
        }
        if !reference.is_empty() {
            parts.push(format!("ref:{}", reference));
        }
        
        parts.join(":")
    }
    
    fn action_to_type(&self, action: &str) -> SemanticType {
        match action.to_lowercase().as_str() {
            "pay" => SemanticType::Payment,
            "request" => SemanticType::Request,
            "invoice" => SemanticType::Invoice,
            "donate" => SemanticType::Donation,
            "sub" => SemanticType::Subscription,
            "reward" => SemanticType::Reward,
            "refund" => SemanticType::Refund,
            "escrow" => SemanticType::Escrow,
            "multisig" => SemanticType::MultiSig,
            "timelock" => SemanticType::TimeLocked,
            "conditional" => SemanticType::Conditional,
            _ => SemanticType::Payment,
        }
    }
    
    fn type_to_action(&self, semantic_type: &SemanticType) -> &'static str {
        match semantic_type {
            SemanticType::Payment => "pay",
            SemanticType::Request => "request",
            SemanticType::Invoice => "invoice",
            SemanticType::Donation => "donate",
            SemanticType::Subscription => "sub",
            SemanticType::Reward => "reward",
            SemanticType::Refund => "refund",
            SemanticType::Escrow => "escrow",
            SemanticType::MultiSig => "multisig",
            SemanticType::TimeLocked => "timelock",
            SemanticType::Conditional => "conditional",
        }
    }
}

/// Email Handler
pub struct EmailHandler {
    email_pattern: Regex,
}

impl EmailHandler {
    pub fn new() -> Self {
        // pay://100.USD/to/+1234567890@domain.com/for/services/ref/INV-001
        let email_pattern = Regex::new(r"(\w+)://([\d.]+)\.(\w+)/to/([^\s/]+)(?:@([^\s/]+))?(?:/for/([^\s/]+))?(?:/ref/([^\s/]+))?(?:/exp/(\d+))?").unwrap();
        Self { email_pattern }
    }
    
    pub fn parse(&self, email_text: &str) -> Option<TransferPayload> {
        let captures = self.email_pattern.captures(email_text)?;
        
        let action = captures.get(1)?.as_str()?;
        let amount: f64 = captures.get(2)?.as_str()?.parse().ok()?;
        let currency = captures.get(3)?.as_str()?.to_string();
        let recipient = captures.get(4)?.as_str()?.to_string();
        let domain = captures.get(5).map(|m| m.as_str().to_string());
        let purpose = captures.get(6).map(|m| m.as_str().to_string());
        let reference = captures.get(7).map(|m| m.as_str().to_string());
        let expiry = captures.get(8).and_then(|m| m.as_str().parse::<i64>().ok());
        
        let mut semantic_value = SemanticValue::new(
            amount,
            currency,
            self.action_to_type(action),
            "unknown".to_string(),
            recipient.clone(),
        );
        
        if let Some(domain) = domain {
            semantic_value.metadata.insert("domain".to_string(), domain.clone());
        }
        if let Some(purpose) = purpose {
            semantic_value.metadata.insert("purpose".to_string(), purpose);
        }
        if let Some(reference) = reference {
            semantic_value.metadata.insert("reference".to_string(), reference);
        }
        
        if let Some(expiry_sec) = expiry {
            semantic_value.expires_at = Some(Utc::now() + Duration::seconds(expiry_sec));
        }
        
        let channel_address = if let Some(domain) = domain {
            format!("{}@{}", recipient, domain)
        } else {
            recipient.clone()
        };
        
        Some(TransferPayload::new(semantic_value, TransferChannel::Email, channel_address))
    }
    
    pub fn generate(&self, payload: &TransferPayload) -> String {
        let action = self.type_to_action(&payload.semantic_value.semantic_type);
        let purpose = payload.semantic_value.metadata.get("purpose").cloned().unwrap_or_default();
        let reference = payload.semantic_value.metadata.get("reference").cloned().unwrap_or_default();
        let domain = payload.semantic_value.metadata.get("domain").cloned().unwrap_or_else(|| "membra.io".to_string());
        
        let mut parts = vec![
            format!("{}://", action),
            format!("{}.{}", payload.semantic_value.amount, payload.semantic_value.currency),
            format!("/to/{}", payload.channel_address),
            format!("@{}", domain),
        ];
        
        if !purpose.is_empty() {
            parts.push(format!("/for/{}", purpose));
        }
        if !reference.is_empty() {
            parts.push(format!("/ref/{}", reference));
        }
        
        parts.join("")
    }
    
    fn action_to_type(&self, action: &str) -> SemanticType {
        // Same as SMS handler
        match action.to_lowercase().as_str() {
            "pay" => SemanticType::Payment,
            "request" => SemanticType::Request,
            "invoice" => SemanticType::Invoice,
            "donate" => SemanticType::Donation,
            "sub" => SemanticType::Subscription,
            "reward" => SemanticType::Reward,
            "refund" => SemanticType::Refund,
            "escrow" => SemanticType::Escrow,
            "multisig" => SemanticType::MultiSig,
            "timelock" => SemanticType::TimeLocked,
            "conditional" => SemanticType::Conditional,
            _ => SemanticType::Payment,
        }
    }
    
    fn type_to_action(&self, semantic_type: &SemanticType) -> &'static str {
        // Same as SMS handler
        match semantic_type {
            SemanticType::Payment => "pay",
            SemanticType::Request => "request",
            SemanticType::Invoice => "invoice",
            SemanticType::Donation => "donate",
            SemanticType::Subscription => "sub",
            SemanticType::Reward => "reward",
            SemanticType::Refund => "refund",
            SemanticType::Escrow => "escrow",
            SemanticType::MultiSig => "multisig",
            SemanticType::TimeLocked => "timelock",
            SemanticType::Conditional => "conditional",
        }
    }
}

/// Link Handler
pub struct LinkHandler {
    link_pattern: Regex,
}

impl LinkHandler {
    pub fn new() -> Self {
        // https://pay.membra.io/100/USD/to/+1234567890/for/services/ref/INV-001
        let link_pattern = Regex::new(r"https?://([^.]+)\.membra\.io/([\d.]+)/(\w+)/to/([^\s/]+)(?:/for/([^\s/]+))?(?:/ref/([^\s/]+))?(?:/exp/(\d+))?").unwrap();
        Self { link_pattern }
    }
    
    pub fn parse(&self, link_url: &str) -> Option<TransferPayload> {
        let captures = self.link_pattern.captures(link_url)?;
        
        let subdomain = captures.get(1)?.as_str()?.to_string();
        let amount: f64 = captures.get(2)?.as_str()?.parse().ok()?;
        let currency = captures.get(3)?.as_str()?.to_string();
        let recipient = captures.get(4)?.as_str()?.to_string();
        let purpose = captures.get(5).map(|m| m.as_str().to_string());
        let reference = captures.get(6).map(|m| m.as_str().to_string());
        let expiry = captures.get(7).and_then(|m| m.as_str().parse::<i64>().ok());
        
        let mut semantic_value = SemanticValue::new(
            amount,
            currency,
            SemanticType::Payment, // Links default to payment
            "unknown".to_string(),
            recipient.clone(),
        );
        
        semantic_value.metadata.insert("subdomain".to_string(), subdomain);
        
        if let Some(purpose) = purpose {
            semantic_value.metadata.insert("purpose".to_string(), purpose);
        }
        if let Some(reference) = reference {
            semantic_value.metadata.insert("reference".to_string(), reference);
        }
        
        if let Some(expiry_sec) = expiry {
            semantic_value.expires_at = Some(Utc::now() + Duration::seconds(expiry_sec));
        }
        
        Some(TransferPayload::new(semantic_value, TransferChannel::Link, link_url.to_string()))
    }
    
    pub fn generate(&self, payload: &TransferPayload) -> String {
        let subdomain = payload.semantic_value.metadata.get("subdomain").cloned().unwrap_or_else(|| "pay".to_string());
        let purpose = payload.semantic_value.metadata.get("purpose").cloned().unwrap_or_default();
        let reference = payload.semantic_value.metadata.get("reference").cloned().unwrap_or_default();
        
        let mut parts = vec![
            format!("https://{}.membra.io/", subdomain),
            payload.semantic_value.amount.to_string(),
            payload.semantic_value.currency.clone(),
            "to".to_string(),
            payload.channel_address.clone(),
        ];
        
        if !purpose.is_empty() {
            parts.push("for".to_string());
            parts.push(purpose);
        }
        if !reference.is_empty() {
            parts.push("ref".to_string());
            parts.push(reference);
        }
        
        parts.join("/")
    }
}

/// Domain Handler
pub struct DomainHandler {
    domain_pattern: Regex,
}

impl DomainHandler {
    pub fn new() -> Self {
        // 100.USD.pay.membra.io:+1234567890:services:INV-001
        let domain_pattern = Regex::new(r"([\d.]+)\.(\w+)\.([^.]+)\.membra\.io:([^\s:]+)(?::([^\s:]+))?(?::([^\s:]+))?").unwrap();
        Self { domain_pattern }
    }
    
    pub fn parse(&self, domain_text: &str) -> Option<TransferPayload> {
        let captures = self.domain_pattern.captures(domain_text)?;
        
        let amount: f64 = captures.get(1)?.as_str()?.parse().ok()?;
        let currency = captures.get(2)?.as_str()?.to_string();
        let action = captures.get(3)?.as_str()?;
        let recipient = captures.get(4)?.as_str()?.to_string();
        let purpose = captures.get(5).map(|m| m.as_str().to_string());
        let reference = captures.get(6).map(|m| m.as_str().to_string());
        
        let mut semantic_value = SemanticValue::new(
            amount,
            currency,
            self.action_to_type(action),
            "unknown".to_string(),
            recipient.clone(),
        );
        
        if let Some(purpose) = purpose {
            semantic_value.metadata.insert("purpose".to_string(), purpose);
        }
        if let Some(reference) = reference {
            semantic_value.metadata.insert("reference".to_string(), reference);
        }
        
        Some(TransferPayload::new(semantic_value, TransferChannel::Domain, domain_text.to_string()))
    }
    
    pub fn generate(&self, payload: &TransferPayload) -> String {
        let action = self.type_to_action(&payload.semantic_value.semantic_type);
        let purpose = payload.semantic_value.metadata.get("purpose").cloned().unwrap_or_default();
        let reference = payload.semantic_value.metadata.get("reference").cloned().unwrap_or_default();
        
        let mut parts = vec![
            format!("{}.{}.{}.membra.io", 
                    payload.semantic_value.amount, 
                    payload.semantic_value.currency, 
                    action),
            payload.channel_address.clone(),
        ];
        
        if !purpose.is_empty() {
            parts.push(purpose);
        }
        if !reference.is_empty() {
            parts.push(reference);
        }
        
        parts.join(":")
    }
    
    fn action_to_type(&self, action: &str) -> SemanticType {
        match action.to_lowercase().as_str() {
            "pay" => SemanticType::Payment,
            "request" => SemanticType::Request,
            "invoice" => SemanticType::Invoice,
            "donate" => SemanticType::Donation,
            "sub" => SemanticType::Subscription,
            "reward" => SemanticType::Reward,
            "refund" => SemanticType::Refund,
            "escrow" => SemanticType::Escrow,
            "multisig" => SemanticType::MultiSig,
            "timelock" => SemanticType::TimeLocked,
            "conditional" => SemanticType::Conditional,
            _ => SemanticType::Payment,
        }
    }
    
    fn type_to_action(&self, semantic_type: &SemanticType) -> &'static str {
        match semantic_type {
            SemanticType::Payment => "pay",
            SemanticType::Request => "request",
            SemanticType::Invoice => "invoice",
            SemanticType::Donation => "donate",
            SemanticType::Subscription => "sub",
            SemanticType::Reward => "reward",
            SemanticType::Refund => "refund",
            SemanticType::Escrow => "escrow",
            SemanticType::MultiSig => "multisig",
            SemanticType::TimeLocked => "timelock",
            SemanticType::Conditional => "conditional",
        }
    }
}

/// Endpoint Handler
pub struct EndpointHandler;

impl EndpointHandler {
    pub fn new() -> Self {
        Self
    }
    
    pub fn parse(&self, endpoint_data: &str) -> Option<TransferPayload> {
        // Try to parse as JSON
        let data: serde_json::Value = serde_json::from_str(endpoint_data).ok()?;
        
        let amount = data.get("amount").and_then(|v| v.as_f64())?;
        let currency = data.get("currency").and_then(|v| v.as_str())?.to_string();
        let semantic_type_str = data.get("type").and_then(|v| v.as_str()).unwrap_or("payment");
        let sender = data.get("from").and_then(|v| v.as_str()).unwrap_or("unknown").to_string();
        let recipient = data.get("to").and_then(|v| v.as_str()).unwrap_or("unknown").to_string();
        let endpoint = data.get("endpoint").and_then(|v| v.as_str()).unwrap_or("/api/v1/transfer").to_string();
        
        let mut semantic_value = SemanticValue::new(
            amount,
            currency,
            self.string_to_type(semantic_type_str),
            sender,
            recipient.clone(),
        );
        
        // Add metadata from other fields
        if let Some(obj) = data.as_object() {
            for (key, value) in obj {
                if !["amount", "currency", "type", "from", "to", "endpoint"].contains(&key.as_str()) {
                    if let Some(str_val) = value.as_str() {
                        semantic_value.metadata.insert(key.clone(), str_val.to_string());
                    }
                }
            }
        }
        
        Some(TransferPayload::new(semantic_value, TransferChannel::Endpoint, endpoint))
    }
    
    pub fn generate(&self, payload: &TransferPayload) -> String {
        let mut endpoint_data = serde_json::json!({
            "amount": payload.semantic_value.amount,
            "currency": payload.semantic_value.currency,
            "type": self.type_to_string(&payload.semantic_value.semantic_type),
            "from": payload.semantic_value.sender,
            "to": payload.channel_address,
            "endpoint": payload.channel_address,
            "nonce": payload.nonce,
            "network_id": payload.network_id
        });
        
        // Add metadata
        if let Some(obj) = endpoint_data.as_object_mut() {
            for (key, value) in &payload.semantic_value.metadata {
                obj.insert(key.clone(), serde_json::Value::String(value.clone()));
            }
        }
        
        endpoint_data.to_string()
    }
    
    fn string_to_type(&self, type_str: &str) -> SemanticType {
        match type_str.to_lowercase().as_str() {
            "payment" => SemanticType::Payment,
            "request" => SemanticType::Request,
            "invoice" => SemanticType::Invoice,
            "donation" => SemanticType::Donation,
            "subscription" => SemanticType::Subscription,
            "reward" => SemanticType::Reward,
            "refund" => SemanticType::Refund,
            "escrow" => SemanticType::Escrow,
            "multi_sig" => SemanticType::MultiSig,
            "time_locked" => SemanticType::TimeLocked,
            "conditional" => SemanticType::Conditional,
            _ => SemanticType::Payment,
        }
    }
    
    fn type_to_string(&self, semantic_type: &SemanticType) -> &'static str {
        match semantic_type {
            SemanticType::Payment => "payment",
            SemanticType::Request => "request",
            SemanticType::Invoice => "invoice",
            SemanticType::Donation => "donation",
            SemanticType::Subscription => "subscription",
            SemanticType::Reward => "reward",
            SemanticType::Refund => "refund",
            SemanticType::Escrow => "escrow",
            SemanticType::MultiSig => "multi_sig",
            SemanticType::TimeLocked => "time_locked",
            SemanticType::Conditional => "conditional",
        }
    }
}

/// Unified semantic transfer handler
pub struct SemanticTransferHandler {
    sms_handler: SmsHandler,
    email_handler: EmailHandler,
    link_handler: LinkHandler,
    domain_handler: DomainHandler,
    endpoint_handler: EndpointHandler,
}

impl SemanticTransferHandler {
    pub fn new() -> Self {
        Self {
            sms_handler: SmsHandler::new(),
            email_handler: EmailHandler::new(),
            link_handler: LinkHandler::new(),
            domain_handler: DomainHandler::new(),
            endpoint_handler: EndpointHandler::new(),
        }
    }
    
    pub fn parse(&self, input: &str, channel: TransferChannel) -> Option<TransferPayload> {
        match channel {
            TransferChannel::Sms => self.sms_handler.parse(input),
            TransferChannel::Email => self.email_handler.parse(input),
            TransferChannel::Link => self.link_handler.parse(input),
            TransferChannel::Domain => self.domain_handler.parse(input),
            TransferChannel::Endpoint => self.endpoint_handler.parse(input),
        }
    }
    
    pub fn generate(&self, payload: &TransferPayload) -> String {
        match payload.channel {
            TransferChannel::Sms => self.sms_handler.generate(payload),
            TransferChannel::Email => self.email_handler.generate(payload),
            TransferChannel::Link => self.link_handler.generate(payload),
            TransferChannel::Domain => self.domain_handler.generate(payload),
            TransferChannel::Endpoint => self.endpoint_handler.generate(payload),
        }
    }
    
    pub fn auto_detect_channel(&self, input: &str) -> Option<TransferChannel> {
        if input.starts_with('@') && input.contains(':') {
            Some(TransferChannel::Sms)
        } else if input.starts_with("http://") || input.starts_with("https://") {
            if input.contains("membra.io") {
                Some(TransferChannel::Link)
            } else {
                Some(TransferChannel::Endpoint)
            }
        } else if input.contains("://") {
            Some(TransferChannel::Email)
        } else if input.contains(".membra.io:") {
            Some(TransferChannel::Domain)
        } else if input.starts_with('{') {
            Some(TransferChannel::Endpoint)
        } else {
            None
        }
    }
}

impl Default for SemanticTransferHandler {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_sms_parsing() {
        let handler = SemanticTransferHandler::new();
        let sms = "@pay:100.USD:to:+1234567890:for:services:ref:INV-001";
        
        let payload = handler.parse(sms, TransferChannel::Sms).unwrap();
        assert_eq!(payload.semantic_value.amount, 100.0);
        assert_eq!(payload.semantic_value.currency, "USD");
        assert_eq!(payload.channel, TransferChannel::Sms);
    }
    
    #[test]
    fn test_sms_generation() {
        let handler = SemanticTransferHandler::new();
        
        let mut semantic_value = SemanticValue::new(100.0, "USD".to_string(), SemanticType::Payment, "sender".to_string(), "+1234567890".to_string());
        semantic_value.metadata.insert("purpose".to_string(), "services".to_string());
        semantic_value.metadata.insert("reference".to_string(), "INV-001".to_string());
        
        let payload = TransferPayload::new(semantic_value, TransferChannel::Sms, "+1234567890".to_string());
        let generated = handler.generate(&payload);
        
        assert!(generated.contains("@pay:100.USD"));
        assert!(generated.contains("to:+1234567890"));
    }
    
    #[test]
    fn test_auto_detection() {
        let handler = SemanticTransferHandler::new();
        
        assert_eq!(handler.auto_detect_channel("@pay:100.USD:to:+1234567890"), Some(TransferChannel::Sms));
        assert_eq!(handler.auto_detect_channel("https://pay.membra.io/100/USD/to/+1234567890"), Some(TransferChannel::Link));
        assert_eq!(handler.auto_detect_channel("pay://100.USD/to/+1234567890@membra.io"), Some(TransferChannel::Email));
    }
}