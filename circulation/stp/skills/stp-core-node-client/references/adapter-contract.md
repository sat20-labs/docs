# STP Adapter Contract

An STP adapter is any executable or callable service that maps JSON requests to STP protocol actions.

For end-user wallets, the recommended adapter is the SAT20 PWA Wallet. The PWA loads the wallet/STP WASM engines, keeps private keys inside the wallet, asks the user to approve value-moving actions, and exposes only the JSON adapter contract to the Agent.

## Invocation

Preferred CLI form:

```bash
$STP_CLIENT_CMD '{"op":"stp.status","chain":"testnet"}'
```

The adapter must return JSON on stdout and use non-zero exit only for transport or process failures. Protocol failures should return JSON with `ok:false`.

Bundled adapter scripts:

| Script | Use case |
| --- | --- |
| `scripts/stp_adapter.py` | Generic dispatcher from an Agent to `STP_ADAPTER_URL` or `STP_CLIENT_CMD` |
| `scripts/stp_workspace_wallet_adapter.py` | SAT20 workspace testnet wallet bootstrap/status/send/tx adapter |
| `scripts/stp_transcend_rpc_adapter.py` | Development adapter for an already running local STP-compatible node |

Development adapters map this standard contract to implementation-specific local APIs. Agent should depend on this contract, not on those local API paths.

## Common Response

```json
{
  "ok": true,
  "chain": "testnet",
  "operation": "stp.unlock",
  "channel_id": "tb1q...",
  "transaction_id": "stp-tx-001",
  "tx_ids": ["..."],
  "status": "BROADCASTED",
  "next_check": "poll stp.transaction"
}
```

Failure response:

```json
{
  "ok": false,
  "chain": "testnet",
  "operation": "stp.lock",
  "error": {
    "code": "INSUFFICIENT_CHANNEL_CAPACITY",
    "message": "channel capacity is lower than requested amount"
  },
  "recommended_op": "stp.lock_with_expand"
}
```

Authorization-required response:

```json
{
  "ok": false,
  "chain": "testnet",
  "operation": "stp.splicing_out",
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Approve this STP operation in SAT20 PWA Wallet."
  },
  "approval": {
    "wallet": "sat20-pwa",
    "request_id": "pwa-approval-001",
    "expires_at": 1760000000
  }
}
```

Agent must not bypass wallet authorization. After wallet approval, the adapter may either complete the operation and return a transaction response, or allow Agent to retry the original request with the same user-approved intent.

Adapters should prefer the nested `error.code` / `error.message` form. Legacy adapters may return flat `error_code` / `message`; Agent should normalize both shapes before deciding the next step.

## Required Evidence In Successful Responses

For value-moving operations, `ok:true` is not enough. The adapter must return enough evidence for an Agent to continue polling and to explain why the user's assets remain safe.

At minimum, successful value-moving responses should include:

| Field | Requirement |
| --- | --- |
| `operation` | The normalized operation name that was executed |
| `chain` | The chain actually used by the adapter |
| `channel_id` | Required for all `stp.*` channel operations |
| `transaction_id` or `reservation_id` | A stable handle for polling `stp.transaction` or `wallet.transaction` |
| `tx_ids` | All known BTC L1 and SatoshiNet txids produced by the operation |
| `layer_tx_ids` | Optional structured split such as `btc_l1`, `satoshinet`, `commitment`, `punish` |
| `status` | Normalized status such as `BROADCASTED`, `READY`, `READY_DEGRADED`, `CONFIRMED`, or `FAILED` |
| `next_check` | The next polling operation or wait condition |
| `safety` | A short safety summary, or a pointer telling Agent to call `stp.safety_snapshot` immediately |

When a response moves channel state forward, it should also include the previous and new `commit_height` if known. If the operation created or updated a commitment transaction, it should include commitment txids or return `next_check:"stp.safety_snapshot"`.

For `stp.safety_snapshot`, `stp.commitment_export`, `stp.punish_status`, `stp.force_close_plan`, and `stp.sweep_build`, the response must be directly verifiable and should not require Agent to infer safety from wallet balances alone.

