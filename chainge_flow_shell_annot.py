import os
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import math
from collections import defaultdict, deque

FLOW_DIR = "flow_data"
MAX_DEPTH = 6
THRESHOLD = 0.95

CHAINGE_ROOTS = {
    "kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5", # functioned in bridging until Jan 27 2024 - MARKED in kas.fyi as Chainge Finance Wallet
    "kaspa:qpgmt2dn8wcqf0436n0kueap7yx82n7raurlj6aqjc3t3wm9y5ssqtg9e4lsm",
    "kaspa:qpy03sxk3z22pacz2vkn2nrqeglvptugyqy54xal2skha6xh0cr7wjueueg79",
    "kaspa:qz9cqmddjppjyth8rngevfs767m5nvm0480nlgs5ve8d6aegv4g9xzu2tgg0u",
    "kaspa:qq9zagcza4jt76eev9jl5z0nqhe0thcu7js8larktj4sle7lvgnw7sfcewlty" # this functioned in bridging after Jan 27 2024 - NOT marked in kas.fyi
}

CEX_WALLETS = {
    "kaspa:qzrula2hgnym93zuwetfaxw7valc9j967scgcxgxg3yzkgd2nfgm26erngrfh": "MEXC1",
    "kaspa:qpjunp39ssazf4rzfxxu0hd35xggfxn6lq0ls9u9q6peevzcmcv4xmv9q4njd": "MEXC2",
    "kaspa:qqetp7ct8kqss99fxmymyz5t3fezppxp0t58wl6pawp27elqd46uudme00cl0": "MEXC3",
    "kaspa:qpzpfwcsqsxhxwup26r55fd0ghqlhyugz8cp6y3wxuddc02vcxtjg75pspnwz": "MEXC4",
    "kaspa:qz7gtc6gkgcj482s6jltww0j4n7664dhvgut5t4pn7333l7mmwah7veg0zxjq": "MEXC5",
    "kaspa:qrayw3qwwza362uxrqxntatnz3s7pzqha7amu532p82khklugkhgj2ls49n98": "MEXC6",
    "kaspa:qp3dpzfcjp2d7n5pslneg8wkkvp8wrw0ae60jff4a8evr6qn6g2gks0qspre3": "MEXC7",
    "kaspa:qpr5pdq0a7cn28vnh37099yaayf7zkjz30az60atk4pdqknnnwhnxww43zgpw": "MEXC8",
    "kaspa:qrj59crrt87qul4p7e9ywa7mz42cffjmk29p7ry7fd8vuxmla6fw5t4yscq00": "MEXC9",
    "kaspa:qrelgny7sr3vahq69yykxx36m65gvmhryxrlwngfzgu8xkdslum2yxjp3ap8m": "Gate.io",
    "kaspa:qpqpyavkqnp60q6t4sfctz4yp3n0ct963z65rxkd5ft32vkehnd3wx8jqctr2": "CoinEx"
}

# Load all wallet CSVs
def load_flow_data():
    data = {}
    for fname in os.listdir(FLOW_DIR):
        if fname.endswith(".csv"):
            wallet = fname.replace("_", ":").replace(".csv", "")
            df = pd.read_csv(os.path.join(FLOW_DIR, fname))
            data[wallet] = df
    return data

flow_data = load_flow_data()

# Reverse graph: who funded whom
reverse_graph = defaultdict(set)
for wallet, df in flow_data.items():
    for row in df[df["direction"] == "received"].itertuples():
        reverse_graph[wallet].add(row.peer_address)

# Deduplicated CEX deposits
tx_seen = set()
deposit_rows = []
for wallet, df in flow_data.items():
    for row in df[df["direction"] == "sent"].itertuples():
        if row.peer_address in CEX_WALLETS and row.tx_id not in tx_seen:
            tx_seen.add(row.tx_id)
            deposit_rows.append({
                "tx_id": row.tx_id,
                "from_address": wallet,
                "to_wallet": row.peer_address,
                "amount_kas": int(row.amount_sompi) / 1e8
            })

df_deposits = pd.DataFrame(deposit_rows)

# Attribution tracing
funding_records = []
for wallet, df in flow_data.items():
    for row in df[df["direction"] == "received"].itertuples():
        funding_records.append({
            "recipient": wallet,
            "from_wallet": row.peer_address,
            "amount_kas": int(row.amount_sompi) / 1e8
        })

df_funding = pd.DataFrame(funding_records)

