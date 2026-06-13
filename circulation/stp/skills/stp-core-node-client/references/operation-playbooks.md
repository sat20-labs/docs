# STP Operation Playbooks

## Wallet Bootstrap

1. Run `wallet.status`.
2. If no wallet exists and the user asks to create one, run `wallet.create`.
3. If the user already has a mnemonic, run `wallet.import` through the wallet adapter.
4. For production use, prefer SAT20 PWA Wallet so mnemonic creation/import happens inside the PWA boundary.
5. After wallet bootstrap, run `wallet.status` again and confirm L1 address, SatoshiNet address, and WASM readiness.

## Mnemonic Export

1. Run `wallet.status`.
2. Confirm the user explicitly asked to export the mnemonic.
3. Run `wallet.export_mnemonic`.
4. If the adapter returns `AUTH_REQUIRED`, instruct the user to approve and enter the password in SAT20 PWA Wallet.
5. Return the mnemonic only after wallet-side authorization succeeds.

## Password Change

1. Run `wallet.status`.
2. Confirm the user explicitly asked to change the password.
3. Run `wallet.change_password`.
4. Password entry should happen in SAT20 PWA Wallet or a local secure adapter prompt.
5. Run `wallet.status` again after completion.

## Direct Wallet Asset Send

1. Run `wallet.status`.
2. Confirm chain, layer, asset, amount, destination address, and fee rate.
3. Run `wallet.send_assets`.
4. Poll `wallet.transaction`.
5. Report tx IDs, final status, and remaining wallet address.

## Channel Safety Snapshot

1. Run `stp.status`.
2. For every active channel, run `stp.safety_snapshot` if the adapter supports it.
3. If `stp.safety_snapshot` is unavailable, derive a minimal snapshot from channel details returned by `stp.status`.
4. Confirm channel point, commit height, local commitment tx, remote commitment tx, balances, CSV delay, and state backup status.
5. Run `stp.punish_status` if available and confirm revoked remote commitments have punish coverage.
6. If `stp.punish_status` cannot prove coverage, normalize it to `PUNISH_COVERAGE_UNKNOWN`; do not treat it as either covered or uncovered.
7. If the snapshot status is `READY_DEGRADED`, continue only read-only tracking. Do not run unlock, lock, splicing, close, or punish drill until it becomes `READY_SAFE`.
8. If local commitment tx is missing, state backup is absent, commit height regressed, punish coverage is missing, or punish coverage is unknown, stop value-moving operations and report `SAFETY_SNAPSHOT_REQUIRED`, `PUNISH_COVERAGE_MISSING`, or `PUNISH_COVERAGE_UNKNOWN`.

## Evidence Verification Matrix

Use this playbook whenever Agent must decide whether a channel operation is safe.

1. Identify the operation: open, expand, splicing-in, unlock, lock, splicing-out, close, force-close, or punish.
2. Collect BTC L1 evidence: relevant funding/splicing/commitment/punish txids, current visibility, confirmation count, block height, and spent status for the channel point.
3. Collect SatoshiNet evidence: anchor/deAnchor/unlock/lock txids, `pendingUtxosL2`, `UtxosL2`, `l2_pending_balance`, and `l2_spendable_balance`.
4. Collect local wallet evidence: latest local/remote commitment, commit height, CSV delay, local/remote balances, merkle roots, state backup, pending reservations, and punish coverage.
5. Collect peer/core-node evidence when available: peer commit height, channel point, status, and active channel list.
6. Compare evidence across layers. Do not use wallet summary balances as a substitute for UTXO and commitment evidence.
7. If any required evidence class is missing, stop and return the missing data category:
   - `MISSING_L1_TX_STATUS`
   - `MISSING_L2_UTXO_STATUS`
   - `MISSING_COMMITMENT_EXPORT`
   - `MISSING_PUNISH_COVERAGE`
   - `MISSING_RESERVATION_STATE`
   - `MISSING_PEER_CHANNEL_STATE`
