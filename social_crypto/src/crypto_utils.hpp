#pragma once

#include <string>
#include <vector>
#include <array>
#include <cstdint>
#include <sstream>
#include <iomanip>
#include <openssl/sha.h>
#include <openssl/evp.h>
#include <openssl/pem.h>
#include <openssl/ec.h>
#include <openssl/obj_mac.h>

namespace social_crypto {

using Hash = std::array<uint8_t, SHA256_DIGEST_LENGTH>;
using Address = std::array<uint8_t, 20>;  // 160-bit address
using Signature = std::vector<uint8_t>;
using PublicKey = std::vector<uint8_t>;
using PrivateKey = std::vector<uint8_t>;

inline Hash sha256(const std::string& data) {
    Hash h{};
    SHA256(reinterpret_cast<const uint8_t*>(data.data()), data.size(), h.data());
    return h;
}

inline Hash sha256(const std::vector<uint8_t>& data) {
    Hash h{};
    SHA256(data.data(), data.size(), h.data());
    return h;
}

inline Hash double_sha256(const std::string& data) {
    return sha256(sha256(data));
}

inline Hash double_sha256(const std::vector<uint8_t>& data) {
    return sha256(sha256(data));
}

inline std::string hash_to_hex(const Hash& h) {
    std::ostringstream oss;
    for (auto b : h) oss << std::hex << std::setfill('0') << std::setw(2) << (int)b;
    return oss.str();
}

inline std::string address_to_hex(const Address& a) {
    std::ostringstream oss;
    oss << "0x";
    for (auto b : a) oss << std::hex << std::setfill('0') << std::setw(2) << (int)b;
    return oss.str();
}

inline Address hash_to_address(const Hash& h) {
    Address a{};
    for (size_t i = 0; i < 20; i++) a[i] = h[i];
    return a;
}

inline std::string bytes_to_hex(const std::vector<uint8_t>& data) {
    std::ostringstream oss;
    for (auto b : data) oss << std::hex << std::setfill('0') << std::setw(2) << (int)b;
    return oss.str();
}

inline std::vector<uint8_t> hex_to_bytes(const std::string& hex) {
    std::vector<uint8_t> bytes;
    for (size_t i = 0; i < hex.length(); i += 2) {
        std::string byte_str = hex.substr(i, 2);
        bytes.push_back(static_cast<uint8_t>(std::stoul(byte_str, nullptr, 16)));
    }
    return bytes;
}

struct KeyPair {
    PublicKey pub_key;
    PrivateKey priv_key;

    Address address() const {
        auto h = sha256(pub_key);
        return hash_to_address(h);
    }

    std::string address_hex() const {
        return address_to_hex(address());
    }
};

inline KeyPair generate_keypair() {
    KeyPair kp;

    EVP_PKEY_CTX* ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_EC, nullptr);
    EVP_PKEY_keygen_init(ctx);
    EVP_PKEY_CTX_set_ec_paramgen_curve_nid(ctx, NID_secp256k1);

    EVP_PKEY* pkey = nullptr;
    EVP_PKEY_keygen(ctx, &pkey);
    EVP_PKEY_CTX_free(ctx);

    // Serialize public key
    size_t pub_len = 0;
    EVP_PKEY_get_raw_public_key(pkey, nullptr, &pub_len);
    kp.pub_key.resize(pub_len);
    EVP_PKEY_get_raw_public_key(pkey, kp.pub_key.data(), &pub_len);

    // Serialize private key
    size_t priv_len = 0;
    EVP_PKEY_get_raw_private_key(pkey, nullptr, &priv_len);
    kp.priv_key.resize(priv_len);
    EVP_PKEY_get_raw_private_key(pkey, kp.priv_key.data(), &priv_len);

    EVP_PKEY_free(pkey);
    return kp;
}

inline Signature sign(const std::vector<uint8_t>& message, const PrivateKey& priv_key) {
    EVP_PKEY* pkey = EVP_PKEY_new_raw_private_key(EVP_PKEY_EC, nullptr,
                                                    priv_key.data(), priv_key.size());

    EVP_MD_CTX* md_ctx = EVP_MD_CTX_new();
    EVP_DigestSignInit(md_ctx, nullptr, EVP_sha256(), nullptr, pkey);

    size_t sig_len = 0;
    EVP_DigestSign(md_ctx, nullptr, &sig_len, message.data(), message.size());

    Signature sig(sig_len);
    EVP_DigestSign(md_ctx, sig.data(), &sig_len, message.data(), message.size());

    EVP_MD_CTX_free(md_ctx);
    EVP_PKEY_free(pkey);
    return sig;
}

inline bool verify(const std::vector<uint8_t>& message, const Signature& sig,
                   const PublicKey& pub_key) {
    EVP_PKEY* pkey = EVP_PKEY_new_raw_public_key(EVP_PKEY_EC, nullptr,
                                                   pub_key.data(), pub_key.size());

    EVP_MD_CTX* md_ctx = EVP_MD_CTX_new();
    EVP_DigestVerifyInit(md_ctx, nullptr, EVP_sha256(), nullptr, pkey);

    int result = EVP_DigestVerify(md_ctx, sig.data(), sig.size(),
                                   message.data(), message.size());

    EVP_MD_CTX_free(md_ctx);
    EVP_PKEY_free(pkey);
    return result == 1;
}

} // namespace social_crypto