For safety-blocking missing data, adapters should return explicit evidence errors instead of a generic failure. Recommended codes:

| Code | Meaning |
| --- | --- |
| `MISSING_L1_TX_STATUS` | The adapter cannot prove visibility, confirmation, or spent status for a required BTC L1 tx/outpoint |
| `MISSING_L2_UTXO_STATUS` | The adapter cannot prove whether the relevant SatoshiNet UTXO is pending or spendable |
| `MISSING_COMMITMENT_EXPORT` | The adapter cannot return the commitment transaction or enough structured data to verify it |
| `MISSING_PUNISH_COVERAGE` | A revoked remote commitment exists but verified punish material is unavailable |
| `MISSING_RESERVATION_STATE` | The adapter cannot determine whether a related STP transaction is still pending |
| `MISSING_PEER_CHANNEL_STATE` | Peer/core-node channel state is needed for recovery but cannot be queried |

Agent must treat these as read-only stop conditions for value-moving operations. The next action should be to request the missing evidence, not to retry the asset operation.

When the peer/core node returns an unexpected internal failure, adapters should normalize it to a user-actionable error:

```json
{
  "ok": false,
  "error": {
    "code": "CORE_NODE_UNAVAILABLE",
    "message": "The core node could not complete this operation. No retry should be attempted until channel and transaction evidence are checked."
  }
}
```

Agent must not blindly retry the same value-moving operation after this error. It should query the channel safety snapshot, reservation/transaction status, and related L1/L2 tx visibility before deciding whether the user can safely retry or must wait.

## Required Operations

The adapter contract is split into two namespaces:

- `wallet.*` covers wallet lifecycle, mnemonic handling, password changes, direct asset sends, and ordinary wallet transaction tracking.
- `stp.*` covers STP channel lifecycle and asset movement through channels.

Production adapters should implement both namespaces through the same wallet authorization boundary.

### `wallet.create`

Input:

```json
{"op":"wallet.create","chain":"testnet","purpose":"agent-stp-testnet-wallet"}
```

Creates a new wallet inside the configured wallet adapter.

For SAT20 PWA Wallet, this must create the wallet inside the PWA authorization boundary. For local development, a workspace adapter may return a testnet mnemonic that can be imported into PWA.

Mainnet wallet creation must require explicit user approval in the wallet UI.

Response:

```json
{
  "ok": true,
  "operation": "wallet.create",
  "chain": "testnet",
  "wallet_type": "sat20-pwa-compatible",
  "mnemonic": "twelve words...",
  "wallet_id": 1760000000000000,
  "l1_address": "tb1p...",
  "satsnet_address": "tb1p...",
  "payment_pubkey": "02...",
  "next_step": "Import this mnemonic into SAT20 PWA Wallet, then connect the PWA STP adapter."
}
```

### `wallet.import`

Input:

```json
{"op":"wallet.import","chain":"testnet","mnemonic":"twelve words..."}
```

Imports a mnemonic into the configured wallet adapter. Production adapters should not echo the mnemonic back in the response.

### `wallet.export_mnemonic`

Input:

```json
{"op":"wallet.export_mnemonic","chain":"testnet","wallet_id":1760000000000000}
```

Exports the active wallet mnemonic only after wallet-side authorization.

For SAT20 PWA Wallet, password entry and reveal confirmation should happen inside the PWA UI. Agent should not ask the user to type the wallet password into chat. The adapter may return `AUTH_REQUIRED` first, then return the mnemonic after the user approves in the wallet UI.

Response:

```json
{
  "ok": true,
  "operation": "wallet.export_mnemonic",
  "chain": "testnet",
  "wallet_id": 1760000000000000,
  "mnemonic": "twelve words...",
  "warning": "Store this mnemonic offline. Anyone with it can control the wallet."
}
```

### `wallet.change_password`

Input:

```json
{"op":"wallet.change_password","chain":"testnet","wallet_id":1760000000000000}
```

Changes the wallet password inside the wallet authorization boundary.

