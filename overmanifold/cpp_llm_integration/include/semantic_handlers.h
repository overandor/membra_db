//! C++ Semantic Value Transfer Handlers
//! Handles SMS, email, link, domain, and endpoint semantic transfers

#ifndef SEMANTIC_HANDLERS_H
#define SEMANTIC_HANDLERS_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <regex>
#include <chrono>
#include <optional>
#include <sstream>
#include <iomanip>
#include <nlohmann/json.hpp>

namespace semantic_transfer {

// Transfer channels
enum class TransferChannel {
    SMS,
    EMAIL,
    LINK,
    DOMAIN,
    ENDPOINT
};

// Semantic value types
enum class SemanticType {
    PAYMENT,
    REQUEST,
    INVOICE,
    DONATION,
    SUBSCRIPTION,
    REWARD,
    REFUND,
    ESCROW,
    MULTI_SIG,
    TIME_LOCKED,
    CONDITIONAL
};

// Semantic value structure
struct SemanticValue {
    double amount;
    std::string currency;
    SemanticType semantic_type;
    std::string sender;
    std::string recipient;
    std::map<std::string, std::string> metadata;
    std::vector<std::string> conditions;
    std::optional<std::chrono::system_clock::time_point> expires_at;
    std::chrono::system_clock::time_point created_at;
    
    SemanticValue(double amt, const std::string& curr, SemanticType type,
                 const std::string& snd, const std::string& rcpt)
        : amount(amt), currency(curr), semantic_type(type), sender(snd), recipient(rcpt),
          created_at(std::chrono::system_clock::now()) {}
};

// Transfer payload
struct TransferPayload {
    SemanticValue semantic_value;
    TransferChannel channel;
    std::string channel_address;
    std::string signature;
    std::string nonce;
    std::string network_id;
    uint64_t gas_limit;
    double gas_price;
    
    TransferPayload(const SemanticValue& value, TransferChannel ch, const std::string& addr)
        : semantic_value(value), channel(ch), channel_address(addr),
          nonce(generate_nonce()), network_id("membra-mainnet"),
          gas_limit(21000), gas_price(0.00001) {}
    
private:
    static std::string generate_nonce();
};

// SMS Handler
class SmsHandler {
public:
    SmsHandler();
    
    std::optional<TransferPayload> parse(const std::string& sms_text) const;
    std::string generate(const TransferPayload& payload) const;
    
private:
    std::regex sms_pattern_;
    
    SemanticType actionToType(const std::string& action) const;
    const char* typeToAction(SemanticType type) const;
};

// Email Handler
class EmailHandler {
public:
    EmailHandler();
    
    std::optional<TransferPayload> parse(const std::string& email_text) const;
    std::string generate(const TransferPayload& payload) const;
    
private:
    std::regex email_pattern_;
    
    SemanticType actionToType(const std::string& action) const;
    const char* typeToAction(SemanticType type) const;
};

// Link Handler
class LinkHandler {
public:
    LinkHandler();
    
    std::optional<TransferPayload> parse(const std::string& link_url) const;
    std::string generate(const TransferPayload& payload) const;
    
private:
    std::regex link_pattern_;
};

// Domain Handler
class DomainHandler {
public:
    DomainHandler();
    
    std::optional<TransferPayload> parse(const std::string& domain_text) const;
    std::string generate(const TransferPayload& payload) const;
    
private:
    std::regex domain_pattern_;
    
    SemanticType actionToType(const std::string& action) const;
    const char* typeToAction(SemanticType type) const;
};

// Endpoint Handler
class EndpointHandler {
public:
    EndpointHandler();
    
    std::optional<TransferPayload> parse(const std::string& endpoint_data) const;
    std::string generate(const TransferPayload& payload) const;
    
private:
    SemanticType stringToType(const std::string& type_str) const;
    const char* typeToString(SemanticType type) const;
};

// Unified semantic transfer handler
class SemanticTransferHandler {
public:
    SemanticTransferHandler();
    
    std::optional<TransferPayload> parse(const std::string& input, TransferChannel channel) const;
    std::string generate(const TransferPayload& payload) const;
    std::optional<TransferChannel> autoDetectChannel(const std::string& input) const;
    
private:
    std::unique_ptr<SmsHandler> sms_handler_;
    std::unique_ptr<EmailHandler> email_handler_;
    std::unique_ptr<LinkHandler> link_handler_;
    std::unique_ptr<DomainHandler> domain_handler_;
    std::unique_ptr<EndpointHandler> endpoint_handler_;
};

} // namespace semantic_transfer

#endif // SEMANTIC_HANDLERS_H