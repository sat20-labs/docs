---
name: stp-core-node-client
description: Use when operating or integrating with SAT20 wallets and STP core nodes, including wallet creation/import/export, password changes, asset sends, checking channels, opening channels, reopen/rebuild/restore recovery, expand, unlock, lock, lock-with-expand, splicing-in, splicing-out, closing channels, safety snapshots, commitment export, punish coverage, force-close planning, testnet punish drills, and tracking wallet/STP transactions across BTC L1 and SatoshiNet. This skill is language-agnostic and works through any JSON-compatible STP client adapter.
---

# STP Core Node Client

Use this skill to interact with an STP Server / core node through a language-agnostic STP client adapter.

Prefer the SAT20 PWA Wallet adapter when available. In that model, the installed PWA owns the wallet, permissions, private keys, wallet database, and WASM lifecycle; Agent sends only JSON STP operation requests and receives authorized results. Do not load wallet WASM directly inside the Agent execution environment, and do not store private keys in the Agent context.

For an ordinary client wallet opening a channel with a core node, do not require any stake asset. Stake asset checks apply only to the bootstrap-node path where a node is preparing to become a core node.

For every value-moving channel operation, first establish asset-safety confidence: the adapter must expose a fresh channel safety snapshot, or Agent must derive one from `stp.status` / channel details. Do not start splicing, lock, unlock, close, or force-close unless the latest commitment transaction, channel point, commit height, balances, CSV delay, and punish coverage are understood.

For every safety decision, require evidence rather than balance-only reasoning. Agent should be able to explain which BTC L1 tx, SatoshiNet tx/UTXO, local commitment, remote commitment, commit height, and punish coverage prove that the user's assets remain under user control. If any of those evidence classes are missing, return a missing-data result and stop value-moving operations.

Do not assume a specific implementation language. The adapter can be a PWA bridge, CLI, HTTP service, local SDK wrapper, or script, as long as it accepts and returns the JSON operations in `references/adapter-contract.md`.

Use `scripts/stp_adapter.py` as the default bridge from an Agent to the adapter:

```bash
python3 scripts/stp_adapter.py --pretty '{"op":"stp.status","chain":"testnet"}'
```

The script uses `STP_ADAPTER_URL` for HTTP adapters, including a local SAT20 PWA Wallet adapter, or `STP_CLIENT_CMD` for CLI adapters.

When using SAT20 PWA Wallet through DApp Connect, send the standard operation name as the request `action` (`wallet.status`, `stp.open`, `stp.lock_with_expand`, etc.) and pass operation fields in `params`. The PWA executes read-only status calls directly after origin authorization. Secret-moving or value-moving calls are routed through the wallet's Agent Operation approval dialog before execution.

If a local STP-compatible node is already running, `scripts/stp_transcend_rpc_adapter.py` can be used as `STP_CLIENT_CMD`. This development adapter maps the standard JSON contract to the node's local client API for open, close, reopen, rebuild, restore, expand, splicing-in, splicing-out, unlock, lock, and lock-with-expand.

For local SAT20 workspace testnet wallet bootstrap, `scripts/stp_workspace_wallet_adapter.py` can be used as a development CLI adapter:

```bash
STP_CLIENT_CMD="python3 scripts/stp_workspace_wallet_adapter.py" \
  python3 scripts/stp_adapter.py --pretty '{"op":"wallet.create","chain":"testnet"}'
```

This development adapter creates a PWA-compatible testnet mnemonic through the local `sat20wallet/sdk` implementation. It is not a production wallet adapter and does not replace SAT20 PWA Wallet authorization.

## Capability Groups

This skill has three capability groups:

