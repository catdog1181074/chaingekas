import requests
import time
import os
import json
import pandas as pd
from datetime import datetime, timezone

API_BASE = "https://api.kaspa.org"
graph_data = {}
CHECKPOINT_FILE = "flow_data/tracer_state.json"
MAX_DEPTH = 2
START_TIMESTAMP_MS = 1685577600000  # June 1, 2023

def load_state():
    state = {"queue": [], "completed": set()}
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            loaded = json.load(f)
            state["queue"] = loaded.get("queue", [])
            state["completed"] = set(loaded.get("completed", []))
    return state

def save_state(state):
    to_save = {
        "queue": state["queue"],
        "completed": list(state["completed"])
    }
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(to_save, f, indent=2)

def format_timestamp(ms_timestamp):
    try:
        return datetime.fromtimestamp(ms_timestamp / 1000, tz=timezone.utc).isoformat()
    except Exception:
        return ""

def fetch_transactions(address, max_pages=100, start_timestamp=START_TIMESTAMP_MS):
    txs = []
    before = int(time.time() * 1000)
    retries = 0

    for _ in range(max_pages):
        url = (
            f"{API_BASE}/addresses/{address}/full-transactions-page"
            f"?limit=500&before={before}&after=0"
            f"&resolve_previous_outpoints=full&acceptance=accepted"
        )
        print(f"📦 Fetching transactions before {before} for {address}")
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            retries += 1
            if retries > 5:
                print(f"❌ Max retries reached for {address}. Error: {e}")
                break
            wait = 2 ** retries
            print(f"⚠️ Request failed: {e}. Retrying in {wait} seconds...")
            time.sleep(wait)
            continue

        if not isinstance(data, list) or not data:
            print("✅ No more transactions.")
            break

        block_times = [tx.get("block_time", 0) for tx in data if tx.get("block_time")]
        if block_times:
            min_time = format_timestamp(min(block_times))
            max_time = format_timestamp(max(block_times))
            print(f"📅 Page covers: {min_time} to {max_time}")

        filtered = [tx for tx in data if tx.get("block_time", 0) >= start_timestamp]
        txs.extend(filtered)
        before = min(tx.get("block_time", before) for tx in data)
        time.sleep(0.25)

    print(f"✅ Total fetched: {len(txs)} transactions for {address}")
    return txs

def trace_wallet(state, address, depth, force=False):
    if depth < 0 or (address in state["completed"] and not force):
        return

    print(f"🔍 Tracing {address} at depth {depth}")
    filename = f"flow_data/{address.replace(':', '_')}.csv"
    jsonfile = f"flow_data/{address.replace(':', '_')}_graph.json"

    if os.path.exists(filename) and not force:
        print(f"⏩ Skipping {address} (already processed)")
        return

    txs = fetch_transactions(address)

    os.makedirs("flow_data", exist_ok=True)

    edges = []
    rows = []

    for i, tx in enumerate(txs):
        txid = tx.get("transaction_id")
        timestamp = format_timestamp(tx.get("block_time"))
        inputs = tx.get("inputs") or []
        outputs = tx.get("outputs") or []        
        recipients = []
        sender = None

        for out in outputs:
            addr = out.get("script_public_key_address")
            amt = out.get("amount", 0)
            if addr:
                recipients.append((addr, amt))

        for inp in inputs:
            if inp.get("previous_outpoint_address"):
                sender = inp.get("previous_outpoint_address")
                break

        if i%100==0: print(f"🔎 [{i+1}/{len(txs)}] tx: {txid} | sender: {sender or '(unknown)'} | recipients: {len(recipients)}")

        for recipient, amount in recipients:
            rows.append({
                "tx_id": txid,
                "timestamp": timestamp,
                "sender": sender or "(unknown)",
                "recipient": recipient,
                "amount_sompi": amount
            })
            if sender and recipient:
                edges.append((sender, recipient))
            if recipient and recipient not in state["completed"]:
                state["queue"].append({"address": recipient, "depth": depth - 1})

    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False)
        print(f"📝 Wrote {len(rows)} rows to {filename}")

    graph_data[address] = {"edges": edges}
    with open(jsonfile, "w") as jf:
        json.dump(graph_data[address], jf, indent=2)
    print(f"📄 Graph JSON written to {jsonfile}")

    state["completed"].add(address)
    save_state(state)

CHAINGE_ROOTS = [
    "kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5",    
    "kaspa:qpgmt2dn8wcqf0436n0kueap7yx82n7raurlj6aqjc3t3wm9y5ssqtg9e4lsm",
    "kaspa:qpy03sxk3z22pacz2vkn2nrqeglvptugyqy54xal2skha6xh0cr7wjueueg79",
    "kaspa:qz9cqmddjppjyth8rngevfs767m5nvm0480nlgs5ve8d6aegv4g9xzu2tgg0u",
    "kaspa:qq9zagcza4jt76eev9jl5z0nqhe0thcu7js8larktj4sle7lvgnw7sfcewlty"
]

if __name__ == "__main__":
    state = load_state()
    if not state["queue"]:
        for root in CHAINGE_ROOTS:
            state["queue"].append({"address": root, "depth": MAX_DEPTH})

    while state["queue"]:
        current = state["queue"].pop(0)
        trace_wallet(state, current["address"], current["depth"], force=False)

    print("✅ Full recursive tracing complete. All data saved to 'flow_data/'")