8. Only proceed when all evidence needed for the requested operation is present and mutually consistent.

## BTC L1 Asset To SatoshiNet

1. Run `stp.status`.
2. Confirm the selected peer is a core node. Ordinary client wallets do not need stake assets to open with a core node.
3. If no `READY` channel exists, run `stp.open`.
4. If `stp.open` returns a stake-asset error, treat it as a likely bootstrap-node/core-node-upgrade path mismatch and recheck the peer type before asking for stake.
5. Once a channel exists, run the Channel Safety Snapshot playbook.
6. If the asset is already at the channel address but unmanaged, run expand through the adapter if available.
7. Do not provide asset inputs or fee inputs for ordinary splicing-in. The adapter chooses suitable L1 inputs and fee inputs internally.
8. If the adapter preview reports that a selected L1 UTXO carries multiple assets, confirm that only the request `asset` / `assetName` will ascend. Other assets in the same UTXO are ignored by current STP and must not be expected in L2 conservation checks.
9. Otherwise run `stp.splicing_in`.
10. Poll `stp.transaction`.
11. After completion, run the Channel Safety Snapshot playbook again and confirm commit height and commitment transactions are updated.
12. If the user wants personal-address liquidity, run `stp.unlock`.

## Channel Recovery

Use this playbook when L1/L2 chain evidence shows the channel address or channel point has moved, but local or peer channel state is missing, inactive, stale, or inconsistent.

1. Run `stp.status` and collect all known channels, reservations, channel address, channel point, status, commit height, and pending tx IDs.
2. Query BTC L1 and SatoshiNet indexers for the channel address, old channel point, latest splicing/open/close tx IDs, and unmanaged assets at the channel address.
3. If a peer or local backup has the latest channel data but the local wallet does not, run `stp.restore`, then run the Channel Safety Snapshot playbook.
4. If the L1 channel point changed but the plain sats were already anchored on SatoshiNet, run `stp.rebuild` with the latest L1 plain-sat channel UTXO when known. This recovery must not create a new SatoshiNet opening anchor.
5. Before `stp.rebuild`, verify the candidate L1 UTXO against the SatoshiNet channel ledger:
   - exact L1 outpoint in an ascending ledger entry means already anchored.
   - any output from the same L1 tx as an ascending ledger entry may be a post-splicing channel continuation.
   - exact outpoint in a descending v2 returned-channel-output record means a splicing-out balance returned to the channel address.
   - old descending records include the L1 txid but not returned-output metadata; accept a candidate only when its txid matches the legacy descending `L1TxId` and its vout is locked to the channel address.