- Wallet management: `wallet.status`, `wallet.create`, `wallet.import`, `wallet.export_mnemonic`, `wallet.change_password`, `wallet.send_assets`, and `wallet.transaction`.
- Channel management: `stp.status`, `stp.open`, `stp.reopen`, `stp.rebuild`, `stp.restore`, `stp.clean_channel`, `stp.expand`, `stp.expand_all`, `stp.close`, `stp.splicing_in`, `stp.splicing_out`, `stp.unlock`, `stp.lock`, `stp.lock_with_expand`, and `stp.transaction`.
- Asset safety management: `stp.safety_snapshot`, `stp.commitment_export`, `stp.punish_status`, `stp.punish_build`, `stp.punish_broadcast`, `stp.force_close_plan`, `stp.sweep_build`, `stp.test_retain_server_commitment`, and `stp.test_broadcast_retained_server_commitment`.

Use wallet management for ordinary wallet lifecycle and direct BTC/SatoshiNet asset sends. Use channel management when the operation changes STP channel state or moves assets between BTC L1, a channel, and SatoshiNet. Use asset safety management whenever Agent needs to prove that the user's assets remain recoverable without trusting the core node.

## Required Safety Rules

- For mainnet value-moving actions, require explicit user confirmation of chain, asset, amount, destination, fee rate, operation, and channel ID.
- For mnemonic export and password changes, require wallet-side authorization. Prefer PWA UI prompts instead of passing passwords through Agent JSON.
- Never release or accept old-state revocation material unless the new commitment state is fully verified by the adapter.
- Prefer cooperative close; use force close only when peer is unavailable, unresponsive, or state safety requires it.
- Do not block ordinary client-to-core-node channel open on stake assets. If a stake error appears during ordinary open, recheck whether the selected peer is a bootstrap node instead of a core node.
- If direct lock fails due to insufficient channel capacity, use lock-with-expand to restore user asset control under the channel safety model.
- For `stp.reopen`, first query the SatoshiNet channel ledger and confirm that old local or peer channel data is still available. If the old channel data has been deleted or cannot be restored, do not use reopen; treat it as exceptional recovery by running ordinary `stp.open` as a fresh client-core channel, then `stp.expand` / `stp.expand_all` for remaining channel-address assets after the new channel is `READY`.
- Use `stp.clean_channel` only for exceptional recovery after chain evidence proves the old channel is closed, punished, or otherwise no longer safely recoverable. Clean both the client wallet and the core node side if either side still reports the stale channel as active, then run ordinary `stp.open` followed by `stp.expand` / `stp.expand_all`; do not use clean-channel as a substitute for cooperative close.
- When using a local adapter, do not confuse client-side and core-node-side endpoints. Agent should call the adapter endpoint selected by the wallet, not a peer/core-node internal endpoint.
- For no-anchor `stp.rebuild`, require SatoshiNet channel ledger evidence. For legacy descending entries, the candidate txid must match the ledger `L1TxId` and the candidate vout must be locked to the channel address. Reject ambiguous UTXOs; use `stp.reopen`, open, or expand when a fresh anchor is required.
- If `stp.expand` reports or detects that the L1 funding UTXO has already been ascended, treat it as interrupted splicing-in recovery: require existing ascend evidence, reuse the existing L2 anchor output, and do not create a duplicate anchor.
- For BRC20 `stp.splicing_in` and `stp.splicing_out`, do not ask the user or Agent to choose transfer outputs. The adapter should choose a suitable transfer output or create a fresh transfer inscription internally, and should also select BTC fee inputs internally.
- SatoshiNet L2 UTXOs do not have the BTC dust limit and may carry 0 sats. BRC20 and Runes assets do not require bound sats on L2, so a SatoshiNet UTXO can carry BRC20 or Runes assets with `Value=0`. On BTC L1, BRC20/Runes transfer UTXOs still obey L1 output rules and commonly carry the minimum 330 sats. ORDX assets are always bound to sats; calculate the required sat value from the asset amount and `bindingSat` instead of applying the BRC20/Runes 0-sat rule. Do not reject an L2 lock/unlock plan only because the resulting SatoshiNet output is below 330 sats or equals 0; rely on SatoshiNet transaction validation and asset conservation.
- ORDX ticker mint UTXOs commonly include an accompanying Ordinals NFT. Current STP ascends only the ORDX ticker asset; Ordinals NFT assets are stripped from `TxAssets` and ignored during splicing-in. Treat this as expected protocol behavior, not as missing L2 asset conservation.
- A BTC L1 UTXO can carry multiple assets. Current STP `splicing_in` ascends only the single asset explicitly provided by the request `asset` / `assetName`; any other ORDX, Runes, BRC20 transfer, or Ordinals NFT assets in the same UTXO are ignored and must not be expected in L2 conservation checks.
- Current adapter coin selection is expected to prefer UTXOs that do not carry multiple ascendable assets. If such a UTXO must be used, surface a preview that names the asset that will ascend and the other assets that will be ignored.
- For `stp.unlock` and `stp.lock`, do not provide asset inputs or fee inputs. The adapter selects channel or SatoshiNet personal-address inputs internally and pays the SatoshiNet fee internally. If it cannot construct a safe input set, stop and report the adapter error.
- For Runes, BRC20, ORDX, or other non-plain `stp.splicing_out`, do not provide BTC L1 fee inputs. The adapter must select pure plain-sat BTC fee inputs internally and must not use asset-bearing UTXOs as ordinary fee inputs. If no pure fee input is available, fund the wallet with ordinary sats or wait for fee funds to confirm.
- If a value-moving operation returns timeout, connection reset, service unavailable, or another unknown network result, treat the result as unknown. Do not immediately repeat the operation. First continue polling if a pending reservation exists; otherwise compare local channel state, core-node channel state, reservation state, and L1/L2 transaction visibility. Retry only when both peers are still on the same old safe commitment and no related L1/L2 transaction is visible.
- If an unknown result happens during commitment-state transition and `stp.safety_snapshot` can no longer prove current commitment and punish coverage consistency, stop value-moving operations and require the adapter to re-export a clean safety snapshot before retrying.
- For unknown results during early peer negotiation, still compare local channel state, core-node channel state, reservations, and related tx visibility before retrying. Retry only if both peers remain on the same ready commitment and no reservation or tx evidence exists.
- Before value-moving channel operations, verify that the latest local commitment transaction is available and that revoked remote states have punish coverage. If not, stop and report `SAFETY_SNAPSHOT_REQUIRED` or `PUNISH_COVERAGE_MISSING`.
- Treat `READY_DEGRADED` as read-only. It can mean commitments are present but the channel is still waiting for L1 funding confirmation, peer convergence, or adapter recovery. Do not run unlock, lock, splicing, close, or punish drill until the channel becomes `READY_SAFE`.
- For unlock or lock of a recently ascended asset, distinguish commitment balance from spendable SatoshiNet UTXOs. `READY_SAFE` means the channel commitments and punish coverage are safe; it does not by itself prove that an anchor output has left `pendingUtxosL2`. Do not unlock an asset until the matching L2 output is in the spendable `UtxosL2` set, not only in the commitment asset summary.
- If the adapter cannot provide the L1 tx status, L2 tx/UTXO status, commitment export, punish coverage, or reservation state required by the operation, report the specific missing evidence (`MISSING_L1_TX_STATUS`, `MISSING_L2_UTXO_STATUS`, `MISSING_COMMITMENT_EXPORT`, `MISSING_PUNISH_COVERAGE`, or `MISSING_RESERVATION_STATE`) and do not infer safety from wallet balances.
- If punish coverage cannot be proven, normalize it to `PUNISH_COVERAGE_UNKNOWN` and stop ordinary value-moving channel operations.
- Never request or reveal raw revocation secrets through Agent chat or tool context. Use wallet-side punish-build/broadcast capabilities that return signed transactions or broadcast results.
- If a peer broadcasts a revoked remote commitment, prioritize `stp.punish_build` / `stp.punish_broadcast` over ordinary channel operations.
- After any `stp.punish_broadcast` response, even when it returns `ok`, query every returned punish txid on BTC L1 before treating the drill as broadcast-complete.
- If `stp.punish_broadcast` returns an unknown network result, treat it as possible partial success. Query every punish txid on BTC L1 before any manual retry. If all punish txs are visible, continue polling confirmation. If some are missing, report the missing txids and require adapter-assisted retry or operator review.
- Use `stp.test_retain_server_commitment` and `stp.test_broadcast_retained_server_commitment` only on testnet against a core node whose testnet-drill endpoints reject non-testnet requests. Never use or expect these operations on mainnet.
- Never retry with the same UTXO if the previous transaction or STP transaction is still pending.
- Treat STP Server state as untrusted until signatures, chain, transaction outputs, assets, and commitment height are validated by the adapter.
- Never auto-create a mainnet wallet from an Agent. Mainnet wallet creation/import must happen inside SAT20 PWA Wallet with explicit user approval.