For PWA adapters, old and new passwords should be entered in the PWA UI, not passed through Agent JSON. CLI adapters may open an interactive local prompt or return `AUTH_REQUIRED` with instructions.

### `wallet.status`

Input:

```json
{"op":"wallet.status","chain":"testnet"}
```

Returns wallet readiness, active account, L1 address, SatoshiNet address, and whether STP WASM is initialized.

### `wallet.send_assets`

Input fields:

- `chain`
- `layer`: `btc_l1` or `satoshinet`
- `asset`
- `amount`
- `to`
- optional `fee_rate`
- optional `utxos`
- optional `memo`

For plain sats, the low-level SAT20/STP asset string is `::`. Adapters should accept user-friendly aliases such as `sat`, `sats`, `plain`, or `plain:sat` and normalize them to `::`.

Example:

```json
{
  "op": "wallet.send_assets",
  "chain": "testnet",
  "layer": "satoshinet",
  "asset": "sats",
  "amount": "1000",
  "to": "tb1p...",
  "fee_rate": 1
}
```

This operation sends assets directly from the user's wallet address. It does not open, close, expand, lock, unlock, or otherwise change an STP channel. If the asset is in a channel, use `stp.unlock`, `stp.splicing_out`, or another channel operation first.

### `wallet.transaction`

Input:

```json
{"op":"wallet.transaction","chain":"testnet","transaction_id":"wallet-tx-001"}
```

Returns direct wallet transaction status, tx IDs, error state, and next polling interval.

### `stp.status`

Input:

```json
{"op":"stp.status","chain":"testnet"}
```

Must return wallet readiness, server readiness, chain, known channels, channel status, and commit height.

### `stp.open`

Input fields:

- `chain`
- `server`
- `amount_sats`
- `fee_rate`
- optional `utxos`
- optional `memo`

Preconditions:

- `server` must identify a reachable core node for ordinary client wallets.
- Ordinary client wallets do not need any stake asset to open a channel with a core node.
- Stake asset checks apply only when connecting to a bootstrap node to become a core node. If an ordinary open returns a stake-asset error, recheck whether the adapter selected a bootstrap node by mistake.

### `stp.reopen`

Input fields:

- `chain`
- optional `channel_id`

Reopens a channel when there is no active local channel but the deterministic channel address still belongs to an earlier client-core channel. This is a recovery path for cases such as force-close recovery, stale local channel data, or a completed L1 transition that left the local channel inactive.

The current transcend RPC endpoint maps this operation to `ReopenChannel(true)`, so it may also try to expand all assets found at the channel address after the reopened channel becomes ready.

Preconditions:

- Wallet is unlocked and connected to the intended core node.
- No active channel already exists.
- SatoshiNet channel ledger proves that the channel address has previous channel history, or the user explicitly intends to create a fresh channel.
- If the channel address has an eligible plain-sat UTXO that satisfies the minimum capacity, the adapter may use it as the new channel point.
- If no eligible channel-address UTXO satisfies the minimum capacity, the adapter may create a new BTC L1 funding transaction from the user's wallet through the reopen flow, then wait for confirmation.
- The channel address does not contain a contract-managed state that forbids reopen.

While the new funding transaction is visible but unconfirmed, `stp.safety_snapshot` may return `READY_DEGRADED`. Agent must treat that as read-only and wait until the channel becomes `READY_SAFE` before ordinary value-moving operations.

### `stp.rebuild`

Input fields:

- `chain`
- optional `channel_id`
- optional `utxo` or `funding_utxo`

Rebuilds a channel from an L1 channel-address funding UTXO without creating a new SatoshiNet opening anchor. Use this when the L1 channel point changed but the corresponding plain sats were already anchored on SatoshiNet by an earlier opening anchor. This avoids duplicating SatoshiNet supply.

If `utxo` is provided, the adapter must use that exact L1 outpoint and verify that it is a pure plain-sat UTXO locked to the deterministic channel address. If omitted, the adapter may select an eligible plain-sat UTXO from the channel address.