6. If no active channel exists but the old local or peer channel data is still available, and the SatoshiNet channel ledger proves previous channel history for the same channel address, run `stp.reopen`. Prefer an eligible channel-address plain-sat UTXO when one exists; otherwise let the reopen path create a new user-wallet L1 funding transaction and wait for it to confirm.
7. If no active channel exists and the old channel data has been deleted or cannot be restored, treat this as exceptional recovery: run ordinary `stp.open` as a fresh client-core channel, wait until it reaches `READY`, then run `stp.expand` or `stp.expand_all` for any remaining channel-address assets that should be brought back under channel management. This path may pay the normal opening DAO fee again; do not use `stp.reopen` without old channel data.
8. If no active channel exists and the channel address has fresh plain sats that have not been anchored on SatoshiNet, run `stp.reopen` only when old channel data is still available; otherwise use the fresh-open-then-expand recovery path.
9. If a revoked commitment has been punished or a force-close drill proves the old channel cannot be safely resumed, and either the client or the core node still lists the stale channel as active, run `stp.clean_channel` on the stale side only after recording L1/L2 close evidence and the confirmed punish or close tx IDs. Then use the fresh-open-then-expand recovery path. Do not use `stp.clean_channel` to skip ordinary close or to hide an unresolved safety mismatch.
10. When operating a core node directly, remember that the local management router is normally bound to `127.0.0.1` on `rpc.host + 1`; the public protocol router may not expose management paths such as `/clean/channel`.
11. After `stp.rebuild`, `stp.reopen`, or fresh recovery `stp.open`, run `stp.status` until the channel is `READY`, then run the Channel Safety Snapshot playbook. If the snapshot returns `READY_DEGRADED`, keep polling funding, reservation, local/core channel status, and ledger evidence.
12. If assets are already at the channel address but not in the latest commitment allocation, run `stp.expand` for the specific L1 UTXO or `stp.expand_all` when the adapter can safely enumerate all eligible assets.
13. If `stp.expand` finds that the L1 UTXO was already ascended, treat this as an interrupted splicing-in recovery, not as an ordinary failure. The client and core node must verify the existing SatoshiNet ascend record, reuse the existing L2 anchor output, and advance the channel commitment without creating or broadcasting a new anchor transaction.
14. For interrupted splicing-in recovery, verify:
   - the ascend record's `fundingUtxo` equals the requested L1 UTXO.
   - the ascend record's channel address equals the channel ID.
   - the recovered L2 anchor output is still unspent and not already managed by the channel.
   - the recovered L2 anchor output asset and amount equal the requested asset and L1 funding asset.
   - the channel commit height advances and both local and remote commitments include the recovered asset.
15. Never run ordinary unlock, lock, splicing-out, or close until recovery ends with a valid safety snapshot and punish coverage.

## BRC20 Splicing Handling

1. Run `wallet.status` or the indexer summary query to confirm the BRC20 balance.
2. Do not ask the user or Agent to choose a BRC20 transfer output for STP splicing.
3. For `stp.splicing_in`, call the adapter with only `asset`, `amount`, `channel_id`, `chain`, and optional fee policy. The adapter should choose a suitable transfer output or create a fresh transfer inscription.
4. For `stp.splicing_out`, call the adapter with only `asset`, `amount`, `channel_id`, `to_l1_address`, `chain`, and optional fee policy. The adapter should choose a suitable transfer output or create a fresh transfer inscription.
5. If the adapter returns `BRC20_TRANSFER_BUILD_FAILED`, `INSUFFICIENT_L1_FEE_BALANCE`, or another construction error, report that error and wait for funding or adapter recovery. Do not retry by manually supplying inputs.
6. Do not use a plain asset UTXO query to conclude that no BRC20 UTXO exists.

## Unknown Network Result During Channel Operations

Use this playbook when `stp.open`, `stp.close`, `stp.splicing_in`, `stp.splicing_out`, `stp.lock`, or `stp.unlock` reaches a broadcast or final peer exchange step and the adapter returns timeout, connection reset, service unavailable, or another unknown network result.

1. Stop. Do not repeat the value-moving operation with the same UTXOs.
2. Save the operation, channel ID, reservation ID if exposed, asset, amount, all constructed or returned txids, and the exact error text.
3. Query local `stp.status` and look for a pending reservation for the same operation.
4. If a pending reservation exists, keep polling `stp.transaction` or reservation details instead of starting a fresh operation.
5. Query every related L1 and L2 txid through the indexers. If a tx is visible or may have been broadcast, keep polling the existing reservation.
6. If no pending reservation exists, query local `stp.safety_snapshot` and the core-node channel state through the protocol API or an adapter operation.
7. Compare commitment height, channel point, local/remote balances, asset roots, and commitment txids from both perspectives.
8. If both peers are on the same old safe commitment, no new tx is visible, and no pending reservation remains, the operation may be retried with fresh preflight checks and fresh UTXO selection.
9. If either peer advanced, a related tx is visible, or a pending reservation remains, enter channel recovery. Do not spend the same UTXOs or start another channel operation.
10. If a peer has advanced but the local wallet has not, export commitment and punish coverage before any recovery action.
11. Record the incident in validation notes; unknown network results are protocol recovery conditions, not normal asset-balance failures.
12. For an unknown result during early peer negotiation, still compare local channel state, core-node channel state, reservations, and related tx visibility before retrying. Retry only if both peers remain on the same ready commitment and no reservation or tx evidence exists.

