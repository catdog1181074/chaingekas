# Chainge-to-CEX Kaspa Flow Analysis

This repository investigates how much native Kaspa (KAS) Chainge Finance likely controlled — and how much it transferred to centralized exchanges (CEXes) for potential sale. The analysis is based on transaction-level tracing on the Kaspa blockchain using the KrcBot public API.

---

## ❓ Why This Matters

Since the end of 2024, Chainge Finance has frozen the wKAS → KAS bridge — initially citing security concerns, then liquidity issues, and later claiming blacklisted vaults required intervention from DJ Qian. Meanwhile, many users have had funds stuck in the bridge.

Chainge has made various promises to re-open the CUSDT/KAS pair and restore wKAS liquidity, but with no confirmed resolution for months.

This repository aims to answer a critical question:

> **Does Chainge still hold the full KAS reserve needed to back all outstanding wKAS 1:1?**

To explore this, we track and quantify the amount of **KAS actually transferred from Chainge wallets into known CEX deposit addresses.**

---

## 📦 Contents

- `flow_data/` — A directory of wallet transaction histories, downloaded using the [krcbot Kaspa REST API](https://krcbot.com/api-docs)
- `trace_wallet_recursive.py` — Downloads transaction histories recursively from a starting wallet (such as the Chainge root wallet)
- `summarize_chainge_to_cex.py` — Analyzes the `flow_data/` to compute total KAS deposited to known exchange addresses, **only from wallets that are predominantly funded by Chainge**

---

## 🧠 Methodology Summary

### Step 1: Recursive Wallet Tracing

We begin with 5 known Chainge wallets:
- Root wallet: [`kaspa:qqwvnk...`](https://kas.fyi/address/kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5)
- Vault wallet: `kaspa:qq9zag...`
- 3 bridge-linked intermediary wallets

From these, we build a **trust graph** by tracing up to 4 levels deep (wallets funded by Chainge, or by those they funded, etc).

### Step 2: Classifying Wallets by Source

For each wallet that sent KAS to a known CEX deposit address, we:
- Analyze **who funded that wallet**, and
- Compute what **% of total inflow came from Chainge-linked sources**

Only wallets with **≥85% of their inflow from Chainge** are counted.

This strict rule prevents over-attributing CEX deposits to Chainge when most funds may have come from elsewhere.

### Step 3: Identifying Exchange Deposits

We scan `flow_data/` for unique `tx_id` transactions into known CEX deposit addresses, deduplicate, and print:
- Total KAS per exchange
- KAS sent to each known CEX wallet

---

## 🔍 Assumptions & Limitations

- **≥85% threshold:** We consider a wallet Chainge-funded only if 85% or more of its received KAS came from wallets linked to Chainge. This avoids overcounting wallets that received KAS from other sources.
- **4-hop limit:** We trace up to 4 levels deep from Chainge origins. This balances coverage with performance.
- **Hardcoded exchange addresses:** Only deposits into known MEXC, Gate.io, and CoinEx addresses are counted. Any undisclosed or new deposit addresses are excluded.
- **One-directional tracking:** We track only outbound KAS from Chainge. We do not track KAS coming back from exchanges or arbitrage cycles.

---

## 🚨 API Caution

All transaction data is fetched using the [KrcBot API](https://krcbot.com/api-docs). **Do not re-run the entire trace unless necessary.** This may overload public infrastructure.

Instead:
- Use the included pre-fetched data in `flow_data/`
- To do so, unzip the provided split `.zip` archives and work from there

---

## 📊 Key Finding

As of this analysis, **Chainge-linked wallets that were ≥85% funded by Chainge deposited approximately 332 million KAS into centralized exchanges.** The majority of this KAS flowed into **MEXC**, not Gate.io — contrary to earlier assumptions.

This strongly suggests that Chainge liquidated a large share of their native KAS holdings, potentially leaving a gap in wKAS collateral.

---

## 🤝 Contributing & Verification

This repo is meant to be transparent and reproducible. Feel free to:
- Propose updates to CEX or Chainge wallet lists
- Improve trust graph rules
- Compare results with your own data

If you're familiar with @KasperoLabs or @KrcBot — reach out! We welcome peer review.