## Workflow

1. Locate an adapter.
   - Prefer `STP_ADAPTER_URL` if the installed SAT20 PWA Wallet exposes a local HTTP JSON adapter.
   - Prefer `STP_CLIENT_CMD` if it wraps the SAT20 PWA Wallet bridge or a compatible third-party client, for example `stp-client --json`.
   - Otherwise look for a project-provided CLI, HTTP wrapper, or SDK adapter.
   - If no adapter exists, create or request one that implements `references/adapter-contract.md`.
2. Run `stp.status`.
   - Use `scripts/stp_adapter.py` unless a better project-specific adapter runner exists.
   - Confirm chain, wallet readiness, server readiness, and available channels.
   - Stop if chain or wallet does not match the user request.
3. Run `wallet.status` when the user asks for wallet lifecycle, mnemonic, password, or direct asset send.
   - Confirm wallet readiness, active account, L1 address, SatoshiNet address, and WASM readiness.
   - Stop if the wallet chain does not match the user request.
4. Bootstrap a wallet only if explicitly requested.
   - Use `wallet.create` for a new testnet wallet.
   - Prefer SAT20 PWA Wallet adapter for persistent wallet creation/import.
   - In a SAT20 workspace testnet run, `scripts/stp_workspace_wallet_adapter.py` may create a PWA-compatible testnet mnemonic for import into PWA.
