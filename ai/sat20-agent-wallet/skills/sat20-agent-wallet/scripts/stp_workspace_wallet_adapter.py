#!/usr/bin/env python3
"""SAT20 workspace development adapter for STP wallet bootstrap.

This adapter is for local testnet development. It creates a temporary Go test
inside sat20wallet/sdk, calls the existing wallet implementation, parses the
result, and removes the temporary file.

Production wallet creation should be handled by SAT20 PWA Wallet adapter.
"""

import json
import os
import pathlib
import re
import subprocess
import sys
import textwrap
import fcntl


TEST_FILE = "wallet/agent_skill_wallet_adapter_test.go"
LOCK_FILE = "/tmp/stp_workspace_wallet_adapter.lock"


GO_TEST = r'''
package wallet

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	indexer "github.com/sat20-labs/indexer/common"
	"github.com/sat20-labs/sat20wallet/sdk/common"
	sbtcec "github.com/sat20-labs/satoshinet/btcec"
)

type agentRequest struct {
	Op             string `json:"op"`
	Chain          string `json:"chain"`
	Mnemonic       string `json:"mnemonic"`
	SourceMnemonic string `json:"source_mnemonic"`
	Layer          string `json:"layer"`
	Asset          string `json:"asset"`
	Amount         string `json:"amount"`
	To             string `json:"to"`
	FeeRate        int64  `json:"fee_rate"`
	TransactionID  string `json:"transaction_id"`
}

func loadAgentRequest(t *testing.T) agentRequest {
	raw := os.Getenv("AGENT_WALLET_REQUEST")
	if raw == "" {
		t.Fatal("AGENT_WALLET_REQUEST is empty")
	}
	var req agentRequest
	if err := json.Unmarshal([]byte(raw), &req); err != nil {
		t.Fatal(err)
	}
	if req.Chain == "" {
		req.Chain = "testnet"
	}
	return req
}

func emitAgent(t *testing.T, out map[string]any) {
	b, err := json.Marshal(out)
	if err != nil {
		t.Fatal(err)
	}
	fmt.Printf("\nAGENT_WALLET_JSON_BEGIN%sAGENT_WALLET_JSON_END\n", b)
}

func satsnetAddress(t *testing.T, w *InternalWallet) string {
	pubKey := w.GetPaymentPubKey().SerializeCompressed()
	satsnetPubKey, err := sbtcec.ParsePubKey(pubKey)
	if err != nil {
		t.Fatal(err)
	}
	return PublicKeyToP2TRAddress_SatsNet(satsnetPubKey)
}

func normalizeAsset(asset string) string {
	switch asset {
	case "", "plain:sat", "sat", "sats", "btc":
		return indexer.ASSET_PLAIN_SAT.String()
	default:
		return asset
	}
}

func l1PlainBalance(mgr *Manager, address string) (int64, int, string) {
	utxos, err := mgr.l1IndexerClient.GetUtxosWithAddress(address)
	if err != nil {
		return 0, 0, err.Error()
	}
	total := int64(0)
	for _, txout := range utxos {
		total += txout.Value
	}
	return total, len(utxos), ""
}

func assetSummary(mgr *Manager, address string, satsnet bool) []map[string]any {
	var summary any
	if satsnet {
		summary = mgr.l2IndexerClient.GetAssetSummaryWithAddress(address)
	} else {
		summary = mgr.l1IndexerClient.GetAssetSummaryWithAddress(address)
	}
	result := []map[string]any{}
	switch s := summary.(type) {
	case nil:
		return result
	default:
		_ = s
	}
	if satsnet {
		assets := mgr.l2IndexerClient.GetAssetSummaryWithAddress(address)
		if assets == nil {
			return result
		}
		for _, item := range assets.Data {
			result = append(result, map[string]any{
				"name": item.Name.String(), "amount": item.Amount.String(), "binding_sat": item.BindingSat,
			})
		}
		return result
	}
	assets := mgr.l1IndexerClient.GetAssetSummaryWithAddress(address)
	if assets == nil {
		return result
	}
	for _, item := range assets.Data {
		result = append(result, map[string]any{
			"name": item.Name.String(), "amount": item.Amount.String(), "binding_sat": item.BindingSat,
		})
	}
	return result
}

func newAgentManager(t *testing.T, mnemonic string) (*Manager, func()) {
	if mnemonic == "" {
		t.Fatal("mnemonic is required")
	}
	dbPath := filepath.Join(os.TempDir(), fmt.Sprintf("agent-skill-wallet-%d", time.Now().UnixNano()))
	cfg := &common.Config{
		Env:   "test",
		Chain: "testnet",
		Peers: []string{
			"b@025fb789035bc2f0c74384503401222e53f72eefdebf0886517ff26ac7985f52ad@https://apiprd.sat20.org/stp/testnet",
			"s@0367f26af23dc40fdad06752c38264fe621b7bbafb1d41ab436b87ded192f1336e@https://apiprd.ordx.market/stp/testnet",
		},
		IndexerL1: &common.Indexer{
			Scheme: "https",
			Host:   "apiprd.sat20.org",
			Proxy:  "btc/testnet",
		},
		IndexerL2: &common.Indexer{
			Scheme: "https",
			Host:   "apiprd.sat20.org",
			Proxy:  "satsnet/testnet",
		},
		Log:  "info",
		DB:   dbPath,
		Mode: CLIENT_NODE,
	}
	db := NewKVDB(cfg.DB)
	if db == nil {
		t.Fatal("NewKVDB failed")
	}
	mgr := NewManager(cfg, db)
	if mgr == nil {
		t.Fatal("NewManager failed")
	}
	if _, err := mgr.ImportWallet(mnemonic, "123456"); err != nil {
		t.Fatal(err)
	}
	return mgr, func() {
		mgr.Close()
		_ = os.RemoveAll(dbPath)
	}
}

func TestAgentSkillWalletAdapter(t *testing.T) {
	req := loadAgentRequest(t)
	if req.Chain != "testnet" {
		emitAgent(t, map[string]any{
			"ok": false, "operation": req.Op, "chain": req.Chain,
			"error_code": "MAINNET_REQUIRES_PWA",
			"message": "This workspace adapter only supports testnet. Use SAT20 PWA Wallet adapter for mainnet.",
		})
		return
	}

	switch req.Op {
	case "wallet.create":
		createWallet(t)
	case "wallet.status":
		mnemonic := req.Mnemonic
		if mnemonic == "" {
			mnemonic = req.SourceMnemonic
		}
		mgr, cleanup := newAgentManager(t, mnemonic)
		defer cleanup()
		w := mgr.GetWallet().(*InternalWallet)
		assetName := normalizeAsset(req.Asset)
		if assetName == "" {
			assetName = indexer.ASSET_PLAIN_SAT.String()
		}
		balance := mgr.GetAssetBalance(w.GetAddress(), indexer.NewAssetNameFromString(assetName))
		balanceText := "0"
		if balance != nil {
			balanceText = balance.String()
		}
		plainTotal, plainUtxos, plainErr := l1PlainBalance(mgr, w.GetAddress())
		emitAgent(t, map[string]any{
			"ok": true, "operation": "wallet.status", "adapter": "sat20-workspace-dev", "chain": "testnet",
			"wallet_id": w.GetId(), "l1_address": w.GetAddress(), "satsnet_address": satsnetAddress(t, w),
			"payment_pubkey": hex.EncodeToString(w.GetPaymentPubKey().SerializeCompressed()),
			"asset": assetName, "l1_balance": balanceText,
			"l1_plain_sats": plainTotal, "l1_plain_utxo_count": plainUtxos, "l1_plain_query_error": plainErr,
			"l1_assets": assetSummary(mgr, w.GetAddress(), false),
			"l2_assets": assetSummary(mgr, w.GetAddress(), true),
		})
	case "wallet.send_assets":
		if req.Layer != "" && req.Layer != "btc_l1" {
			emitAgent(t, map[string]any{
				"ok": false, "operation": req.Op, "chain": req.Chain, "layer": req.Layer,
				"error_code": "PWA_ADAPTER_REQUIRED",
				"message": "This workspace adapter only sends BTC L1 testnet assets. Use PWA adapter for SatoshiNet sends.",
			})
			return
		}
		mgr, cleanup := newAgentManager(t, req.SourceMnemonic)
		defer cleanup()
		w := mgr.GetWallet().(*InternalWallet)
		assetName := normalizeAsset(req.Asset)
		before := mgr.GetAssetBalance(w.GetAddress(), indexer.NewAssetNameFromString(assetName))
		beforeText := "0"
		if before != nil {
			beforeText = before.String()
		}
		plainTotal, plainUtxos, plainErr := l1PlainBalance(mgr, w.GetAddress())
		if plainErr != "" {
			emitAgent(t, map[string]any{
				"ok": false, "operation": req.Op, "chain": "testnet", "layer": "btc_l1",
				"from": w.GetAddress(), "to": req.To, "asset": assetName, "amount": req.Amount,
				"error_code": "SOURCE_BALANCE_QUERY_FAILED", "message": plainErr,
			})
			return
		}
		tx, err := mgr.SendAssets(req.To, assetName, req.Amount, req.FeeRate, nil)
		if err != nil {
			emitAgent(t, map[string]any{
				"ok": false, "operation": req.Op, "chain": "testnet", "layer": "btc_l1",
				"from": w.GetAddress(), "to": req.To, "asset": assetName, "amount": req.Amount,
				"source_l1_balance": beforeText, "source_l1_plain_sats": plainTotal, "source_l1_plain_utxo_count": plainUtxos,
				"error_code": "SEND_ASSETS_FAILED", "message": err.Error(),
			})
			return
		}
		emitAgent(t, map[string]any{
			"ok": true, "operation": "wallet.send_assets", "adapter": "sat20-workspace-dev", "chain": "testnet", "layer": "btc_l1",
			"from": w.GetAddress(), "to": req.To, "asset": assetName, "amount": req.Amount,
			"source_l1_balance_before": beforeText, "source_l1_plain_sats_before": plainTotal, "source_l1_plain_utxo_count_before": plainUtxos,
			"tx_ids": []string{tx.TxID()}, "transaction_id": tx.TxID(),
			"status": "BROADCASTED", "next_check": "poll wallet.transaction or BTC testnet4 indexer",
		})
	case "wallet.transaction":
		mnemonic := req.Mnemonic
		if mnemonic == "" {
			mnemonic = req.SourceMnemonic
		}
		mgr, cleanup := newAgentManager(t, mnemonic)
		defer cleanup()
		if req.TransactionID == "" {
			emitAgent(t, map[string]any{
				"ok": false, "operation": req.Op, "chain": req.Chain,
				"error_code": "MISSING_TRANSACTION_ID", "message": "transaction_id is required",
			})
			return
		}
		info, err := mgr.l1IndexerClient.GetTxInfo(req.TransactionID)
		if err != nil {
			emitAgent(t, map[string]any{
				"ok": false, "operation": req.Op, "chain": "testnet", "layer": "btc_l1",
				"transaction_id": req.TransactionID, "error_code": "TX_QUERY_FAILED", "message": err.Error(),
				"status": "BROADCASTED_OR_PENDING_INDEXER",
			})
			return
		}
		height, _ := mgr.l1IndexerClient.GetTxHeight(req.TransactionID)
		confirmed := mgr.l1IndexerClient.IsTxConfirmed(req.TransactionID)
		status := "BROADCASTED"
		if confirmed {
			status = "CONFIRMED"
		}
		emitAgent(t, map[string]any{
			"ok": true, "operation": "wallet.transaction", "adapter": "sat20-workspace-dev", "chain": "testnet", "layer": "btc_l1",
			"transaction_id": req.TransactionID, "tx_info": info, "height": height, "confirmed": confirmed,
			"status": status,
		})
	default:
		emitAgent(t, map[string]any{
			"ok": false, "operation": req.Op, "chain": req.Chain,
			"error_code": "UNSUPPORTED_OPERATION",
			"message": "This development adapter supports wallet.create, wallet.status, wallet.transaction, and BTC L1 wallet.send_assets.",
		})
	}
}

func createWallet(t *testing.T) {
	w, mnemonic, err := NewInteralWallet(GetChainParam())
	if err != nil {
		t.Fatal(err)
	}
	pubKey := w.GetPaymentPubKey().SerializeCompressed()
	out := map[string]any{
		"ok":              true,
		"operation":       "wallet.create",
		"adapter":         "sat20-workspace-dev",
		"chain":           "testnet",
		"wallet_type":     "sat20-pwa-compatible",
		"mnemonic":        mnemonic,
		"wallet_id":       w.GetId(),
		"l1_address":      w.GetAddress(),
		"satsnet_address": satsnetAddress(t, w),
		"payment_pubkey":  hex.EncodeToString(pubKey),
		"next_step":       "Import this mnemonic into SAT20 PWA Wallet, then connect the PWA STP adapter.",
	}
	emitAgent(t, out)
}
'''