The adapter must prove that the selected UTXO is safe for no-anchor rebuild before it calls the protocol flow. Preferred proof comes from the SatoshiNet channel ledger, which records ascending entries and descending v2 returned-channel outputs. Old descending data still records the L1 txid, but not the returned vouts; accept a candidate only when its txid matches the legacy descending `L1TxId` and the candidate vout is locked to the channel address.

The adapter must reject ambiguous candidates instead of creating a new opening anchor. If fresh L1 assets need a new anchor, use `stp.reopen` or an ordinary open/expand path instead of `stp.rebuild`.

After a successful rebuild, Agent must run `stp.safety_snapshot`. If additional protocol assets such as Runes, BRC-20, or ORDX are still visible at the L1 channel address, Agent should bring them under channel control with `stp.expand` or `stp.expand_all`.

### `stp.restore`

Input fields:

- `chain`
- `channel_id`

Restores channel state from a saved channel backup or peer-supported restore path. Use only when ordinary status cannot find the active channel, or when safety checks show local state is missing but peer/channel backup data is available.

### `stp.clean_channel`

Input fields:

- `chain`
- `channel_id`

Deletes stale local channel state from one adapter endpoint. Use this only after L1/L2 evidence proves that the old channel is closed, punished, or no longer safely recoverable, and only when the stale record blocks a fresh open or a documented recovery flow. The adapter must not treat this as a normal close operation and must not hide unresolved safety mismatches.

When a client wallet and a core node both retain stale state, run `stp.clean_channel` against each side's own management endpoint. A transcend core node typically exposes public protocol RPC on `rpc.host` and local management RPC on `127.0.0.1:(rpc.host + 1)`, so management paths such as `/clean/channel` may not be available through the public `/stp/testnet` reverse proxy.

After cleaning stale state, use ordinary `stp.open` as a fresh client-core channel, wait until it is `READY_SAFE`, then run `stp.expand` or `stp.expand_all` for assets already controlled by the channel address.

### `stp.expand`

Input fields:

- `chain`
- `channel_id`
- `asset`
- `utxos`: one BTC L1 UTXO for L1 expand, or one or more SatoshiNet UTXOs when `network:"satsnet"`
- optional `network`: set to `satsnet` for SatoshiNet-side expand; omit or leave empty for BTC L1 expand
- optional `reason`

Adds an asset UTXO that is already controlled by the channel address into the channel commitment state. This is the correct operation when an asset has reached the channel address on BTC L1 or SatoshiNet but is not yet represented in the channel's latest commitment allocation.

### `stp.expand_all`

Input fields:

- `chain`
- `channel_id`
- optional `asset`
- optional `network`

Attempts to expand all eligible assets at the channel address, or one asset when `asset` is supplied. Use after reopen or after detecting unmanaged channel-address assets.

### `stp.unlock`

Input fields:

- `chain`
- `channel_id`
- `asset`
- `amount`
- `to`
- optional `fee_rate`

Agent-facing adapters must not expose asset-input or fee-input parameters for `stp.unlock`. The wallet/STP adapter selects channel inputs and SatoshiNet fee inputs internally. If no safe input set can be constructed, return an explicit error such as `INSUFFICIENT_SPENDABLE_BALANCE` or `MISSING_L2_UTXO_STATUS`.

### `stp.lock`

Input fields:

- `chain`
- `channel_id`
- `asset`
- `amount`

If capacity is insufficient, return `ok:false` with `error.code:"INSUFFICIENT_CHANNEL_CAPACITY"` and `recommended_op:"stp.lock_with_expand"`. Legacy adapters may use `error_code`.

Agent-facing adapters must not expose asset-input or fee-input parameters for `stp.lock`. The adapter selects SatoshiNet personal-address asset inputs and fee inputs internally.

### `stp.lock_with_expand`

Input fields:

- `chain`
- `channel_id`
- `asset`
- `amount`
- optional `fee_rate`

This operation restores SatoshiNet personal-address assets to channel control when direct lock capacity is insufficient.