wallet_class = {}
for wallet in df_funding["from_wallet"].unique():
    visited = set()
    queue = deque([(wallet, 0)])
    found = False
    while queue:
        current, depth = queue.popleft()
        if current in CHAINGE_ROOTS:
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
df_ratio = df_funding.groupby(["recipient", "source"], as_index=False)["amount_kas"].sum()
df_pivot = df_ratio.pivot(index="recipient", columns="source", values="amount_kas").fillna(0)
df_pivot["total"] = df_pivot.sum(axis=1)
df_pivot["chainge_pct"] = df_pivot.get("Chainge", 0) / df_pivot["total"]

verified_wallets = df_pivot[df_pivot["chainge_pct"] >= THRESHOLD].index
df_verified = df_deposits[df_deposits["from_address"].isin(verified_wallets)]
verified_intermediaries = set(df_verified["from_address"].unique())

# Build flow graph G
G = nx.DiGraph()
for row in df_verified.itertuples():
    G.add_edge(row.from_address, row.to_wallet, weight=row.amount_kas)

# Add Chainge → intermediary + intermediary → intermediary
for wallet in verified_wallets:
    if wallet not in flow_data:
        continue
    for row in flow_data[wallet][flow_data[wallet]["direction"] == "received"].itertuples():
        src = row.peer_address
        amt = int(row.amount_sompi) / 1e8
        if src in CHAINGE_ROOTS or src in verified_wallets:
            G.add_edge(src, wallet, weight=amt)

# Shell layout: Chainge → intermediary → CEX
shell_map = {}
queue = deque([(r, 0) for r in CHAINGE_ROOTS if r in G])
visited = set()
while queue:
    node, depth = queue.popleft()
    if node in visited:
        continue
    visited.add(node)
    shell_map[node] = depth
    for nbr in G.successors(node):
        if nbr not in visited:
            queue.append((nbr, depth + 1))

# Assign to shell layers
shells = defaultdict(list)
for node, layer in shell_map.items():
    shells[layer].append(node)
shells[max(shells.keys()) + 1] = [n for n in G.nodes if n in CEX_WALLETS]
shells = [shells[i] for i in sorted(shells)]

# Layout with spacing
def custom_shell_layout(nlist, spacing=6.5):
    pos = {}
    for radius, nodes in enumerate(nlist, start=1):
        theta = 2 * math.pi / max(len(nodes), 1)
        for i, node in enumerate(nodes):
            angle = theta * i
            pos[node] = (spacing * radius * math.cos(angle), spacing * radius * math.sin(angle))
    return pos

pos = custom_shell_layout(shells)
G = G.subgraph(pos.keys()).copy()

# Node visuals
node_colors = []
node_sizes = []
labels = {}
for node in G.nodes:
    if node in CHAINGE_ROOTS:
        node_colors.append("orange")
        node_sizes.append(1200)
        labels[node] = "Chainge"
    elif node in CEX_WALLETS:
        node_colors.append("red")
        node_sizes.append(1200)
        labels[node] = CEX_WALLETS[node]
    else:
        node_colors.append("steelblue")
        node_sizes.append(100)
        labels[node] = node[:4] + "..." + node[-4:]

# Scaled edge widths (clamped to 1–10×)
weights_raw = [G[u][v]["weight"] for u, v in G.edges()]
min_w, max_w = min(weights_raw), max(weights_raw)
edge_weights = []
for u, v in G.edges():
    w = G[u][v]["weight"]
    scale = 1.0 + 9.0 * (w - min_w) / (max_w - min_w) if max_w > min_w else 1.0
    edge_weights.append(scale)

# Plot
fig, ax = plt.subplots(figsize=(16, 16))
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
nx.draw_networkx_edges(G, pos, edge_color="gray", width=edge_weights, arrows=True, arrowsize=10, ax=ax)
nx.draw_networkx_labels(G, pos, labels=labels, font_size=6, ax=ax)

# Main legend
import matplotlib.patches as mpatches
legend = [
    mpatches.Patch(color="orange", label="Chainge Root"),
    mpatches.Patch(color="steelblue", label="Intermediary Wallet"),
    mpatches.Patch(color="red", label="CEX Wallet")
]
plt.legend(handles=legend, loc="upper left")

# Second legend: total per CEX
cex_totals = df_verified.groupby("to_wallet")["amount_kas"].sum()
cex_legend = "\n".join([f"{CEX_WALLETS.get(k, k[-4:])}: {v:,.0f} KAS" for k, v in cex_totals.items()])
plt.gcf().text(0.73, 0.88, "CEX Totals:\n" + cex_legend, fontsize=8, ha='left')

plt.title("Chainge → Intermediary → CEX Flow (≥95% Verified)", fontsize=14)
plt.axis("off")
plt.tight_layout()
plt.savefig("chainge_verified_shell_final.png", dpi=600)
plt.savefig("chainge_verified_shell_final.pdf")
plt.show()

print(f"Total deduplicated KAS sent to CEX: {df_verified['amount_kas'].sum():,.2f} KAS")
