"""
Demo: genesis -> 3 txs (one double-spend, one over-spend) -> mine a block.
Run: python3 example.py
"""

from utxo_mempool import UTXOSet, Tx, Mempool, mine

ledger = UTXOSet()
mempool = Mempool(ledger)

# Genesis: 100 coins to alice
gen = ledger.add_genesis(100, "alice")
print(f"genesis {gen.txid[:8]}…  -> alice: {ledger.balance('alice')}\n")

ref = (gen.txid, 0)

# 1) valid: alice -> bob (30), change back to alice (68), fee = 2
tx1 = Tx([ref], [(30, "bob"), (68, "alice")])
ok, why = mempool.add(tx1)
print(f"tx1 alice→bob   : {ok} — {why}")

# 2) double-spend of the same input: rejected
tx2 = Tx([ref], [(90, "carol")])
ok, why = mempool.add(tx2)
print(f"tx2 double-spend: {ok} — {why}")

# 3) outputs exceed inputs (negative fee): rejected
tx3 = Tx([ref], [(150, "dave")])
ok, why = mempool.add(tx3)
print(f"tx3 over-spend  : {ok} — {why}")

# Mine a block (reward 50 to miner sam)
block, fees = mine(mempool, "sam", reward=50, max_txs=10)
print(f"\nmined block with {len(block.txs)} txs (coinbase + {len(block.txs)-1}), fees: {fees}")
print(f"balances -> alice: {ledger.balance('alice')}  bob: {ledger.balance('bob')}  sam: {ledger.balance('sam')}")

# tx2/tx3 never made it into the chain
assert ledger.balance('carol') == 0 and ledger.balance('dave') == 0
print("rejected txs left no trace on the ledger ✓")
