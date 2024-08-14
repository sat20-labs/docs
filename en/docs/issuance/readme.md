SAT20 Asset Issuance Protocol
=========

The SAT20 Asset Issuance Protocol is a protocol for issuing various types of digital assets on the BTC mainnet. Its core is the **binding of satoshis**, hence the name "Sat Asset" (SAT20 ASSETS). Sat Assets have distinctive characteristics and are the world's first "**satoshi standard**" native BTC asset issuance protocol, where assets possess the properties of satoshis.

Basic Properties of SAT20 Assets
----
1. Satoshis are not destructible, so the assets are also non-destructible.
2. The data bound to satoshis is immutable, so once the assets are issued, they cannot be modified.
3. Wherever the satoshis are, the assets are also present, allowing assets to freely move across different networks alongside satoshis.
4. Assets belong to the owner of the satoshis, so when satoshis are transferred, the assets are transferred as well.
5. The non-fungible nature of satoshis determines the non-fungibility of assets, making them inherently SFT (Semi-Fungible Token) assets.
6. Satoshis can be bound to any data, including smart contracts, enabling assets to have a certain level of intelligence.


Basic Capabilities of SAT20 Assets
----
The issuance of SAT20 assets relies on two basic capabilities:
1. The ability to identify satoshis and track them.
2. The ability to read and write data on satoshis.

Core Principles of SAT20 Assets
----
SAT20 assets are built upon the two fundamental properties of satoshis, which are also the core principles of SAT20 assets:
1. The non-fungible nature of satoshis. The order of creation of satoshis determines their uniqueness and identifiability. Each satoshi can be encoded using a certain encoding scheme, serving as its identification that remains unchanged.
2. The non-destructible nature of satoshis. BTC operates on a ledger model that requires ledger balance. Satoshis, being inputs and outputs of the ledger, cannot be destroyed, as it would result in an imbalanced ledger.

Other Related Services
----
In addition, for convenient indexing and data manipulation of satoshis, some core services based on satoshis must be established:
1. Naming service. Based on satoshis, it facilitates memorability and propagation, serving as the foundation of IP (Intellectual Property) development and an essential core service for protocol evolution.
2. Data service. It enables the reading and writing of data bound to satoshis, where only the owner can write while anyone can read. In the future, income-generating services will require payment for accessing data.
3. Payment service. SAT20 supports running software compiled into the WASM (WebAssembly) format on a virtual machine (VM). When income-generating services run other software packages on the VM, fees are charged, which are shared between node providers and software developers. The fees are low but not zero, denominated in satoshis.

The protocol's verification version was officially activated at height 827,307, and the official version is planned to be activated at height 845,000.
