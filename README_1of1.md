# The Beaks — 1-of-1 Token ID Selection (Verifiable Fairness)

The Beaks collection contains 8 hand-painted **1-of-1 originals** by Dima
Kashtalyan, mixed into the 1,111 procedurally generated NFTs. The token
IDs that get the originals are chosen via a publicly verifiable
commit-reveal scheme.

**No one — including the team — can predict or manipulate which token
IDs become the 8 originals.**

## How it works

### Step 1: Commit (before reveal)

1. Generate a random 32-byte `salt`.
2. Compute `SHA-256(salt)` → public commitment hash.
3. Publish the commitment hash + the rule for picking the target block.
4. **Keep the salt private** until the target block is mined.

The commitment locks us in: we cannot change the salt later without
breaking the SHA-256 match.

### Step 2: Target block

Wait for the **first Ethereum mainnet block with timestamp at or after
2026-05-27 12:00 UTC**. Wait for **10 confirmations** to eliminate any
reorg risk.

The block's hash is unpredictable. No miner can target a specific
hash, and no one knows it before the block is produced.

### Step 3: Reveal

Once the target block is final:

1. Publish the salt.
2. Anyone verifies `SHA-256(salt) == commitment_hash`.
3. Run the algorithm:
   ```
   for counter in 0, 1, 2, ...:
     digest = SHA-256(salt || block_hash || counter[4-byte big-endian])
     idx = uint32(digest[:4]) mod 1111 + 1
     if idx not already picked: picked.append(idx)
     stop when 8 unique IDs collected
   ```
4. Outputs 8 token IDs in [1..1111]. The 8 originals get assigned to
   those IDs.

Anyone can re-run `reveal_1of1.py` and reproduce the **identical** 8 IDs.

## Files in this repo

- `1of1_commit.json` — public commitment (SHA-256, target block rule, algorithm).
- `_generate_salt.py` — script used to generate salt + commit. Not needed after commit.
- `reveal_1of1.py` — the reveal script (anyone can re-run).
- `1of1_reveal.json` — final proof (added after reveal): salt + block hash + 8 IDs.
- `1of1_salt.SECRET.txt` — **NOT in this repo until reveal**. Will be added after the target block is final.

## Verifying after reveal

```bash
# 1. clone this repo
git clone https://github.com/<your-org>/beaks-1of1
cd beaks-1of1

# 2. run the reveal script
python reveal_1of1.py

# 3. the script:
#    - verifies SHA-256(salt) matches commitment
#    - finds the target block on Ethereum
#    - derives 8 token IDs
#    - prints + saves them
#
# Compare with the published 1of1_reveal.json: must match exactly.
```

## Tradeoffs vs alternatives

| Approach | Verifiable? | Risk |
|---|---|---|
| Team picks 8 IDs themselves | ❌ No | "they cheated" |
| Use past block hash | ⚠ Partial | "they cherry-picked the block" |
| **Commit-reveal w/ future block** (this) | ✅ Full | None |

## Why we did this

The 1-of-1 originals are the rarest pieces in The Beaks. Whoever holds
those 8 token IDs has Dima's hand-painted works — pieces that took
20+ years of his pointillism practice to be possible. We wanted to
prove to collectors that the selection process was unmanipulated.