def _load_request() -> dict:
    if len(sys.argv) > 1:
        return json.loads(sys.argv[1])
    if not sys.stdin.isatty():
        return json.load(sys.stdin)
    raise SystemExit(json.dumps({"ok": False, "error_code": "MISSING_REQUEST"}))


def _find_sdk_dir() -> pathlib.Path:
    env = os.environ.get("SAT20_WORKSPACE")
    candidates = []
    if env:
        candidates.append(pathlib.Path(env).expanduser())
    cwd = pathlib.Path.cwd()
    candidates.extend([cwd, *cwd.parents])

    for base in candidates:
        direct = base / "sat20wallet" / "sdk"
        if (direct / "go.mod").exists() and (direct / "wallet").is_dir():
            return direct
        if base.name == "sdk" and (base / "go.mod").exists() and (base / "wallet").is_dir():
            return base
    raise RuntimeError("cannot locate sat20wallet/sdk; set SAT20_WORKSPACE=/path/to/github")


def _run_wallet_adapter(request: dict) -> dict:
    chain = request.get("chain", "testnet")
    if chain != "testnet":
        return {
            "ok": False,
            "operation": request.get("op"),
            "chain": chain,
            "error_code": "MAINNET_WALLET_CREATE_REQUIRES_PWA",
            "message": "Use SAT20 PWA Wallet adapter and explicit user approval for mainnet wallet creation.",
        }

    with open(LOCK_FILE, "w", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        sdk_dir = _find_sdk_dir()
        test_path = sdk_dir / TEST_FILE
        try:
            test_path.unlink()
        except FileNotFoundError:
            pass

        env = os.environ.copy()
        env["AGENT_WALLET_REQUEST"] = json.dumps(request, separators=(",", ":"), ensure_ascii=False)
        test_path.write_text(textwrap.dedent(GO_TEST).lstrip(), encoding="utf-8")
        try:
            proc = subprocess.run(
                ["go", "test", "./wallet", "-run", "^TestAgentSkillWalletAdapter$", "-count=1", "-v"],
                cwd=str(sdk_dir),
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        finally:
            try:
                test_path.unlink()
            except FileNotFoundError:
                pass

    if proc.returncode != 0:
        return {
            "ok": False,
            "operation": request.get("op"),
            "chain": chain,
            "error_code": "GO_WALLET_CREATE_FAILED",
            "message": proc.stderr.strip() or proc.stdout.strip(),
        }

    match = re.search(r"AGENT_WALLET_JSON_BEGIN(.*?)AGENT_WALLET_JSON_END", proc.stdout, re.S)
    if not match:
        return {
            "ok": False,
            "operation": request.get("op"),
            "chain": chain,
            "error_code": "WALLET_JSON_NOT_FOUND",
            "message": proc.stdout,
        }
    return json.loads(match.group(1))


def main() -> None:
    request = _load_request()
    op = request.get("op")
    if op in {"wallet.create", "wallet.status", "wallet.send_assets", "wallet.transaction"}:
        response = _run_wallet_adapter(request)
    elif op in {"wallet.import", "wallet.export_mnemonic", "wallet.change_password"}:
        response = {
            "ok": False,
            "operation": op,
            "chain": request.get("chain", "testnet"),
            "error_code": "PWA_ADAPTER_REQUIRED",
            "message": "Use SAT20 PWA Wallet adapter for persistent wallet import/export/password operations.",
        }
    elif isinstance(op, str) and op.startswith("stp."):
        response = {
            "ok": False,
            "operation": op,
            "chain": request.get("chain", "testnet"),
            "error": {
                "code": "PWA_ADAPTER_REQUIRED",
                "message": "Use SAT20 PWA Wallet adapter or a transcend-backed STP runtime adapter for channel operations.",
            },
            "error_code": "PWA_ADAPTER_REQUIRED",
            "message": "Use SAT20 PWA Wallet adapter or a transcend-backed STP runtime adapter for channel operations.",
        }
    else:
        response = {
            "ok": False,
            "operation": op,
            "chain": request.get("chain", "testnet"),
            "error_code": "UNSUPPORTED_OPERATION",
            "message": "This development adapter supports wallet.create, wallet.status, wallet.transaction, and BTC L1 wallet.send_assets.",
        }
    print(json.dumps(response, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()
