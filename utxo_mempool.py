"""
UTXO ledger + mempool simulator (Bitcoin-style, pure Python).

Models the core mechanics of a UTXO chain in ~150 lines:
  - UTXOSet   : the ledger; tracks unspent outputs, applies blocks
  - Tx        : a transaction with inputs, outputs and an implicit fee
  - Mempool   : validates and holds pending transactions
  - mine()    : builds a fee-rate-ordered block template from the mempool

No dependencies, no network. Just run:  python3 example.py
"""

import hashlib
import itertools
from dataclasses import dataclass, field


# ---------------------------------------------------------------- helpers
def txid_of(tx) -> str:
    blob = repr((tx.inputs, tx.outputs)).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


# ---------------------------------------------------------------- data
@dataclass
class Tx:
    """A transaction. fee is implicit: sum(inputs) - sum(outputs)."""
    inputs: list   # [(txid, vout), ...]
    outputs: list  # [(value, owner), ...]
    txid: str = field(init=False)

    def __post_init__(self):
        self.txid = txid_of(self)


@dataclass
class Block:
    txs: list  # [Tx, ...]  (index 0 is the coinbase paying miner_reward to miner)


# ---------------------------------------------------------------- ledger
class UTXOSet:
    """The ledger: {(txid, vout): (value, owner)}"""

    def __init__(self):
        self.utxos = {}

    def add_genesis(self, value, owner):
        genesis = Tx([], [(value, owner)])
        self.utxos[(genesis.txid, 0)] = (value, owner)
        return genesis

    def balance(self, owner) -> int:
        return sum(v for (v, o) in self.utxos.values() if o == owner)

    def apply_block(self, block):
        for tx in block.txs:
            for ref in tx.inputs:
                if ref not in self.utxos:
                    raise ValueError(f"missing input {ref}")
                del self.utxos[ref]
            for i, (value, owner) in enumerate(tx.outputs):
                self.utxos[(tx.txid, i)] = (value, owner)


# ---------------------------------------------------------------- mempool
class Mempool:
    """Holds pending txs; rejects invalid and double-spending ones."""

    def __init__(self, ledger: UTXOSet):
        self.ledger = ledger
        self.txs = {}       # txid -> (Tx, fee)
        self.spent = set()  # inputs already claimed by a pending tx

    def _fee(self, tx) -> int:
        in_val = sum(self.ledger.utxos[r][0] for r in tx.inputs)
        out_val = sum(v for v, _ in tx.outputs)
        return in_val - out_val

    def add(self, tx: Tx):
        if tx.txid in self.txs:
            return False, "already in mempool"
        if not tx.outputs or any(v <= 0 for v, _ in tx.outputs):
            return False, "bad outputs"
        for ref in tx.inputs:
            if ref not in self.ledger.utxos:
                return False, f"unknown input {ref[0][:8]}…"
            if ref in self.spent:
                return False, f"double spend of {ref[0][:8]}…"
        fee = self._fee(tx)
        if fee < 0:
            return False, "negative fee (outputs exceed inputs)"
        for ref in tx.inputs:
            self.spent.add(ref)
        self.txs[tx.txid] = (tx, fee)
        return True, f"accepted (fee {fee})"


# ---------------------------------------------------------------- mining
def mine(mempool: Mempool, miner, reward, max_txs=10) -> Block:
    """Pick the highest fee-rate txs, build + apply a block.

    Transactions that don't fit in this block stay in the mempool and are
    reconsidered for the next one — only mined txs leave the mempool.
    """
    ordered = sorted(mempool.txs.values(),
                     key=lambda t: t[1] / max(1, len(repr(t[0]))),
                     reverse=True)[:max_txs]
    coinbase = Tx([], [(reward, miner)])
    block = Block([coinbase] + [t for t, _ in ordered])
    mempool.ledger.apply_block(block)
    total_fees = sum(f for _, f in ordered)
    for t, _ in ordered:
        del mempool.txs[t.txid]
        for ref in t.inputs:
            mempool.spent.discard(ref)
    return block, total_fees
