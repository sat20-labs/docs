Locking and Unlocking of Satoshis
====

Locking and unlocking satoshis are necessary conditions for assets to move from layer-1 to layer-2.
We utilize Lightning Network's channel technology to lock satoshis in a multi-signature address and enter the Lightning channel.
In the Lightning Network, the Revocable Sequence Maturity Contract (RSMC) is a contract type used to ensure the security and reliability of Lightning Network channels.

RSMC is a contract based on time locks, allowing participants to revoke or close Lightning Network channels under specific conditions. Its design purpose is to prevent fraudulent behavior and malicious operations and ensure the security of transactions.

We use RSMC contracts to ensure the security of user funds.