## Channel Asset To SatoshiNet Personal Address

1. Confirm the channel is `READY`.
2. Run the Channel Safety Snapshot playbook.
3. Confirm channel balance is sufficient.
4. Do not provide unlock inputs or fee inputs. The adapter selects channel inputs and pays the SatoshiNet fee internally.
5. Remember SatoshiNet L2 UTXOs do not have the BTC dust limit and can be 0. BRC20 and Runes can be carried by 0-sat SatoshiNet UTXOs; BTC L1 BRC20/Runes transfer UTXOs still obey L1 output rules and commonly carry the minimum 330 sats. ORDX must carry enough bound sats according to its `bindingSat` rule. Do not reject a plan solely because L2 change is below 330 sats.
6. For assets from a recent splicing-in or expand, confirm the target asset is in `l2_spendable_balance`, not only in `local_balance`. If it is still in `l2_pending_balance` / `pendingUtxosL2`, wait for adapter/indexer convergence and do not retry unlock.
7. Run `stp.unlock`.
8. Poll `stp.transaction` until `CONFIRMED`.
9. Run the Channel Safety Snapshot playbook again.

## SatoshiNet Personal Asset Back To Channel

1. Confirm the channel is `READY`.
2. Run the Channel Safety Snapshot playbook.
3. Do not provide lock inputs or fee inputs. The adapter selects SatoshiNet personal-address inputs and fee inputs internally.
4. Try `stp.lock`.
5. If adapter returns `INSUFFICIENT_CHANNEL_CAPACITY`, run `stp.lock_with_expand`.
6. Poll `stp.transaction`.
7. Run the Channel Safety Snapshot playbook again.
8. Report final channel status and tx IDs.

## Channel Asset Back To BTC L1

1. Validate destination BTC L1 address and chain.
2. Run the Channel Safety Snapshot playbook.
3. Do not provide asset inputs or fee inputs. The adapter selects BTC L1 fee inputs internally and must not use asset-bearing UTXOs as ordinary fee inputs.
4. If the adapter reports insufficient BTC fee balance, fund the wallet with ordinary sats or wait for fee funds to confirm; do not retry by manually supplying fee inputs.
5. For BRC20, let the adapter choose a suitable transfer output or create a fresh transfer inscription when needed.
6. Run `stp.splicing_out`.
7. Poll de-anchor and L1 transaction status through `stp.transaction`.
8. Run the Channel Safety Snapshot playbook again if the channel remains open.
9. Report final L1 tx ID.

## Permanent Channel Exit

1. Run the Channel Safety Snapshot playbook.
2. Prefer `stp.close` with `mode:"cooperative"`.
3. Use `mode:"force"` only when peer is offline, unresponsive, or safety requires unilateral exit.
4. Before force close, run `stp.force_close_plan` if available and confirm local commitment tx, CSV delay, and sweep conditions.
5. For force close, track CSV delay and sweep status.

## Revoked Commitment Defense

1. If the chain watcher reports a remote commitment tx on BTC L1, compare its txid with current and revoked commitment records.
2. If the tx is the latest valid remote commitment, continue close/sweep tracking.
3. If the tx is a revoked commitment, run `stp.punish_status` for the channel.
4. If punish coverage exists, run `stp.punish_build` with `broadcast:false` to verify the signed punishment path.
5. Run `stp.punish_broadcast` or `stp.punish_build` with `broadcast:true`.
6. Query every returned punish txid on BTC L1, even if the broadcast response is `ok`; Agent must verify final tx visibility, not infer it from the aggregate response alone.
7. If punish broadcast returns an unknown network result, do not manually rebroadcast the full punish package. Query every punish txid on BTC L1 first. If all txids are visible, continue polling confirmation. If some txids are missing, report the missing txids and require adapter-assisted retry or operator review.
8. Poll the punish transactions until all are confirmed.
9. If punish coverage is missing, report `PUNISH_COVERAGE_MISSING` immediately and stop all ordinary operations.