Wallet adapters should expose this operation even when they also expose ordinary `stp.lock`. It is the control-right recovery path that lets the user regain channel protection without manually exiting through BTC L1 and reopening the channel.

### `stp.splicing_in`

Input fields:

- `chain`
- `channel_id`
- `asset`
- `amount`
- optional `fee_rate`

Agent-facing adapters must not expose asset-input or fee-input selection for `stp.splicing_in`. The request describes intent only: asset, amount, channel, chain, and optional fee policy. The adapter selects suitable L1 asset inputs and BTC fee inputs internally.

For BRC20, the adapter should automatically choose an existing suitable transfer output when one is available. If no suitable transfer output exists, the adapter should create a fresh BRC20 transfer inscription and use its reveal output for splicing-in.

If the adapter cannot construct the required transfer inscription or fee inputs, it must return a clear error such as `INSUFFICIENT_L1_FEE_BALANCE`, `BRC20_TRANSFER_BUILD_FAILED`, or `MISSING_L1_TX_STATUS`. Agent should not retry by manually supplying inputs.

### `stp.splicing_out`

Input fields:

- `chain`
- `channel_id`
- `asset`
- `amount`
- `to_l1_address`
- optional `fee_rate`

Agent-facing adapters must not expose asset-input or fee-input parameters for `stp.splicing_out`. For BRC20, the adapter should choose a suitable channel-address transfer output or create a fresh transfer inscription when needed. For all assets, the adapter selects BTC fee inputs internally and returns a clear funding/error state if it cannot do so safely.

### `stp.close`

Input fields:

- `chain`
- `channel_id`
- `mode`: `cooperative` or `force`
- optional `fee_rate`

### `stp.transaction`

Input:

```json
{
  "op": "stp.transaction",
  "chain": "testnet",
  "transaction_id": "stp-tx-001",
  "reservation_id": "1780719720785232",
  "tx_ids": ["..."],
  "layer": "btc_l1"
}
```

Must return current protocol status, linked BTC L1 tx IDs, linked SatoshiNet tx IDs, error state, and recommended next check.

Adapters should accept either a protocol `transaction_id`, a `reservation_id`, explicit `tx_ids`, or a combination of them. When `tx_ids` are supplied, the adapter should query the relevant indexer and return visibility, confirmation count, block height, and next polling guidance. When only `reservation_id` is supplied, the adapter should at least return the local reservation details and terminal/pending status.

### `stp.safety_snapshot`

Input:

```json
{"op":"stp.safety_snapshot","chain":"testnet","channel_id":"tb1q..."}
```

Returns an Agent-readable safety summary for one channel:

```json
{
  "ok": true,
  "operation": "stp.safety_snapshot",
  "result": {
    "channel_id": "tb1q...",
    "chan_point": "txid:0",
    "status": "READY_SAFE",
    "raw_status": 16,
    "commit_height": 12,
    "csv_delay": 1000,
    "local_commitment_present": true,
    "remote_commitment_present": true,
    "local_balance": [],
    "remote_balance": [],
    "l2_spendable_balance": {
      "::": "10000",
      "brc20:f:sgas": "100"
    },
    "l2_pending_balance": {
      "ordx:f:dogcoin": "100"
    },
    "l2_spendable_utxo_count": 2,
    "l2_pending_utxo_count": 1,
    "punish_coverage": {
      "covered_revoked_commitments": 12,
      "missing": []
    }
  }
}
```

Agent must run this operation before value-moving channel operations. If the adapter cannot prove local commitment availability and punish coverage, it must return `SAFETY_SNAPSHOT_REQUIRED` or `PUNISH_COVERAGE_MISSING`. If the adapter returns `READY_DEGRADED`, Agent may continue read-only tracking but must not run unlock, lock, splicing, close, or punish drill.

For unlock and lock planning, `local_balance` / `remote_balance` describe the current commitment asset allocation, while `l2_spendable_balance` and `l2_pending_balance` describe whether the SatoshiNet UTXOs backing a recent ascend are already spendable. A recently spliced-in asset may appear in the commitment summary while its anchor output is still pending. Adapters should expose both views so an Agent does not retry or unlock too early.