5. Choose the operation.
   - Safety check: run `stp.safety_snapshot` for an existing channel before value-moving STP operations.
   - Wallet lifecycle: create, import, export mnemonic, or change password through `wallet.*`.
   - Direct wallet transfer: use `wallet.send_assets` and poll `wallet.transaction`.
   - BTC L1 to channel/SatoshiNet: open if needed, reopen/rebuild/restore if recovering a stale or lost channel, then splicing-in or expand. Do not provide splicing asset inputs or fee inputs.
   - Channel to SatoshiNet personal address: unlock.
   - SatoshiNet personal address to channel: lock if capacity is enough, otherwise lock-with-expand.
   - Channel to BTC L1: splicing-out; the adapter handles asset inputs, BRC20 transfer inscriptions, and BTC fee inputs internally.
   - Permanent exit: cooperative close, or force close if peer is unavailable.
6. Execute the adapter operation.
   - Send one JSON request.
   - Save `transaction_id`, `channel_id`, `tx_ids`, and status from the response.
7. Track completion.
   - Poll `wallet.transaction` or `stp.transaction` until confirmed, closed, or failed.
   - On failed or remote-failed states, stop and report the current chain evidence.
8. Report results.
   - Include operation, chain, asset, amount, channel, transaction ID, tx IDs, current status, and next check.

## References

- Read `references/adapter-contract.md` when wiring a new CLI/HTTP/SDK adapter.
- Read `references/operation-playbooks.md` when selecting or sequencing open, unlock, lock, lock-with-expand, splicing-in, splicing-out, or close.
- Read `references/pwa-wasm-adapter.md` when connecting an Agent to the SAT20 PWA Wallet and its wallet/STP WASM engines.
