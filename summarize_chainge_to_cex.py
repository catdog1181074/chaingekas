import os
import csv
import pandas as pd
from collections import defaultdict, deque

FLOW_DATA_DIR = "flow_data"
MAX_DEPTH = 4
THRESHOLD = 0.85

CHAINGE_ORIGINS = {
    "kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5",
    "kaspa:qq9zagcza4jt76eev9jl5z0nqhe0thcu7js8larktj4sle7lvgnw7sfcewlty",
    "kaspa:qpgmt2dn8wcqf0436n0kueap7yx82n7raurlj6aqjc3t3wm9y5ssqtg9e4lsm",
    "kaspa:qpy03sxk3z22pacz2vkn2nrqeglvptugyqy54xal2skha6xh0cr7wjueueg79",
    "kaspa:qz9cqmddjppjyth8rngevfs767m5nvm0480nlgs5ve8d6aegv4g9xzu2tgg0u"
}

CEX_WALLETS = {
    "kaspa:qzrula2hgnym93zuwetfaxw7valc9j967scgcxgxg3yzkgd2nfgm26erngrfh": "MEXC",
    "kaspa:qpjunp39ssazf4rzfxxu0hd35xggfxn6lq0ls9u9q6peevzcmcv4xmv9q4njd": "MEXC",
    "kaspa:qqetp7ct8kqss99fxmymyz5t3fezppxp0t58wl6pawp27elqd46uudme00cl0": "MEXC",
    "kaspa:qpzpfwcsqsxhxwup26r55fd0ghqlhyugz8cp6y3wxuddc02vcxtjg75pspnwz": "MEXC",
    "kaspa:qz7gtc6gkgcj482s6jltww0j4n7664dhvgut5t4pn7333l7mmwah7veg0zxjq": "MEXC",
    "kaspa:qrayw3qwwza362uxrqxntatnz3s7pzqha7amu532p82khklugkhgj2ls49n98": "MEXC",
    "kaspa:qp3dpzfcjp2d7n5pslneg8wkkvp8wrw0ae60jff4a8evr6qn6g2gks0qspre3": "MEXC",
    "kaspa:qpr5pdq0a7cn28vnh37099yaayf7zkjz30az60atk4pdqknnnwhnxww43zgpw": "MEXC",
    "kaspa:qrj59crrt87qul4p7e9ywa7mz42cffjmk29p7ry7fd8vuxmla6fw5t4yscq00": "MEXC",
    "kaspa:qrelgny7sr3vahq69yykxx36m65gvmhryxrlwngfzgu8xkdslum2yxjp3ap8m": "Gate.io",
    "kaspa:qpqpyavkqnp60q6t4sfctz4yp3n0ct963z65rxkd5ft32vkehnd3wx8jqctr2": "CoinEx"
}

# Step 1: Load deposit transactions into known CEX wallets
deposits = []
tx_seen = set()
for fname in os.listdir(FLOW_DATA_DIR):
    if not fname.endswith(".csv"):
        continue
    sender = fname.replace("_", ":").replace(".csv", "")
    df = pd.read_csv(os.path.join(FLOW_DATA_DIR, fname))
    for row in df[df["direction"] == "sent"].itertuples():
        if row.peer_address in CEX_WALLETS and row.tx_id not in tx_seen:
            tx_seen.add(row.tx_id)
            deposits.append({
                "tx_id": row.tx_id,
                "sender": sender,
                "to_wallet": row.peer_address,
                "cex": CEX_WALLETS[row.peer_address],
                "amount_kas": int(row.amount_sompi) / 1e8
            })

df_deposits = pd.DataFrame(deposits)

# Step 2: Build reverse graph of wallet flows
reverse_graph = defaultdict(set)
for fname in os.listdir(FLOW_DATA_DIR):
    wallet = fname.replace("_", ":").replace(".csv", "")
    df = pd.read_csv(os.path.join(FLOW_DATA_DIR, fname))
    for row in df[df["direction"] == "received"].itertuples():
        reverse_graph[wallet].add(row.peer_address)

# Step 3: Trace inflow sources to each depositing wallet
funding_records = []
for wallet in df_deposits["sender"].unique():
    path = os.path.join(FLOW_DATA_DIR, f"{wallet.replace(':', '_')}.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        df_in = df[df["direction"] == "received"]
        for row in df_in.itertuples():
            funding_records.append({
                "recipient": wallet,
                "from_wallet": row.peer_address,
                "amount_kas": int(row.amount_sompi) / 1e8
            })

df_funding = pd.DataFrame(funding_records)

# Step 4: Label each funder as Chainge or External via 4-hop reverse trace
wallet_class = {}
for wallet in df_funding["from_wallet"].unique():
    visited = set()
    queue = deque([(wallet, 0)])
    found = False
    while queue:
        current, depth = queue.popleft()
        if current in CHAINGE_ORIGINS:
            found = True
            break
        if depth >= MAX_DEPTH or current in visited:
            continue
        visited.add(current)
        for prev in reverse_graph.get(current, set()):
            if prev not in visited:
                queue.append((prev, depth + 1))
    wallet_class[wallet] = "Chainge" if found else "External"

df_funding["source"] = df_funding["from_wallet"].map(wallet_class)

# Step 5: Calculate funding ratios
df_ratio = df_funding.groupby(["recipient", "source"], as_index=False)["amount_kas"].sum()
df_pivot = df_ratio.pivot(index="recipient", columns="source", values="amount_kas").fillna(0)
df_pivot["total"] = df_pivot.sum(axis=1)
df_pivot["chainge_pct"] = df_pivot.get("Chainge", 0) / df_pivot["total"]
eligible_wallets = df_pivot[df_pivot["chainge_pct"] >= THRESHOLD].index

# Step 6: Filter and summarize final results
df_final = df_deposits[df_deposits["sender"].isin(eligible_wallets)]
df_summary = df_final.groupby(["cex", "to_wallet"], as_index=False)["amount_kas"].sum()
total_kas = df_final["amount_kas"].sum()

print(f"🔍 Total KAS sent from ≥85%-Chainge-funded wallets to CEXes: {total_kas:,.2f} KAS\\n")
for row in df_summary.itertuples():
    print(f"{row.cex:8} → {row.to_wallet} : {row.amount_kas:,.2f} KAS")
    
