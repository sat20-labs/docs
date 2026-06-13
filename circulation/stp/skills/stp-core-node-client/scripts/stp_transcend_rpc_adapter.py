#!/usr/bin/env python3
"""Adapter from the STP JSON skill contract to a running transcend RPC node.

Set STP_TRANSCEND_RPC_URL to the local management RPC URL. For a transcend
config with rpc.host 0.0.0.0:9060, the local management RPC is usually
http://127.0.0.1:9061.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional


DEFAULT_RPC_URL = "http://127.0.0.1:9061"
DEFAULT_L1_INDEXER_BASE = "https://apiprd.ordx.market/btc/testnet"
DEFAULT_L2_INDEXER_BASE = "https://apiprd.ordx.market/satsnet/testnet"


def _load_request() -> dict:
    if len(sys.argv) > 1:
        return json.loads(sys.argv[1])
    if not sys.stdin.isatty():
        return json.load(sys.stdin)
    return {"op": ""}


def _base_url() -> str:
    return os.environ.get("STP_TRANSCEND_RPC_URL", DEFAULT_RPC_URL).rstrip("/")


def _protocol_base_url(req: Optional[dict] = None) -> str:
    if req:
        server = req.get("server") or req.get("core_node") or req.get("url")
        if server:
            return str(server).rstrip("/")
    return os.environ.get("STP_TRANSCEND_PROTOCOL_URL", _base_url()).rstrip("/")


def _request_json(method: str, path: str, body: Optional[dict] = None) -> dict:
    return _request_json_at(_base_url(), method, path, body)


def _request_json_at(base_url: str, method: str, path: str, body: Optional[dict] = None) -> dict:
    url = base_url + path
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        headers["content-type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        raise RuntimeError(f"transcend RPC request failed: {e}") from e
    if not raw:
        return {}
    return json.loads(raw)


def _get_json_url(url: str) -> dict:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        return {
            "ok": False,
            "error": str(e),
        }
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "ok": True,
            "raw": raw,
        }


def _ok(operation: str, result: dict, extra: Optional[dict] = None) -> dict:
    out = {
        "ok": True,
        "operation": operation,
        "adapter": "transcend-rpc",
        "result": result,
    }
    if extra:
        out.update(extra)
    return out


def _fail(operation: str, code: str, message: str, extra: Optional[dict] = None) -> dict:
    out = {
        "ok": False,
        "operation": operation,
        "adapter": "transcend-rpc",
        "error": {
            "code": code,
            "message": message,
        },
        "error_code": code,
        "message": message,
    }
    if extra:
        out.update(extra)
    return out


def _normalize_response(operation: str, result: dict, extra: Optional[dict] = None) -> dict:
    code = result.get("code", result.get("Code", 0))
    if code not in (0, "0", None):
        msg = str(result.get("msg") or result.get("Msg") or result)
        if msg == "server panic":
            return _fail(operation, "CORE_NODE_SERVER_PANIC", msg, extra)
        return _fail(operation, "TRANSCEND_RPC_ERROR", msg, extra)
    return _ok(operation, result, extra)


def _amount(req: dict, default: str = "") -> str:
    value = req.get("amount", req.get("amount_sats", default))
    return str(value)


def _fee_rate(req: dict) -> int:
    value = req.get("fee_rate", req.get("feeRate", 1))
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1


def _channel(req: dict) -> str:
    return str(req.get("channel_id") or req.get("channel") or req.get("channel_point") or "")


def _default_channel_id() -> str:
    status = _request_json("GET", "/info/channels")
    channel_ids = status.get("channels", [])
    if isinstance(channel_ids, list) and len(channel_ids) == 1:
        return str(channel_ids[0])
    return ""


def _channel_or_default(req: dict) -> str:
    return _channel(req) or _default_channel_id()


def _asset(req: dict) -> str:
    value = str(req.get("asset", req.get("assetName", ""))).strip()
    if value.lower() in {"sat", "sats", "plain", "plain:sat", "plain:sats", "btc"}:
        return "::"
    return value


def _strings(value) -> list:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return []


def _tx_ids(req: dict) -> list:
    values = _strings(req.get("tx_ids", req.get("txids", [])))
    single = req.get("tx_id", req.get("txid", ""))
    if single:
        values.append(str(single))
    return list(dict.fromkeys(values))


def _l1_indexer_base() -> str:
    return os.environ.get("STP_L1_INDEXER_BASE", DEFAULT_L1_INDEXER_BASE).rstrip("/")


def _l2_indexer_base() -> str:
    return os.environ.get("STP_L2_INDEXER_BASE", DEFAULT_L2_INDEXER_BASE).rstrip("/")


def _query_tx_status(txid: str, layer: str) -> dict:
    base = _l2_indexer_base() if layer == "satoshinet" else _l1_indexer_base()
    result = _get_json_url(base + "/btc/tx/simpleinfo/" + urllib.parse.quote(txid, safe=""))
    status = {
        "txid": txid,
        "layer": layer,
        "visible": False,
        "confirmed": False,
    }
    if result.get("ok") is False:
        status["error"] = result.get("error")
        return status
    if result.get("code") not in (0, "0", None):
        status["error"] = result.get("msg") or str(result)
        return status
    data = result.get("data") or {}
    status.update({
        "visible": True,
        "confirmations": data.get("confirmations", 0),
        "confirmed": int(data.get("confirmations") or 0) > 0,
        "block_height": data.get("block_height", data.get("blockHeight", 0)),
        "block_time": data.get("block_time", data.get("blockTime", 0)),
        "raw": data,
    })
    return status


def _reservation_id(req: dict) -> str:
    value = req.get("reservation_id", req.get("resv_id", req.get("transaction_id", "")))
    return str(value) if value is not None else ""


def _parse_reservation_payload(reservation: dict) -> dict:
    if not isinstance(reservation, dict):
        return reservation
    raw = reservation.get("resvs")
    if not isinstance(raw, str) or not raw:
        return reservation
    try:
        reservation["reservation_data"] = json.loads(raw)
    except json.JSONDecodeError:
        reservation["reservation_raw"] = raw
    return reservation


def _transaction_status(req: dict) -> dict:
    result = {
        "transaction_id": req.get("transaction_id", ""),
        "reservation_id": _reservation_id(req),
        "tx_statuses": [],
    }
    resv_id = _reservation_id(req)
    if resv_id and resv_id.isdigit():
        try:
            reservation = _request_json("GET", "/info/resv/" + urllib.parse.quote(resv_id, safe=""))
            result["reservation"] = _parse_reservation_payload(reservation)
        except Exception as e:
            result["reservation_error"] = str(e)
    layer = str(req.get("layer", req.get("network", "btc_l1")))
    normalized_layer = "satoshinet" if layer in {"satoshinet", "satsnet", "l2"} else "btc_l1"
    for txid in _tx_ids(req):
        result["tx_statuses"].append(_query_tx_status(txid, normalized_layer))
    if result["tx_statuses"]:
        if all(item.get("confirmed") for item in result["tx_statuses"]):
            result["status"] = "CONFIRMED"
        elif any(item.get("visible") for item in result["tx_statuses"]):
            result["status"] = "BROADCASTED"
        else:
            result["status"] = "PENDING_OR_NOT_VISIBLE"
    elif "reservation" in result:
        result["status"] = "RESERVATION_TRACKED"
    else:
        result["status"] = "MISSING_TRANSACTION_REFERENCE"
    result["next_check"] = "poll stp.transaction until all related txids are confirmed and reservation reaches a terminal state"
    return result


def _tx_present(tx) -> bool:
    return isinstance(tx, dict) and bool(tx.get("TxIn") or tx.get("TxOut"))


def _channel_payload(channel_result: dict) -> dict:
    channel = channel_result.get("channel")
    if isinstance(channel, dict):
        return channel
    return channel_result


def _fetch_channel(req: dict) -> dict:
    channel_id = _channel(req)
    if not channel_id:
        status = _request_json("GET", "/info/channels")
        channel_ids = status.get("channels", [])
        if isinstance(channel_ids, list) and channel_ids:
            channel_id = str(channel_ids[0])
    if not channel_id:
        raise RuntimeError("channel_id is required")
    return _channel_payload(_request_json("GET", "/info/channel/" + urllib.parse.quote(channel_id, safe="")))


def _punish_coverage(channel_id: str) -> dict:
    if not channel_id:
        return {
            "status": "PUNISH_COVERAGE_UNKNOWN",
            "message": "missing channel id",
        }
    try:
        result = _request_json("GET", "/safety/punish/" + urllib.parse.quote(channel_id, safe=""))
    except Exception as e:
        return {
            "status": "PUNISH_COVERAGE_UNKNOWN",
            "message": str(e),
        }
    if result.get("code") not in (0, "0", None):
        return {
            "status": "PUNISH_COVERAGE_UNKNOWN",
            "message": result.get("msg") or str(result),
            "raw": result,
        }
    revoked = result.get("revoked_commitments") or []
    if not revoked:
        return {
            "status": "NO_REVOKED_REMOTE_STATE",
            "raw": result,
        }
    covered = all(item.get("verified") and item.get("broadcastable") for item in revoked if isinstance(item, dict))
    return {
        "status": "COVERED" if covered else "PUNISH_COVERAGE_MISSING",
        "revoked_commitments": revoked,
        "raw": result,
    }


def _asset_key(asset: dict) -> str:
    name = asset.get("Name") or {}
    protocol = name.get("Protocol") or ""
    typ = name.get("Type") or ""
    ticker = name.get("Ticker") or ""
    return f"{protocol}:{typ}:{ticker}"


def _add_amount(summary: dict, key: str, amount) -> None:
    try:
        value = int(str(amount))
    except (TypeError, ValueError):
        value = 0
    summary[key] = str(int(summary.get(key, "0")) + value)


def _l2_asset_summary(utxos: list) -> dict:
    summary = {}
    if not isinstance(utxos, list):
        return summary
    for utxo in utxos:
        out_value = (utxo or {}).get("OutValue") or {}
        assets = out_value.get("Assets") or []
        if assets:
            for asset in assets:
                if not isinstance(asset, dict):
                    continue
                amount = (asset.get("Amount") or {}).get("Value")
                _add_amount(summary, _asset_key(asset), amount)
        else:
            _add_amount(summary, "::", out_value.get("Value", 0))
    return summary


def _derive_safety_snapshot(channel: dict) -> dict:
    local_commitment = channel.get("localCommitment")
    remote_commitment = channel.get("remoteCommitment")
    local_ok = _tx_present(local_commitment)
    remote_ok = _tx_present(remote_commitment)
    commit_height = channel.get("commitHeight")
    status_code = channel.get("status")
    safety_status = "READY_SAFE" if local_ok and remote_ok and status_code == 16 else "READY_DEGRADED"
    channel_id = channel.get("channelId") or channel.get("address")
    return {
        "channel_id": channel_id,
        "channel_address": channel.get("address"),
        "chan_point": channel.get("chanPoint"),
        "status": safety_status,
        "raw_status": status_code,
        "commit_height": commit_height,
        "csv_delay": channel.get("csvDelay"),
        "capacity": channel.get("capacity"),
        "local_commitment_present": local_ok,
        "remote_commitment_present": remote_ok,
        "local_balance": channel.get("localbalanceL1", []),
        "remote_balance": channel.get("remotebalanceL1", []),
        "l2_spendable_balance": _l2_asset_summary(channel.get("UtxosL2", [])),
        "l2_pending_balance": _l2_asset_summary(channel.get("pendingUtxosL2", [])),
        "l2_spendable_utxo_count": len(channel.get("UtxosL2", []) or []),
        "l2_pending_utxo_count": len(channel.get("pendingUtxosL2", []) or []),
        "merkle_roots": {
            "static": channel.get("staticMerkleRoot"),
            "local_assets": channel.get("localAssetMerkleRoot"),
            "remote_assets": channel.get("remoteAssetMerkleRoot"),
        },
        "punish_coverage": _punish_coverage(channel_id),
        "state_backup": {
            "status": "UNKNOWN",
            "message": "The current transcend RPC status endpoint does not expose backup metadata.",
        },
    }


def _post(operation: str, path: str, body: dict, extra: Optional[dict] = None) -> dict:
    result = _request_json("POST", path, body)
    return _normalize_response(operation, result, extra)


def _post_protocol(operation: str, req: dict, path: str, body: dict, extra: Optional[dict] = None) -> dict:
    result = _request_json_at(_protocol_base_url(req), "POST", path, body)
    out = _normalize_response(operation, result, extra)
    out["protocol_url"] = _protocol_base_url(req)
    return out


def handle(req: dict) -> dict:
    op = req.get("op") or req.get("operation")
    chain = req.get("chain", "testnet")
    extra = {"chain": chain}

    if chain != "testnet":
        return _fail(op, "MAINNET_REQUIRES_PWA", "Use SAT20 PWA Wallet approval for mainnet STP operations.", extra)

    try:
        if op == "wallet.create":
            return _post(op, "/wallet/create", {"password": req.get("password", "")}, extra)
        if op == "wallet.import":
            return _post(op, "/wallet/import", {"password": req.get("password", ""), "mnemonic": req.get("mnemonic", "")}, extra)
        if op == "wallet.unlock":
            return _post(op, "/wallet/unlock", {"password": req.get("password", "")}, extra)

        if op == "stp.status":
            status = {"rpc_url": _base_url()}
            failures = 0
            for name, path in (("channels", "/info/channels"), ("reservations", "/info/resvs")):
                try:
                    status[name] = _request_json("GET", path)
                except Exception as e:
                    failures += 1
                    status[name] = {"error": str(e)}
            if failures == 2:
                return _fail(op, "TRANSCEND_RPC_UNAVAILABLE", "No transcend RPC status endpoint is reachable.", extra)
            channel_ids = status.get("channels", {}).get("channels", [])
            if isinstance(channel_ids, list):
                status["channel_details"] = []
                for channel_id in channel_ids:
                    try:
                        status["channel_details"].append(_request_json("GET", "/info/channel/" + urllib.parse.quote(str(channel_id), safe="")))
                    except Exception as e:
                        status["channel_details"].append({"channel": str(channel_id), "error": str(e)})
            reservations = status.get("reservations", {}).get("resvs", [])
            if isinstance(reservations, list):
                status["reservation_details"] = []
                for item in reservations:
                    resv_id = item.get("id") if isinstance(item, dict) else None
                    if resv_id is None:
                        continue
                    try:
                        status["reservation_details"].append(_request_json("GET", "/info/resv/" + urllib.parse.quote(str(resv_id), safe="")))
                    except Exception as e:
                        status["reservation_details"].append({"id": resv_id, "error": str(e)})
            return _ok(op, status, extra)

        if op == "stp.open":
            result = _post(op, "/channel/open", {
                "feeRate": _fee_rate(req),
                "amt": int(req.get("amount_sats", req.get("amount", 0))),
                "utxos": _strings(req.get("utxos")),
                "memo": req.get("memo", ""),
            }, extra)
            if result.get("ok") and isinstance(result.get("result"), dict):
                result["channel_id"] = result["result"].get("channel")
            return result

        if op == "stp.close":
            return _post(op, "/channel/close", {
                "channel": _channel(req),
                "feeRate": _fee_rate(req),
                "force": bool(req.get("force", False)),
            }, extra)

        if op == "stp.splicing_in":
            return _post(op, "/channel/splicingin", {
                "channel": _channel(req),
                "feeRate": _fee_rate(req),
                "assetName": _asset(req),
                "amt": _amount(req),
                "splicingInUtxos": _strings(req.get("utxos")),
                "feeUtxos": _strings(req.get("fees", req.get("fee_utxos"))),
                "reason": req.get("reason", ""),
            }, extra)

        if op == "stp.splicing_out":
            return _post(op, "/channel/splicingout", {
                "channel": _channel(req),
                "feeRate": _fee_rate(req),
                "assetName": _asset(req),
                "amt": _amount(req),
                "address": req.get("to", req.get("address", "")),
                "feeUtxos": _strings(req.get("fees", req.get("fee_utxos"))),
                "reason": req.get("reason", ""),
                "more": req.get("more", ""),
            }, extra)

        if op == "stp.expand":
            return _post(op, "/channel/expand", {
                "channel": _channel_or_default(req),
                "assetName": _asset(req),
                "expandingUtxos": _strings(req.get("utxos", req.get("expanding_utxos"))),
                "network": req.get("network", req.get("layer", "")),
                "reason": req.get("reason", ""),
            }, extra)

        if op == "stp.expand_all":
            return _post(op, "/channel/expandall", {
                "channel": _channel(req),
                "assetName": _asset(req),
                "network": req.get("network", req.get("layer", "")),
            }, extra)

        if op == "stp.reopen":
            return _post(op, "/rebuild/channel", {
                "channel": _channel(req),
                "method": "reopen",
            }, extra)

        if op == "stp.rebuild":
            return _post(op, "/rebuild/channel", {
                "channel": _channel(req),
                "method": "rebuild",
                "utxo": req.get("utxo", req.get("funding_utxo", "")),
            }, extra)

        if op == "stp.restore":
            return _post(op, "/rebuild/channel", {
                "channel": _channel(req),
                "method": "restore",
            }, extra)

        if op == "stp.clean_channel":
            return _post(op, "/clean/channel", {
                "channel": _channel(req),
            }, extra)

        if op == "stp.unlock":
            return _post(op, "/channel/unlock", {
                "channel": _channel(req),
                "assetName": _asset(req),
                "amt": _amount(req),
                "feeUtxos": _strings(req.get("fee_utxos")),
                "address": req.get("to", req.get("address", "")),
            }, extra)

        if op == "stp.lock":
            return _post(op, "/channel/lock", {
                "channel": _channel(req),
                "assetName": _asset(req),
                "amt": _amount(req),
                "lockUtxos": _strings(req.get("utxos", req.get("lock_utxos"))),
                "feeUtxos": _strings(req.get("fee_utxos")),
            }, extra)

        if op == "stp.lock_with_expand":
            return _post(op, "/channel/lockwithexpand", {
                "channel": _channel(req),
                "assetName": _asset(req),
                "amt": _amount(req),
                "feeRate": _fee_rate(req),
            }, extra)

        if op == "stp.safety_snapshot":
            channel = _fetch_channel(req)
            return _ok(op, _derive_safety_snapshot(channel), extra)

        if op == "stp.commitment_export":
            channel = _fetch_channel(req)
            result = {
                "channel_id": channel.get("channelId") or channel.get("address"),
                "chan_point": channel.get("chanPoint"),
                "commit_height": channel.get("commitHeight"),
                "csv_delay": channel.get("csvDelay"),
                "local_commitment": channel.get("localCommitment"),
                "remote_commitment": channel.get("remoteCommitment"),
                "local_deanchor_tx": channel.get("localDeAnchorTx"),
                "remote_deanchor_tx": channel.get("remoteDeAnchorTx"),
                "local_balance": channel.get("localbalanceL1", []),
                "remote_balance": channel.get("remotebalanceL1", []),
                "merkle_roots": {
                    "static": channel.get("staticMerkleRoot"),
                    "local_assets": channel.get("localAssetMerkleRoot"),
                    "remote_assets": channel.get("remoteAssetMerkleRoot"),
                },
            }
            return _ok(op, result, extra)

        if op == "stp.punish_status":
            channel_id = _channel(req)
            if not channel_id:
                return _fail(op, "CHANNEL_ID_REQUIRED", "channel_id is required.", extra)
            result = _request_json("GET", "/safety/punish/" + urllib.parse.quote(channel_id, safe=""))
            return _normalize_response(op, result, extra)

        if op == "stp.punish_build":
            return _post(op, "/safety/punish/build", {
                "channel_id": _channel(req),
                "commit_txid": req.get("commit_txid", req.get("commitTxId", "")),
            }, extra)

        if op == "stp.punish_broadcast":
            return _post(op, "/safety/punish/broadcast", {
                "channel_id": _channel(req),
                "commit_txid": req.get("commit_txid", req.get("commitTxId", "")),
            }, extra)

        if op == "stp.force_close_plan":
            return _post(op, "/safety/force-close/plan", {
                "channel_id": _channel(req),
            }, extra)

        if op in {"stp.sweep_build"}:
            return _fail(op, "STP_RUNTIME_INTERFACE_REQUIRED", "The transcend runtime must expose the corresponding /safety endpoint before this adapter can execute the operation.", extra)

        if op == "stp.test_retain_server_commitment":
            return _post_protocol(op, req, "/test/fault/retain-server-commitment", {
                "channel_id": _channel(req),
                "commit_height": int(req.get("commit_height", 0)),
                "label": req.get("label", ""),
                "confirm_unsafe_test_only": bool(req.get("confirm_unsafe_test_only", False)),
            }, extra)

        if op == "stp.test_broadcast_retained_server_commitment":
            return _post_protocol(op, req, "/test/fault/broadcast-server-commitment", {
                "channel_id": _channel(req),
                "commit_height": int(req.get("commit_height", 0)),
                "fee_rate": _fee_rate(req),
                "confirm_unsafe_test_only": bool(req.get("confirm_unsafe_test_only", False)),
            }, extra)

        if op == "stp.transaction":
            return _ok(op, _transaction_status(req), extra)

        if op in {"wallet.status", "wallet.transaction"}:
            return _fail(op, "NOT_IMPLEMENTED", "This transcend RPC adapter does not implement this query yet.", extra)

        return _fail(op, "UNSUPPORTED_OPERATION", f"Unsupported operation: {op}", extra)
    except Exception as e:
        return _fail(op, "TRANSCEND_RPC_UNAVAILABLE", str(e), extra)


def main() -> None:
    print(json.dumps(handle(_load_request()), separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()
