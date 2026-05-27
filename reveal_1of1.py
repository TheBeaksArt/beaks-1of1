"""
The Beaks — 1-of-1 token ID reveal.

Run this on or after 2026-05-27 12:00 UTC.

What it does:
  1. Reads the secret salt from 1of1_salt.SECRET.txt
  2. Verifies salt's SHA-256 matches the public commitment (1of1_commit.json)
  3. Queries Ethereum mainnet for first block with timestamp >= 2026-05-27 12:00 UTC
  4. Waits for 10 confirmations (block to be at least 10 blocks behind current head)
  5. Computes 8 token IDs deterministically:
         sha256(salt || block_hash || counter[4 bytes BE]) -> uint32 mod 1111 + 1
         skip duplicates, iterate until 8 unique IDs collected
  6. Outputs the 8 IDs and saves 1of1_reveal.json (the proof)

ANYONE can re-run this script with the same salt and target block
and get the IDENTICAL 8 token IDs. That's the proof of fairness.
"""
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

try: sys.stdout.reconfigure(encoding="utf-8")
except: pass

# ─── Constants ─────────────────────────────────────────────────────────
TOTAL = 1111
PICK = 8
TARGET_UNIX = 1779963600  # 2026-05-27T12:00:00Z = first ETH block at/after this
CONFIRMATIONS = 10
RPC = "https://ethereum-rpc.publicnode.com"

def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode()
    req = urllib.request.Request(
        RPC, data=body,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    return json.loads(urllib.request.urlopen(req).read())["result"]

# ─── Step 1: read salt + verify commitment ─────────────────────────────
salt_path = Path("1of1_salt.SECRET.txt")
commit_path = Path("1of1_commit.json")
if not salt_path.exists() or not commit_path.exists():
    print(f"ERR: need {salt_path} and {commit_path} in cwd"); sys.exit(1)

salt_hex = ""
for line in salt_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and not line.startswith("SALT") and not line.startswith("COMMIT") and all(c in "0123456789abcdef" for c in line.lower()):
        if len(line) == 64:
            salt_hex = line.lower()
            break
if not salt_hex:
    print("ERR: could not parse salt hex from secret file"); sys.exit(1)

salt_bytes = bytes.fromhex(salt_hex)
computed_hash = hashlib.sha256(salt_bytes).hexdigest()

commit = json.loads(commit_path.read_text(encoding="utf-8"))
expected_hash = commit["commitment_sha256"]

print("=" * 70)
print("STEP 1: VERIFY SALT MATCHES COMMITMENT")
print("=" * 70)
print(f"  Expected (public commit):  {expected_hash}")
print(f"  Computed sha256(salt):     {computed_hash}")
if computed_hash != expected_hash:
    print("  ✗ MISMATCH — salt has been tampered with. ABORT.")
    sys.exit(2)
print("  ✓ MATCH — salt is the one originally committed\n")

# ─── Step 2: find target block ─────────────────────────────────────────
print("=" * 70)
print(f"STEP 2: FIND TARGET BLOCK (first with timestamp >= {TARGET_UNIX})")
print("=" * 70)

latest_hex = rpc("eth_blockNumber", [])
latest = int(latest_hex, 16)
print(f"  Current latest block:      {latest}")

# Binary search for first block with timestamp >= TARGET_UNIX
# Earliest possible: latest - 5000 (covers ~17 hours of history at 12s/block)
lo, hi = max(1, latest - 5000), latest
target_block = None
while lo < hi:
    mid = (lo + hi) // 2
    b = rpc("eth_getBlockByNumber", [hex(mid), False])
    ts = int(b["timestamp"], 16)
    if ts >= TARGET_UNIX:
        hi = mid
    else:
        lo = mid + 1

target_block_num = lo
b = rpc("eth_getBlockByNumber", [hex(target_block_num), False])
target_ts = int(b["timestamp"], 16)
target_hash = b["hash"]

if target_ts < TARGET_UNIX:
    print(f"  ⏳ Target time not reached yet. Latest block timestamp: {target_ts}")
    print(f"     Need: timestamp >= {TARGET_UNIX} ({TARGET_UNIX - target_ts}s remaining)")
    sys.exit(3)

# Check confirmations
confirmations = latest - target_block_num
print(f"  Target block:              #{target_block_num}")
print(f"  Target timestamp:          {target_ts}")
print(f"  Block hash:                {target_hash}")
print(f"  Confirmations so far:      {confirmations}")
if confirmations < CONFIRMATIONS:
    need = CONFIRMATIONS - confirmations
    print(f"  ⏳ Need {need} more confirmations. Wait ~{need*12}s and re-run.")
    sys.exit(4)
print(f"  ✓ {CONFIRMATIONS}+ confirmations achieved — block is final.\n")

# ─── Step 3: derive 8 token IDs deterministically ─────────────────────
print("=" * 70)
print("STEP 3: DERIVE 8 TOKEN IDS")
print("=" * 70)
print(f"  Algorithm: sha256(salt || block_hash || counter[4 bytes BE])")
print(f"             -> uint32 mod {TOTAL} + 1, skip duplicates\n")

block_hash_bytes = bytes.fromhex(target_hash[2:])  # strip 0x
picked = []
counter = 0
while len(picked) < PICK:
    h = hashlib.sha256(salt_bytes + block_hash_bytes + counter.to_bytes(4, "big")).digest()
    idx = int.from_bytes(h[:4], "big") % TOTAL + 1
    if idx not in picked:
        picked.append(idx)
    counter += 1

print(f"  Selected 8 token IDs (in draw order):")
for i, pid in enumerate(picked, 1):
    print(f"    {i}. #{pid:04d}")

picked_sorted = sorted(picked)
print(f"\n  Sorted: {picked_sorted}")

# ─── Save the proof ───────────────────────────────────────────────────
proof = {
    "project": commit["project"],
    "total_supply": TOTAL,
    "n_picked": PICK,
    "commitment_sha256": expected_hash,
    "salt_hex_revealed": salt_hex,
    "target_block_rule": commit["target_block_rule"],
    "target_block_number": target_block_num,
    "target_block_hash": target_hash,
    "target_block_timestamp": target_ts,
    "confirmations_at_reveal": confirmations,
    "selected_token_ids_in_draw_order": picked,
    "selected_token_ids_sorted": picked_sorted,
    "algorithm": commit["algorithm"],
    "etherscan_verify": f"https://etherscan.io/block/{target_block_num}",
}
out = Path("1of1_reveal.json")
out.write_text(json.dumps(proof, indent=2), encoding="utf-8")
print(f"\n  ✓ Saved proof: {out.absolute()}")
print(f"\n  Anyone can verify by re-running this script with the same files.")
