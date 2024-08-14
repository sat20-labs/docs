SAT20 Protocol
=========

SAT20 is a "Satoshi Standard" protocol for issuing and circulating BTC native assets, with its core feature being the binding of assets to satoshis and their free movement alongside satoshis.
The SAT20 protocol consists of two components: the asset issuance protocol and the asset circulation protocol.

Asset Issuance Protocol (ORDX)
----
The SAT20 asset issuance protocol is an enhanced version of the Ordinals protocol. It is used to issue assets called SAT20 assets. These assets are bound to satoshis and inherit the properties of satoshis:
1. Satoshis are not destructible, so the assets are also non-destructible.
2. The data bound to satoshis is immutable, so once the assets are issued, they cannot be modified.
3. Wherever the satoshis are, the assets are also present, allowing assets to freely move across different networks alongside satoshis.
4. Assets belong to the owner of the satoshis, so when satoshis are transferred, the assets are transferred as well.
5. The non-fungible nature of satoshis determines the non-fungibility of assets, making them inherently SFT (Semi-Fungible Token) assets.
6. Satoshis can be bound to any data, including smart contracts, enabling assets to have a certain level of intelligence.

Asset Circulation Protocol (Transcend)
----
The SAT20 asset circulation protocol defines the rules for the circulation of satoshis and provides an implementation sample.
1. Satoshis Locking: Satoshis can be locked and unlocked via the Lightning Network channels, allowing users to exit autonomously and ensuring the safety of their funds.
2. Satoshis Transcending: Locked satoshis are automatically transcended to the second layer networks, allowing them to continue circulating as satoshis within these networks. Users can transcend Satoshi back to the mainnet at any time.
3. Satoshis Swapping: The core technology enabling the free movement of satoshis within the second layer networks.
4. Core Principles:
   * Safe Withdrawal: Users can decide to withdraw from the second layer networks at any time without requiring permission from others.
   * Client Verification: Users can self-verify whether an asset is bound to a satoshi by its identifier.
   * Complete asset transfer history

Vision
----
One sat, one world.

Everyone can enjoy the benefits of the BTC network.