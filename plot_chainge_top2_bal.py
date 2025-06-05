import pandas as pd
import matplotlib.pyplot as plt
import os

DATA_DIR = "flow_data_fullhistory"
WALLETS = {
    "kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5": "Chainge 1",
    "kaspa:qpgmt2dn8wcqf0436n0kueap7yx82n7raurlj6aqjc3t3wm9y5ssqtg9e4lsm": "Chainge 2",
}

wallet_ids = list(WALLETS.keys())
dfs = []

for wallet in wallet_ids:
    file_path = os.path.join(DATA_DIR, f"{wallet.replace(':', '_')}_fullhistory.csv")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df["wallet"] = wallet
        dfs.append(df)

if not dfs:
    print("❗ No wallet CSV files found.")
else:
    df_all = pd.concat(dfs, ignore_index=True)
    df_all["timestamp"] = pd.to_datetime(df_all["timestamp"], utc=True, errors="coerce")
    df_all = df_all.dropna(subset=["timestamp"])
    df_all = df_all.drop_duplicates(subset=["tx_id", "amount_sompi", "sender", "recipient", "timestamp"])
    df_all = df_all[df_all["sender"] != df_all["recipient"]]
    df_all.sort_values("timestamp", inplace=True)

    # Filter only inter-wallet relevant transactions
    flows = []
    for wallet, label in WALLETS.items():
        inflow = df_all[df_all["recipient"] == wallet].copy()
        inflow["wallet"] = label
        inflow["flow"] = inflow["amount_sompi"]
        outflow = df_all[df_all["sender"] == wallet].copy()
        outflow["wallet"] = label
        outflow["flow"] = -outflow["amount_sompi"]
        flows.append(pd.concat([inflow, outflow]))

    tx_df = pd.concat(flows)[["timestamp", "wallet", "flow"]]
    tx_df = tx_df.groupby(["timestamp", "wallet"], as_index=False).sum()
    tx_df["balance"] = tx_df.groupby("wallet")["flow"].cumsum()

    # Max balance and totals
    inflows = {}
    outflows = {}
    max_balances = {}
    for wallet, label in WALLETS.items():
        inflow = df_all[df_all["recipient"] == wallet]["amount_sompi"].sum() / 1e8
        outflow = df_all[df_all["sender"] == wallet]["amount_sompi"].sum() / 1e8
        max_bal = tx_df[tx_df["wallet"] == label]["balance"].max() / 1e8
        inflows[label] = inflow
        outflows[label] = outflow
        max_balances[label] = max_bal

    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=False)

    for label in WALLETS.values():
        wdf = tx_df[tx_df["wallet"] == label]
        ax1.plot(wdf["timestamp"], wdf["balance"] / 1e8, label=f"{label} (max {max_balances[label]:,.0f} KAS)")

    ax1.set_title("Chainge Wallet Balances Over Time (Corrected for Inter-wallet Flow)", fontsize=16)
    ax1.set_ylabel("Balance (KAS)", fontsize=14)
    ax1.legend(fontsize=10)
    ax1.grid(True)
    ax1.tick_params(axis='both', labelsize=12)

    labels = list(WALLETS.values())
    inflow_vals = [inflows[l] for l in labels]
    outflow_vals = [-outflows[l] for l in labels]
    x = range(len(labels))
    bars1 = ax2.bar(x, inflow_vals, width=0.4, label="Inflow", color="blue", align="center")
    bars2 = ax2.bar([i + 0.4 for i in x], outflow_vals, width=0.4, label="Outflow", color="orange", align="center")

    for i, l in enumerate(labels):
        ax2.text(i, inflow_vals[i] + 2, f"{inflow_vals[i]:,.0f}", ha="center", fontsize=10)
        ax2.text(i + 0.4, outflow_vals[i] - 4, f"{-outflow_vals[i]:,.0f}", ha="center", fontsize=10)

    ax2.set_title("Total Inflow vs Outflow per Wallet", fontsize=16)
    ax2.set_ylabel("KAS", fontsize=14)
    ax2.set_xticks([i + 0.2 for i in x])
    ax2.set_xticklabels(labels, fontsize=12)
    ax2.legend(fontsize=12)
    ax2.grid(True)

    plt.tight_layout()
    plt.ion()
    plt.show()
    plt.savefig('top2_chainge_wallet_balances.png')

