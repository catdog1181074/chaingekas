# 🧾 Chainge-to-CEX Kaspa Flow Analysis

This repository investigates how much native Kaspa (KAS) Chainge Finance likely controlled — and how much was transferred to centralized exchanges (CEXes), presumably for liquidation. The analysis is based on transaction-level tracing using the [KrcBot public API](https://krcbot.com/api-docs), and results are visualized as a verified shell graph.

---

## ❓ Why This Matters

Since late 2024, Chainge Finance has frozen the **wKAS → KAS bridge**, citing security, liquidity, and vault blacklisting concerns. DJ Qian, Chainge’s founder, has repeatedly promised a “liquidity injection,” but as of mid-2025, users remain unable to redeem wKAS.

Despite claims that the bridge will reopen, no proof-of-reserves or redemption path has been provided.

> **This raises the question:**
> Has the native KAS meant to back wKAS been retained — or sold?

This repository traces actual KAS outflows from Chainge-linked wallets to known exchange deposit addresses.

---

## 📁 Contents

- `flow_data/` — All wallet-level transaction CSVs (from KrcBot)
- `chainge_flow_shell_annot.py` — Full tracing, attribution, and graph visualization
- `summarize_chainge_to_cex.py` — Aggregates deposit totals by attribution source
- `summary_chainge_to_cex_vs_threshold.py` — Plots CEX flows as a function of attribution threshold

---

## 🧠 Methodology Summary

### Step 1: Recursive Wallet Tracing

We begin with 5 Chainge-linked wallets:
- 🟠 `kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5` (Root wallet)
- 🟠 3 other wallets labeled on kas.fyi
- 🟠 The previously so-called “Vault” wallet (`kaspa:qq9zagcza4jt76eev9jl5z0nqhe0thcu7js8larktj4sle7lvgnw7sfcewlty`) is included. While we previously stated it has weak linkage (only ~26% of inflow from other Chainge marked wallets on kas.fyi), users have now confirmed bridging transactions involved this wallet AFTER Jan 27 2024. This is when the Root wallet transferred ~57M Kaspa to the ”Vault”. 

We recursively trace wallet inflows up to **4 hops deep**, forming a funding graph from Chainge to any recipient wallet.

---

### Step 2: Attribution Filtering (≥95%)

For each wallet that sent KAS to a known CEX:
- We compute the **% of its total inflow that came (directly or indirectly) from Chainge**
- Only wallets with **≥95% Chainge funding** are included

This ensures we only count flows from wallets highly likely to be Chainge-controlled or Chainge-funded.

---

### Step 3: CEX Matching + Deduplication

We match deposit `tx_id`s against a verified list of:
- MEXC deposit wallets
- Gate.io deposit wallets
- CoinEx deposit wallets

Each transaction is **deduplicated** by `tx_id`. Totals are aggregated per exchange.

---

### Step 4: Graph Visualization

We build a shell-based flow graph:
- 🟠 Chainge wallets at the center
- 🔵 Verified intermediaries layered by hop count
- 🔴 CEX wallets forced into the outermost shell

Edge widths are scaled by transfer volume (capped to 10×).

📤 See: `chainge_verified_shell_final.png` and `.pdf`

---

## 🔍 Assumptions & Limitations

- **≥95% attribution threshold** avoids over-attribution to Chainge
- **4-hop trace depth** balances accuracy and reach
- **Only known CEX deposit addresses** are included

All data is one-directional (Chainge → CEX). No return flows or self-custody are considered.

---

## 🚨 API Usage Warning

All transaction data comes from Kaspa API calls. 
**Please avoid re-running full traces unnecessarily**, as this may overload public nodes.

Use the included pre-fetched `.csv` files in `flow_data/`.

---

## 📊 Key Findings

💥 **~318 million KAS** was deposited to exchanges from wallets ≥95% funded by Chainge

Breakdown:
- **MEXC**: ~299M
- **Gate.io**: 19M


📈 Most liquidation occurred through MEXC — not Gate.io.

The visualized graph shows strong and direct off-ramp behavior from Chainge-origin wallets to CEXes.

---

## 🤝 Contributing & Verification

This repo is designed to be transparent, reproducible, and audit-friendly.

You can:
- Suggest updated wallet labels
- Tune attribution thresholds
- Fork and modify hop-depth or flow constraints
- Compare with @KasperoLabs

We welcome peer review and alternative visualizations.
