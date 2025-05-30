# 🧾 Chainge-to-CEX Kaspa Flow Analysis

This repository investigates how much native Kaspa (KAS) Chainge Finance likely controlled — and how much it transferred to centralized exchanges (CEXes), presumably for liquidation. The analysis is based on transaction-level tracing on the Kaspa blockchain using the [KrcBot public API](https://krcbot.com/api-docs).

---

## ❓ Why This Matters

Since late 2024, Chainge Finance has frozen the **wKAS → KAS bridge**, initially citing security concerns, then liquidity issues, and later claiming its vaults had been blacklisted. DJ Qian, the founder, promised intervention and a "liquidity injection," but as of mid-2025, many users’ funds remain trapped in wKAS.

Despite repeated claims that the bridge will reopen, no clear reserve proof or redemption pathway has been provided.

This raises a critical question:

> **Does Chainge still hold enough native KAS to back wKAS 1:1 — or has that KAS been sold?**

This repository traces the flow of native KAS from known Chainge wallets to known CEX deposit addresses.

---

## 📁 Contents

- `flow_data/` — Wallet-level transaction histories, downloaded via KrcBot
- `trace_wallet_recursive.py` — Recursively fetches and saves wallet transaction data
- `summarize_chainge_to_cex.py` — Computes total KAS sent to CEX addresses, filtered by funding attribution
- `summary_chainge_to_cex_vs_threshold.py` — Analyzes KAS-to-CEX deposits as a function of attribution threshold

---

## 🧠 Methodology Summary

### Step 1: Recursive Wallet Tracing

We begin with **5 labelled Chainge wallets**, including:
- 🟩 The Chainge Finance Root wallet (kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5)  
- 🟩 3 labeled Chainge wallets on kas.fyi (kaspa:qpgmt2dn8wcqf0436n0kueap7yx82n7raurlj6aqjc3t3wm9y5ssqtg9e4lsm, kaspa:qpy03sxk3z22pacz2vkn2nrqeglvptugyqy54xal2skha6xh0cr7wjueueg79, kaspa:qz9cqmddjppjyth8rngevfs767m5nvm0480nlgs5ve8d6aegv4g9xzu2tgg0u)  
- 🟩 The "Vault" (now **excluded from attribution** due to only ~26% funding from known Chainge sources, though directly received ~57M Kas from Root wallet in Jan 2024)

We trace wallet inflows up to **4 hops deep**, building a “trust graph” of which wallets are funded (directly or indirectly) by Chainge.

---

### Step 2: Source Attribution by Threshold

For each wallet that sent KAS to a known CEX deposit address, we:
- Analyze its funding history
- Calculate the **% of total inflow originating from Chainge wallets**

Only wallets with **≥85% Chainge attribution** are included in the primary analysis. This avoids false positives and ensures we only include wallets likely controlled by Chainge.

---

### Step 3: Identifying CEX Deposits

We match deduplicated `tx_id` entries against a manually verified list of MEXC, Gate.io, and CoinEx deposit wallets. We then aggregate:
- Total KAS deposited per CEX
- Total KAS deposited by all ≥85% Chainge-linked wallets

---

## 🔍 Assumptions & Limitations

- **≥85% threshold** avoids attributing mixed-source wallets to Chainge
- **4-hop trace depth** provides adequate reach while keeping the graph computationally manageable
- **Known CEX deposit addresses only** — undisclosed CEX wallets are not captured
- **One-directional trace** — inflows back from CEXes are not analyzed

The Vault wallet is **excluded from attribution** in the final analysis due to insufficient linkage (only ~26% of its inflow came from Chainge Root or labelled wallets).

---

## 🚨 API Usage Warning

All transaction data comes from [KrcBot’s public API](https://krcbot.com/api-docs).  
**Do not re-run the full trace unless absolutely necessary**, as this may overload public infrastructure.

Use the included pre-fetched `.csv` files in `flow_data/` — unzip the `.zip` archive to proceed with local analysis.

---

## 📊 Key Finding

> 💥 **~332 million KAS** was deposited to MEXC and other CEXes by wallets ≥85% funded by Chainge Root or known Chainge-linked wallets.

Most of these deposits went to **MEXC**, not Gate.io — contradicting earlier assumptions.  
This strongly supports the conclusion that **Chainge Finance liquidated a large portion of its native KAS holdings**.

---

## 🤝 Contributing & Verification

This repository is designed to be **transparent and reproducible**. You can:
- Propose new wallet tags for Chainge or CEXes
- Tune the attribution threshold
- Fork and run your own analysis
- Compare with other datasets (e.g., @KasperoLabs or @KrcBot)

We welcome peer review and collaboration.

