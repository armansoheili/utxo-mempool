# UTXO Mempool Simulator

A tiny, self-contained simulation of a Bitcoin-style UTXO ledger in pure Python
(no dependencies). It shows how a mempool validates pending transactions and how
a miner builds a fee-ordered block from them.

## What's inside

| File | Purpose |
|---|---|
| `utxo_mempool.py` | `UTXOSet` ledger, `Tx`, `Mempool` validator, `mine()` block builder |
| `example.py` | runnable demo: valid tx, rejected double-spend, rejected over-spend, mined block |

## How it works

- **UTXOSet** tracks unspent outputs as `(txid, vout) → (value, owner)`.
- **Mempool.add()** validates each transaction: inputs must exist and be
  unspent, outputs must be positive, the fee (inputs − outputs) must not be
  negative, and no input may already be claimed by another pending tx.
- **mine()** sorts the mempool by fee rate, takes the best `max_txs` txs,
  prepends a coinbase reward, applies the block to the ledger and clears the pool.

## Run it

```bash
python3 example.py
```

Expected output (txids vary):

```
genesis 3f2a91c4…  -> alice: 100

tx1 alice→bob   : True — accepted (fee 2)
tx2 double-spend: False — double spend of 3f2a91c4…
tx3 over-spend  : False — negative fee (outputs exceed inputs)

mined block with 2 txs (coinbase + 1), fees: 2
balances -> alice: 68  bob: 30  sam: 50
rejected txs left no trace on the ledger ✓
```

## Try it yourself

```python
from utxo_mempool import UTXOSet, Tx, Mempool, mine

ledger, mempool = UTXOSet(), None
gen = ledger.add_genesis(100, "alice")
mempool = Mempool(ledger)

# send 25 to bob, keep the rest (fee 1)
tx = Tx([(gen.txid, 0)], [(25, "bob"), (74, "alice")])
print(mempool.add(tx))

block, fees = mine(mempool, miner="sam", reward=50)
print("alice:", ledger.balance("alice"), "bob:", ledger.balance("bob"))
```

MIT licensed — play with it, break it, learn how UTXOs really work.
