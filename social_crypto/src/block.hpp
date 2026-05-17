#pragma once

#include "crypto_utils.hpp"
#include "transaction.hpp"
#include <vector>
#include <string>
#include <cstdint>
#include <chrono>

namespace social_crypto {

struct BlockHeader {
    uint64_t index;
    uint64_t timestamp;
    Hash prev_hash;
    Hash merkle_root;
    uint64_t nonce;
    uint32_t difficulty;

    std::vector<uint8_t> serialize() const {
        std::vector<uint8_t> buf;
        auto* idx = reinterpret_cast<const uint8_t*>(&index);
        buf.insert(buf.end(), idx, idx + sizeof(index));
        auto* ts = reinterpret_cast<const uint8_t*>(&timestamp);
        buf.insert(buf.end(), ts, ts + sizeof(timestamp));
        buf.insert(buf.end(), prev_hash.begin(), prev_hash.end());
        buf.insert(buf.end(), merkle_root.begin(), merkle_root.end());
        auto* nc = reinterpret_cast<const uint8_t*>(&nonce);
        buf.insert(buf.end(), nc, nc + sizeof(nonce));
        auto* diff = reinterpret_cast<const uint8_t*>(&difficulty);
        buf.insert(buf.end(), diff, diff + sizeof(difficulty));
        return buf;
    }

    Hash block_hash() const {
        return sha256(serialize());
    }
};

struct Block {
    BlockHeader header;
    std::vector<Transaction> transactions;

    Hash compute_merkle_root() const {
        if (transactions.empty()) {
            Hash h{};
            h.fill(0);
            return h;
        }

        std::vector<Hash> hashes;
        for (const auto& tx : transactions) {
            hashes.push_back(tx.tx_hash());
        }

        while (hashes.size() > 1) {
            std::vector<Hash> next;
            for (size_t i = 0; i < hashes.size(); i += 2) {
                std::vector<uint8_t> combined;
                combined.insert(combined.end(), hashes[i].begin(), hashes[i].end());
                if (i + 1 < hashes.size()) {
                    combined.insert(combined.end(), hashes[i + 1].begin(), hashes[i + 1].end());
                } else {
                    combined.insert(combined.end(), hashes[i].begin(), hashes[i].end());
                }
                next.push_back(sha256(combined));
            }
            hashes = std::move(next);
        }
        return hashes[0];
    }

    void seal() {
        header.merkle_root = compute_merkle_root();
    }

    bool is_valid() const {
        auto computed = compute_merkle_root();
        return computed == header.merkle_root;
    }

    std::string block_hash_hex() const {
        return hash_to_hex(header.block_hash());
    }
};

} // namespace social_crypto
