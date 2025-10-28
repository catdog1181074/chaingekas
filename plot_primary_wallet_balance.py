import pandas as pd
import matplotlib.pyplot as plt
import os

DATA_DIR = "flow_data_fullhistory"
PRIMARY_WALLET = "kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5"
# kaspa:qq9zagcza4jt76eev9jl5z0nqhe0thcu7js8larktj4sle7lvgnw7sfcewlty # <<-- check this wallet too - it functioned in Chainge bridging after Jan 27 2024

def get_filename(address):
    return os.path.join(DATA_DIR, f"{address.replace(':', '_')}_fullhistory.csv")

file_path = get_filename(PRIMARY_WALLET)
if not os.path.exists(file_path):
    print("❗ No data file found for the primary wallet.")
else:
    df = pd.read_csv(file_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df.sort_values("timestamp", inplace=True)

    before_dedup = len(df)
    df = df.drop_duplicates(subset=["tx_id", "amount_sompi", "sender", "recipient", "timestamp"])
    df = df[df["sender"] != df["recipient"]]
    after_dedup = len(df)
    print(f"✅ Deduplicated: {before_dedup - after_dedup} duplicates removed")

    df["flow"] = 0
    df.loc[df["recipient"] == PRIMARY_WALLET, "flow"] = df["amount_sompi"]
    df.loc[df["sender"] == PRIMARY_WALLET, "flow"] = -df["amount_sompi"]

    flow_df = df[["timestamp", "flow"]].copy()
    flow_df = flow_df.groupby("timestamp", as_index=False).sum()
    flow_df["balance"] = flow_df["flow"].cumsum()
    flow_df.set_index("timestamp", inplace=True)

    inflow = df[df["recipient"] == PRIMARY_WALLET]["amount_sompi"].sum() / 1e8
    outflow = df[df["sender"] == PRIMARY_WALLET]["amount_sompi"].sum() / 1e8
    max_balance = flow_df["balance"].max() / 1e8

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=False)

    ax1.plot(flow_df.index, flow_df["balance"] / 1e8, color="black", linewidth=2,
             label=f"Balance (max {max_balance:,.2f} KAS)")
    ax1.set_title("Primary Chainge Wallet Balance Over Time (Deduplicated)", fontsize=16)
    ax1.set_ylabel("Balance (KAS)", fontsize=14)
    ax1.legend(fontsize=12)
    ax1.grid(True)
    ax1.tick_params(axis='both', labelsize=12)

    bars = ax2.bar(["Inflow", "Outflow"], [inflow, -outflow], color=["blue", "orange"])
    ax2.set_title("Total Inflow vs Outflow (Deduplicated)", fontsize=16)
    ax2.set_ylabel("KAS", fontsize=14)
    ax2.tick_params(axis='both', labelsize=12)
    ax2.grid(True)

    # Manually create and apply legend with both labels
    labels = [
        f"Inflow: {inflow:,.2f} KAS",
        f"Outflow: {outflow:,.2f} KAS"
    ]
    ax2.legend(bars, labels, fontsize=12, loc="best")

    plt.tight_layout()
    plt.ion()
    plt.show()
    plt.savefig('chainge_primary_wallet_balance_flow.png')
