import requests
import csv
import time
import os
from datetime import datetime

API_BASE = "https://api.kaspa.org"
CEX_ADDRESSES = {
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


visited = set()

def fetch_transactions(address, max_pages=20):
    txs = []
    before = int(time.time() * 1000)
    retries = 0

    for _ in range(max_pages):
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

        txs.extend(data)
        before = min(tx.get("block_time", before) for tx in data)
        time.sleep(0.25)
    print(f"✅ Total fetched: {len(txs)} transactions for {address}")
    return txs


def format_timestamp(ms_timestamp):
    try:
        return datetime.utcfromtimestamp(ms_timestamp / 1000).isoformat()
    except Exception:
        return ""

def trace_wallet(address, depth=2, output_dir="flow_data", force=False):
    # Resume: skip if file already exists
    if depth < 0 or address in visited:
        return

    filename = f"{output_dir}/{address.replace(':', '_')}.csv"
    if os.path.exists(filename) and not force:
        print(f"⏩ Skipping {address} (already processed)")
        visited.add(address)
        return

    visited.add(address)
    txs = fetch_transactions(address)
    os.makedirs(output_dir, exist_ok=True)

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["tx_id", "timestamp", "direction", "peer_address", "amount_sompi", "cex_label"])

        for tx in txs:
            txid = tx.get("transaction_id")
            timestamp = format_timestamp(tx.get("block_time"))
            inputs = tx.get("inputs") or []
            outputs = tx.get("outputs") or []

            for inp in inputs:
                if inp.get("previous_outpoint_address") == address:
                    for out in outputs:
                        to_addr = out.get("script_public_key_address")
                        amt = out.get("amount", 0)
                        if to_addr and to_addr != address:
                            label = CEX_ADDRESSES.get(to_addr, "")
                            writer.writerow([txid, timestamp, "sent", to_addr, amt, label])
                            if to_addr not in CEX_ADDRESSES:
                                trace_wallet(to_addr, depth - 1, output_dir)

            for out in outputs:
                if out.get("script_public_key_address") == address:
                    amt = out.get("amount", 0)
                    for inp in inputs:
                        from_addr = inp.get("previous_outpoint_address")
                        if from_addr and from_addr != address:
                            label = CEX_ADDRESSES.get(from_addr, "")
                            writer.writerow([txid, timestamp, "received", from_addr, amt, label])
                            if from_addr not in CEX_ADDRESSES:
                                trace_wallet(from_addr, depth - 1, output_dir)

if __name__ == "__main__":
    start_address = "kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5" # first Chainge Finance wallet
    #start_address = "kaspa:qq9zagcza4jt76eev9jl5z0nqhe0thcu7js8larktj4sle7lvgnw7sfcewlty" # received >57M Kas from first wallet
    trace_wallet(start_address, depth=2, force=True)
    print("✅ Recursive tracing complete. See results in 'flow_data/'")
