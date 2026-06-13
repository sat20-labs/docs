# SAT20 PWA Wallet WASM Adapter

This reference describes the recommended adapter shape for Agent-controlled STP wallets.

## Recommended Model

Use SAT20 PWA Wallet as the installed wallet and authorization container. The PWA loads the wallet and STP WASM engines, owns private-key access, stores wallet/channel state, and shows user confirmations. Agent interacts only with a permissioned adapter exposed by the PWA.

Agent should not load `sat20wallet.wasm` or `stpd.wasm` directly, and should not store mnemonics, private keys, revocation secrets, or raw wallet databases.

The PWA should be designed for both human users and AI Agents. Human users need clear approvals and understandable risk explanations. Agents need structured state, predictable errors, operation previews, polling handles, and scoped permissions. The same PWA adapter should serve both without weakening the wallet security boundary.

## Components

| Component | Responsibility |
| --- | --- |
| SAT20 PWA Wallet | Installed user wallet, permission UI, DApp authorization, persistent wallet/channel state |
| `sat20wallet.wasm` | Base wallet, account, signing, and asset operations |
| `stpd.wasm` | STP channel lifecycle operations |
| PWA STP Adapter | Normalizes JSON operations, checks permissions, calls WASM, returns JSON responses |
| STP Skill | Plans user-approved STP operations and calls the adapter |

## Adapter Transport

The PWA adapter can be exposed through one of these transports:

- Local HTTP endpoint, configured in Agent as `STP_ADAPTER_URL`.
- Browser `postMessage` bridge following the SAT20 DApp Connect request/response pattern.
- A small local CLI wrapper configured as `STP_CLIENT_CMD`, where the wrapper forwards JSON requests to the PWA bridge.

The JSON operation contract remains the same regardless of transport.

## Authorization Flow

For value-moving or secret-moving operations, the adapter must require wallet-side authorization.

The current SAT20 PWA DApp bridge accepts the standard `wallet.*` and `stp.*` method names through the SAT20 DApp Connect `action` field. Read-only operations such as `wallet.status` and `stp.status` execute directly after origin authorization. Operations that create/import/export wallets, change passwords, send assets, or change channel state are routed through a wallet-side `AGENT_OPERATION` approval dialog before execution.

An unapproved direct call should return:

```json
{
  "ok": false,
  "operation": "stp.splicing_out",
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "This Agent operation must be confirmed in the SAT20 PWA Wallet before execution."
  }
}
```

After approval, the PWA executes the operation and returns the result to the requesting Agent. Mainnet operations must show chain, asset, amount, destination, fee rate, channel ID, and operation type in the PWA confirmation UI.

Production hardening target: password entry, password change, and mnemonic reveal should be collected inside the PWA UI rather than passed through Agent JSON. The current bridge establishes the operation and approval boundary first; the next iteration should move sensitive form fields into the approval component.

## Operation Mapping

| JSON operation | PWA / WASM responsibility |
| --- | --- |
| `wallet.create` | Create a wallet inside the PWA boundary and initialize both wallet and STP WASM state |
| `wallet.import` | Import a mnemonic or private key inside the PWA boundary; do not echo secrets back |
| `wallet.export_mnemonic` | Reveal the mnemonic only after PWA password verification and explicit user confirmation |
| `wallet.change_password` | Change the wallet password inside the PWA UI; do not pass passwords through Agent JSON |
| `wallet.status` | Report wallet readiness, active account, L1 address, SatoshiNet address, and WASM readiness |
| `wallet.send_assets` | Send BTC L1 or SatoshiNet assets directly from the wallet address |
| `wallet.transaction` | Track direct wallet send status |
| `stp.status` | Report wallet readiness, current account, STP server readiness, channels, current channel, and pending transactions |
| `stp.open` | Open a channel with the configured core node |
| `stp.unlock` | Release channel assets to a SatoshiNet personal address |
| `stp.lock` | Lock SatoshiNet personal-address assets back to the channel |
| `stp.lock_with_expand` | Execute lock with expand when direct lock lacks channel capacity |
| `stp.splicing_in` | Move BTC L1 assets into the channel |
| `stp.splicing_out` | Move channel assets back to BTC L1 |
| `stp.close` | Perform cooperative or force channel close |
| `stp.safety_snapshot` | Return channel point, commit height, local/remote commitments, balances, CSV delay, and punish coverage |
| `stp.commitment_export` | Export current commitment transactions and read-only verification material, without private keys or revocation secrets |
| `stp.punish_status` | Report saved punish coverage for revoked remote commitments |
| `stp.punish_build` | Build and dry-run verify the punish transaction for a revoked remote commitment |
| `stp.punish_broadcast` | Broadcast the verified punish transaction |
| `stp.force_close_plan` | Return the local unilateral exit plan and sweep condition |
| `stp.transaction` | Return current transaction status, tx IDs, error state, and next polling interval |

Current PWA bridge status:

| Operation group | Status |
| --- | --- |
| `wallet.status`, `stp.status` | Implemented through the DApp bridge and returns wallet, channel, and UTXO snapshots when WASM is available |
| `wallet.create`, `wallet.import`, `wallet.export_mnemonic`, `wallet.change_password` | Routed through Agent approval; sensitive field entry should move into wallet UI in the next hardening pass |
| `wallet.send_assets` | Routed through Agent approval; supports BTC L1 and SatoshiNet layers |
| `stp.open`, `stp.close`, `stp.splicing_in`, `stp.splicing_out`, `stp.lock`, `stp.lock_with_expand`, `stp.unlock` | Routed through Agent approval and mapped to STP WASM operations |
| `stp.safety_snapshot`, `stp.commitment_export`, `stp.punish_status`, `stp.force_close_plan` | Exposed through STP WASM and PWA Agent Adapter as read-only or protective safety calls |
| `stp.punish_build`, `stp.punish_broadcast` | Exposed through STP WASM and PWA Agent Adapter as protective safety calls; `broadcast` requires wallet-side confirmation |
| `wallet.transaction`, `stp.transaction` | PWA adapter can poll explicit `tx_ids` through L1/L2 indexers; `stp.transaction` can also query local reservation state by `reservation_id` |

## PWA/WASM Capability Status Required By The Skill

The skill can already call these operations. The PWA and WASM layer now expose the P0 safety interfaces needed for Agent verification. The remaining work is mostly schema hardening, richer evidence, and real testnet sample responses.

| Capability | Needed by skill operation | Current PWA behavior | Required WASM / adapter capability |
| --- | --- | --- | --- |
| Reservation lookup by ID | `stp.transaction` with only `reservation_id` | Implemented through STP WASM `reservationStatus` and PWA `stp.transaction` | Harden the schema to always include related L1/L2 txids, channel ID, error, and next polling step when available |
| Complete transaction evidence | `wallet.transaction`, `stp.transaction` | Polls explicit `tx_ids` against configured L1/L2 indexers | Return layer-tagged tx visibility, confirmations, block height, mempool/not-found state, and explorer/indexer URLs from a stable adapter schema |
| Standard safety snapshot | `stp.safety_snapshot` | Implemented through STP WASM `SafetySnapshot`; falls back to partial channel detail only for older WASM | Freeze a stable v1 schema and add backup status / merkle roots as explicit fields |
| Commitment export | `stp.commitment_export`, `stp.force_close_plan` | Implemented through STP WASM `CommitmentExport` with txids, tx hex, balances, deAnchor txs, and no secrets | Add canonical input/output evidence and merkle-root fields to the response schema |
| Punish coverage query | `stp.punish_status`, preflight for every value-moving operation | Implemented through watchtower-backed STP WASM query | Standardize `NO_REVOKED_REMOTE_STATE` / `COVERED` / `UNKNOWN` / `MISSING` status names across adapters |
| Punish build | `stp.punish_build` | Implemented through STP WASM `BuildPunishTx` without exposing revocation secrets | Add sample responses and require L1 package acceptance evidence in test drills |
| Punish broadcast | `stp.punish_broadcast` | Implemented through STP WASM `BroadcastPunishTx`; requires wallet approval and returns txids | Keep Agent-side post-broadcast polling for every returned txid |
| Force-close plan completeness | `stp.force_close_plan` | Implemented through STP WASM with local commitment, deAnchor, prev/next txs, CSV, and action warning | Include earliest sweep height/time, user-controlled destination, required fee inputs, and close-state warnings |
| Sweep build dry-run | `stp.sweep_build` | Implemented through STP WASM build/sign/verify and optional authorized broadcast; `broadcast:false` does not send a tx | Freeze response schema with commit txid, sweep txid, tx hex package, fee, verified, broadcastable, CSV height, and broadcast result when requested |
| Channel ledger evidence | rebuild / reopen / expand playbooks | Not available directly through PWA adapter | Query L2 indexer for ascend/deAnchor ledger, returned channel outputs, and whether an L1 UTXO is already anchored |

## Security Requirements

- The PWA remains the only component allowed to access private keys.
- Agent receives only operation results, transaction IDs, channel IDs, status, explicit error messages, and mnemonics only when the user explicitly asks to export them and approves inside the wallet.
- Password creation, password verification, mnemonic reveal confirmation, and password changes should happen in the PWA UI, not in Agent chat.
- The adapter must reject expired requests, duplicate request IDs, unauthorized origins, chain mismatch, and destination replacement.
- The adapter must not release old-state safety material until the new commitment state is fully verified.
- The adapter must not expose raw revocation secrets to the Agent; it should expose signed punish transactions, txids, or broadcast results.
- Before a value-moving STP operation, the adapter should be able to produce a fresh safety snapshot. If it cannot, it should return `SAFETY_SNAPSHOT_REQUIRED`.
- If revoked remote commitments lack punish coverage, the adapter should return `PUNISH_COVERAGE_MISSING` and stop ordinary channel operations.
- If direct lock fails due to insufficient capacity, the adapter should recommend `stp.lock_with_expand`.

## Agent-Friendly Requirements

- Return structured asset inventories for BTC L1, channels, and SatoshiNet.
- Return operation previews before signing: source, destination, asset, amount, fee, channel impact, and fallback path.
- Support scoped sessions, such as testnet-only, max amount, specific assets, read-only, or one-operation approval.
- Return stable error codes that an Agent can act on, such as `OUTPUT_VALUE_TOO_SMALL`, `TICKER_INFO_MISSING`, `UTXO_LOCKED`, `PEER_OFFLINE`, and `INSUFFICIENT_CHANNEL_CAPACITY`.
- Provide transaction and STP reservation IDs for polling.
- Keep an audit log of Agent requests, user approvals, and final transaction IDs.
- Expose recovery hints, especially force close, sweep, and lock-with-expand.
- Expose enough commitment metadata for an Agent to explain to the user why assets remain under user control.
