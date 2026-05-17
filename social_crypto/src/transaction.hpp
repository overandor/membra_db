#pragma once

#include "crypto_utils.hpp"
#include <string>
#include <vector>
#include <cstdint>
#include <chrono>
#include <sstream>

namespace social_crypto {

struct Transaction {
    Address from;
    Address to;
    uint64_t amount;
    uint64_t nonce;
    uint64_t timestamp;
    std::vector<uint8_t> data;  // arbitrary data field
    Signature sig;

    std::vector<uint8_t> serialize_for_signing() const {
        std::vector<uint8_t> buf;
        buf.insert(buf.end(), from.begin(), from.end());
        buf.insert(buf.end(), to.begin(), to.end());
        auto* amt = reinterpret_cast<const uint8_t*>(&amount);
        buf.insert(buf.end(), amt, amt + sizeof(amount));
        auto* nc = reinterpret_cast<const uint8_t*>(&nonce);
        buf.insert(buf.end(), nc, nc + sizeof(nonce));
        auto* ts = reinterpret_cast<const uint8_t*>(&timestamp);
        buf.insert(buf.end(), ts, ts + sizeof(timestamp));
        buf.insert(buf.end(), data.begin(), data.end());
        return buf;
    }

    Hash tx_hash() const {
        return sha256(serialize_for_signing());
    }

    std::string tx_hash_hex() const {
        return hash_to_hex(tx_hash());
    }

    bool is_signed() const { return !sig.empty(); }
};

struct MetaTransaction {
    // The actual transaction the user wants to execute
    Transaction tx;

    // Venmo identity of the sender (instead of requiring them to hold gas tokens)
    std::string venmo_username;

    // Relayer signature: relayer signs to indicate they'll pay gas
    Signature relayer_sig;

    // The user signs the tx, relayer wraps it
    std::vector<uint8_t> serialize_for_relayer() const {
        auto buf = tx.serialize_for_signing();
        buf.insert(buf.end(), venmo_username.begin(), venmo_username.end());
        return buf;
    }

    Hash meta_hash() const {
        return sha256(serialize_for_relayer());
    }
};

} // namespace social_crypto
