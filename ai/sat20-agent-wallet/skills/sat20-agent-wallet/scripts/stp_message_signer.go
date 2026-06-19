package main

import (
	"encoding/base64"
	"fmt"
	"io"
	"os"

	"github.com/btcsuite/btcd/chaincfg"
	"github.com/sat20-labs/sat20wallet/sdk/wallet"
)

func main() {
	mnemonic := os.Getenv("STP_WALLET_MNEMONIC")
	if mnemonic == "" {
		fmt.Fprintln(os.Stderr, "STP_WALLET_MNEMONIC is required")
		os.Exit(2)
	}
	password := os.Getenv("STP_WALLET_PASSWORD")
	msg, err := io.ReadAll(os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	w := wallet.NewInternalWalletWithMnemonic(mnemonic, password, &chaincfg.TestNet4Params)
	if w == nil {
		fmt.Fprintln(os.Stderr, "failed to create wallet from mnemonic")
		os.Exit(2)
	}
	sig, err := w.SignMessage(msg)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	fmt.Print(base64.StdEncoding.EncodeToString(sig))
}
