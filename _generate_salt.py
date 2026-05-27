"""Generate salt + commitment hash for 1-of-1 selection.

Outputs:
  - 1of1_salt.SECRET.txt          (the salt — KEEP PRIVATE until reveal)
  - 1of1_commit.json              (the public commitment — tweet/post this)
"""
import secrets
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try: sys.stdout.reconfigure(encoding="utf-8")
except: pass

# 32 random bytes (256 bits) — uniformly random from /dev/urandom equivalent
salt_bytes = secrets.token_bytes(32)
salt_hex = salt_bytes.hex()

# SHA-256 commitment hash
commit_hash = hashlib.sha256(salt_bytes).hexdigest()

now_utc = datetime.now(timezone.utc).isoformat()

# Save SECRET salt locally (do NOT publish until reveal time)
secret_path = Path("1of1_salt.SECRET.txt")
secret_path.write_text(
    f"# PRIVATE - DO NOT SHARE UNTIL REVEAL TIME ({now_utc})\n"
    f"# Reveal time: 2026-05-27 ~12:00 UTC (after target Ethereum block mined)\n\n"
    f"SALT (hex, 32 bytes):\n{salt_hex}\n\n"
    f"COMMITMENT HASH (sha256 of salt):\n{commit_hash}\n",
    encoding="utf-8",
)

# Save public commitment (this is what we tweet / put on GitHub)
public = {
    "project": "The Beaks — 1-of-1 token ID selection",
    "total_supply": 1111,
    "n_to_pick": 8,
    "committed_at_utc": now_utc,
    "commitment_sha256": commit_hash,
    "target_block_rule": "First Ethereum mainnet block with timestamp >= 2026-05-27T12:00:00Z, with 10+ confirmations.",
    "algorithm": "sha256(salt_bytes || block_hash_bytes || counter[4 bytes BE]) -> uint32 -> mod 1111 + 1; skip duplicates; iterate until 8 unique IDs collected.",
    "reveal_plan": "At/after target block + 10 confirmations: publish salt; anyone can verify sha256(salt) == commitment_sha256; anyone can re-run the algorithm and reproduce the same 8 IDs.",
    "reveal_repo": "https://github.com/<your-org>/beaks-1of1   (push the script + this file)",
}
commit_path = Path("1of1_commit.json")
commit_path.write_text(json.dumps(public, indent=2), encoding="utf-8")

print("=" * 60)
print("STEP 1 COMPLETE — SALT + COMMITMENT GENERATED")
print("=" * 60)
print(f"\n  Commitment SHA-256 (PUBLIC — safe to share):")
print(f"  {commit_hash}\n")
print(f"  Salt: PRIVATE — saved at {secret_path.absolute()}")
print(f"        DO NOT open / share / copy until reveal time")
print(f"\n  Public commitment JSON: {commit_path.absolute()}")
print(f"\n  Committed at: {now_utc}")
print(f"  Target block: first Ethereum block with timestamp ≥ 2026-05-27 12:00 UTC")
print(f"                + wait 10 confirmations (~2 min after that block)")