## Testnet Punish Drill

Use only on testnet against a core node whose drill endpoints strictly reject non-testnet requests.

1. Run the Channel Safety Snapshot playbook and require `READY_SAFE`.
2. If the drill is meant to demonstrate asset circulation, run at least one Runes `stp.splicing_in` and one BRC20 `stp.splicing_in`, then save L1 tx IDs and indexer UTXO evidence.
3. Run `stp.unlock` for a small amount of one spliced asset and verify the asset appears at the SatoshiNet personal address.
4. Run `stp.lock`; if capacity is insufficient, run `stp.lock_with_expand`, then verify the asset returns to channel protection.
5. Optionally run a small `stp.splicing_out` to show the asset can exit back to BTC L1.
6. Run the Channel Safety Snapshot playbook again and require `READY_SAFE`.
7. Run `stp.test_retain_server_commitment` with the current `channel_id`, current `commit_height`, and `confirm_unsafe_test_only:true`.
8. Move the channel to a new state with a small testnet-only operation such as `stp.lock`, `stp.unlock`, or a controlled splicing test.
9. Run the Channel Safety Snapshot playbook again and verify `commit_height` advanced.
10. Run `stp.punish_status`; if the old remote commitment does not have punish coverage, stop and report `PUNISH_COVERAGE_MISSING`.
11. Run `stp.test_broadcast_retained_server_commitment` for the retained `commit_height`.
12. Watch BTC L1 for the old server commitment tx.
13. Run `stp.punish_build` with `broadcast:false`; verify the punish transaction spends the revoked commitment output to the user's control path.
14. Run `stp.punish_broadcast`.
15. Query each returned punish txid on L1, even if the adapter returned `ok`.
16. If the broadcast result is unknown, query each returned punish txid on L1. If the package was partially accepted, record which txids are visible and which are missing, then require adapter-assisted retry or operator review for the missing txs.
17. Poll confirmation and record the drill result in the testnet validation log.
18. If the user asks for a shareable proof, collect PWA screenshots, L1 explorer pages, L2 explorer pages, indexer JSON, and skill outputs, then follow `docs/circulation/stp/testnet-punish-drill-video.md` to produce a 2-minute video.

## Failure Handling

- `INSUFFICIENT_CHANNEL_CAPACITY`: use `stp.lock_with_expand`.
- `PEER_OFFLINE`: stop ordinary cooperative operations; ask before force close.
- `CHAIN_MISMATCH`: stop immediately.
- `SIGNATURE_INVALID`: stop immediately and report a security error.
- `UTXO_LOCKED` or pending transaction: poll existing transaction; do not reuse UTXO.
- `REMOTE_FAILED`: stop and report chain evidence plus adapter message.
- `SAFETY_SNAPSHOT_REQUIRED`: stop value-moving channel operations until commitment state and backup are readable.
- `PUNISH_COVERAGE_MISSING`: stop ordinary operations and ask the wallet/STP adapter to recover or re-export punish coverage before continuing.
- `PUNISH_COVERAGE_UNKNOWN`: stop ordinary operations; the wallet/STP adapter could not prove punish coverage.
- `REVOKED_COMMITMENT_SEEN`: prioritize punish build/broadcast.
- `TESTNET_FAULT_INTERFACE_UNAVAILABLE`: the target core node does not expose the testnet-only fault-injection interface or rejected the request because the network is not testnet; skip the drill or use a dedicated testnet core node.
- `CORE_NODE_UNAVAILABLE`: stop retrying the same value-moving request, query safety snapshot, reservation/transaction status, and related L1/L2 tx visibility, then resume only when evidence shows the operation did not advance or has safely converged.