### `stp.commitment_export`

Input:

```json
{"op":"stp.commitment_export","chain":"testnet","channel_id":"tb1q..."}
```

Exports current commitment transactions and read-only validation material. It must not export mnemonic, private keys, or raw revocation secrets.

### `stp.punish_status`

Input:

```json
{"op":"stp.punish_status","chain":"testnet","channel_id":"tb1q..."}
```

Lists revoked remote commitments that have locally stored or constructible punish transactions.

### `stp.punish_build`

Input:

```json
{
  "op": "stp.punish_build",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "commit_txid": "...",
  "broadcast": false
}
```

Builds and verifies the punish transaction for a revoked remote commitment. With `broadcast:false`, this is a dry-run safety proof. With `broadcast:true`, the adapter may broadcast directly.

### `stp.punish_broadcast`

Input:

```json
{"op":"stp.punish_broadcast","chain":"testnet","channel_id":"tb1q...","commit_txid":"..."}
```

Broadcasts the verified punish transaction. This is a protective action and should take priority over ordinary channel operations when a revoked commitment is seen on BTC L1.

### `stp.force_close_plan`

Input:

```json
{"op":"stp.force_close_plan","chain":"testnet","channel_id":"tb1q..."}
```

Returns the local commitment transaction, expected CSV delay, earliest sweep condition, and user-controlled destination path.

### `stp.sweep_build`

Input:

```json
{"op":"stp.sweep_build","chain":"testnet","channel_id":"tb1q...","commit_txid":"...","height":0,"broadcast":false}
```

Builds or broadcasts the sweep transaction after force-close CSV delay expires.

Adapters must not implement `stp.sweep_build` by calling a helper that broadcasts as a side effect. The adapter must expose separate build, sign, verify, and broadcast phases so Agent can dry-run safety checks before any transaction is sent. With `broadcast:false`, the adapter returns signed and verified transaction hex without broadcasting. With `broadcast:true`, the wallet must treat the operation as a protective value-moving action and require wallet-side authorization before broadcasting.

Expected response fields include:

- `channel_id`
- `commit_txid`
- `sweep_txid`
- `tx_ids`
- `tx_hex`
- `fee`
- `height`
- `csv_delay`
- `signed`
- `verified`
- `broadcastable`
- `broadcasted`

## Testnet Fault Injection Operations

These operations are for testnet safety drills only. A core node must reject them unless the active network is testnet, and production/mainnet configuration must not allow them to execute.

### `stp.test_retain_server_commitment`

Input:

```json
{
  "op": "stp.test_retain_server_commitment",
  "chain": "testnet",
  "server": "https://apiprd.ordx.market/stp/testnet",
  "channel_id": "tb1q...",
  "commit_height": 0,
  "label": "agent-punish-drill-001",
  "confirm_unsafe_test_only": true
}
```

Asks the core node to retain its current server-local commitment snapshot. It does not broadcast anything. `commit_height` may be `0`.

### `stp.test_broadcast_retained_server_commitment`

Input:

```json
{
  "op": "stp.test_broadcast_retained_server_commitment",
  "chain": "testnet",
  "server": "https://apiprd.ordx.market/stp/testnet",
  "channel_id": "tb1q...",
  "commit_height": 0,
  "fee_rate": 1,
  "confirm_unsafe_test_only": true
}
```

Asks the core node to broadcast the retained old server commitment after the channel has advanced to a later commit height. The expected next step is `stp.punish_build` / `stp.punish_broadcast` from the client wallet.

## Status Values

Adapters should normalize status to one of:

- `INIT`
- `BROADCASTED`
- `L1_CONFIRMED`
- `L2_CONFIRMED`
- `READY`
- `CONFIRMED`
- `CLOSING`
- `FORCE_CLOSING`
- `SWEEPING`
- `CLOSED`
- `FAILED`
- `REMOTE_FAILED`

Adapters may include implementation-specific raw status in `raw_status`.
