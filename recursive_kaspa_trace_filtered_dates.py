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
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"queue": [], "completed": set()}

def save_state(state):
    state["completed"] = list(state["completed"])
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f, indent=2)

def get_transaction(txid):
    try:
        resp = requests.get(f"{API_BASE}/transactions/{txid}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ Failed to fetch transaction {txid}: {e}")
        return None

def get_previous_output_address(txid, index):
    tx = get_transaction(txid)
    if not tx:
        return None
    for out in tx.get("outputs", []):
        if out.get("index") == index:
            return out.get("script_public_key_address")
    return None

def find_most_recent_sender(txid, depth=3):
    tx = get_transaction(txid)
    if not tx:
        return None
    for inp in tx.get("inputs", []):
        prev_hash = inp.get("previous_outpoint_hash")
        prev_index = int(inp.get("previous_outpoint_index", 0))
        if prev_hash:
            sender = get_previous_output_address(prev_hash, prev_index)
            if sender:
                return sender
            elif depth > 1:
                return find_most_recent_sender(prev_hash, depth - 1)
    return None

def extract_final_recipients(tx):
    recipients = []
    for out in tx.get("outputs", []):
        addr = out.get("script_public_key_address")
        if addr:
            recipients.append((addr, out.get("amount", 0)))
    return recipients

def format_timestamp(ms_timestamp):
    try:
        return datetime.fromtimestamp(ms_timestamp / 1000, tz=timezone.utc).isoformat()
    except Exception:
        return ""

def trace_wallet(state, address, depth, force=False):
    if depth < 0 or (address in state["completed"] and not force):
        return

    print(f"🔍 Tracing {address} at depth {depth}")
    filename = f"flow_data/{address.replace(':', '_')}.feather"
    jsonfile = f"flow_data/{address.replace(':', '_')}_graph.json"

    if os.path.exists(filename) and not force:
        print(f"⏩ Skipping {address} (already processed)")
        return

    txs = []
    before = int(time.time() * 1000)
    retries = 0

    while True:
        url = f"{API_BASE}/addresses/{address}/full-transactions-page?limit=100&before={before}"
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

        for tx in data:
            if tx.get("block_time", 0) >= START_TIMESTAMP_MS:
                txs.append(tx)

        before = min(tx.get("block_time", before) for tx in data)
        time.sleep(0.25)

        if before < START_TIMESTAMP_MS:
            print("🛑 Reached start of allowed date range.")
            break

    print(f"📊 Retrieved {len(txs)} transactions after cutoff for {address}")
    os.makedirs("flow_data", exist_ok=True)

    edges = []
    rows = []

    for i, tx in enumerate(txs):
        txid = tx.get("transaction_id")
        timestamp = format_timestamp(tx.get("block_time"))
        print(f"🔎 [{i+1}/{len(txs)}] Processing tx: {txid}")

        sender = find_most_recent_sender(txid, depth=3)
        recipients = extract_final_recipients(tx)

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
        df.to_feather(filename)
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
    "kaspa:qz9cqmddjppjyth8rngevfs767m5nvm0480nlgs5ve8d6aegv4g9xzu2tgg0u"
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
