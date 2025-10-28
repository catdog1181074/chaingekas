import requests
import time
import os
import json
import pandas as pd
from datetime import datetime, timezone

API_BASE = "https://api.kaspa.org"
DATA_DIR = "flow_data_fullhistory"
os.makedirs(DATA_DIR, exist_ok=True)

CHAINGE_ROOTS = [
    "kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5", # original marked Chainge Finance wallet - used for bridging until end of January 27 2024
    "kaspa:qpgmt2dn8wcqf0436n0kueap7yx82n7raurlj6aqjc3t3wm9y5ssqtg9e4lsm",
    "kaspa:qpy03sxk3z22pacz2vkn2nrqeglvptugyqy54xal2skha6xh0cr7wjueueg79",
    "kaspa:qz9cqmddjppjyth8rngevfs767m5nvm0480nlgs5ve8d6aegv4g9xzu2tgg0u",
    "kaspa:qq9zagcza4jt76eev9jl5z0nqhe0thcu7js8larktj4sle7lvgnw7sfcewlty" # vault - verified function in known bridge transactions, NOT marked on kas.fyi
]

def format_timestamp(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()

def fetch_transactions(address, max_pages=100):
    txs = []
    before = int(time.time() * 1000)
    for _ in range(max_pages):
        url = (
            f"{API_BASE}/addresses/{address}/full-transactions-page"
            f"?limit=500&before={before}&after=0"
            f"&resolve_previous_outpoints=full&acceptance=accepted"
        )
        print(f"📦 Fetching before={before} for {address}")
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"❌ Error fetching transactions: {e}")
            break

        if not isinstance(data, list) or not data:
            print("✅ No more transactions.")
            break

        block_times = [tx.get("block_time", 0) for tx in data if tx.get("block_time")]
        if block_times:
            print(f"📅 Page covers: {format_timestamp(min(block_times))} to {format_timestamp(max(block_times))}")

        txs.extend(data)
        before = min(block_times)
        time.sleep(0.25)
    return txs

def trace_wallet(address):
    print(f"🔍 Fetching full non-recursive history for {address}")
    txs = fetch_transactions(address)
    rows = []

    for tx in txs:
        txid = tx.get("transaction_id")
        timestamp = format_timestamp(tx.get("block_time", 0))
        inputs = tx.get("inputs") or []
        outputs = tx.get("outputs") or []
        sender = next((inp.get("previous_outpoint_address") for inp in inputs if inp.get("previous_outpoint_address")), "(unknown)")
        for out in outputs:
            recipient = out.get("script_public_key_address")
            amount = out.get("amount", 0)
            if recipient:
                rows.append({
                    "tx_id": txid,
                    "timestamp": timestamp,
                    "sender": sender,
                    "recipient": recipient,
                    "amount_sompi": amount
                })

    df = pd.DataFrame(rows)
    output_path = os.path.join(DATA_DIR, f"{address.replace(':', '_')}_fullhistory.csv")
    df.to_csv(output_path, index=False)
    print(f"📝 Saved {len(rows)} rows to {output_path}")

if __name__ == "__main__":
    for addr in CHAINGE_ROOTS:
        trace_wallet(addr)
    print("✅ Completed full non-recursive transaction history export.")
