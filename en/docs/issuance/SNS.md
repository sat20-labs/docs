SAT20 Name Service
====

Satoshis are the foundation of our entire protocol ecosystem, and their ordinal numbers can be considered as indices of satoshis. However, the ordinal numbers are 64-bit integers, which are too long and not easy to remember. In order to quickly index each satoshi, it is necessary to develop a name service based on satoshis, allowing users to remember satoshis that hold significant meaning to them. The relationship between ordinal numbers and names is similar to the relationship between IP addresses and domain names. The SAT20 Name Service is a completely decentralized, BTC-based name service that is available to everyone on a fair basis and is not controlled by any third party.

The core of the name service is that each name is unique, and there are no sub-namespace. This avoids the possibility of fraud.
Each name is an NFT (Non-Fungible Token) that is engraved on a satoshi. A Satoshi has only one name, and the name and Satoshi are also in one-to-one correspondence.
Names are bound to satoshis, so whoever owns the satoshi also owns the name. When a satoshi is transferred, the name is transferred along with it.
Names are also a type of sat asset.

Naming Rules
---
1. The first instance of a name is valid.
2. Names use UTF-8 characters.
3. Case-insensitive. All names/namespaces will be indexed in lowercase.
4. No spaces are allowed in names.
5. No punctuation marks are allowed in names. (Names with periods are from other name protocols.)
6. Name length starts from 3 bytes, but 4-byte names are temporarily prohibited from registration.

Note: The 4-byte names are reserved for BRC20 tickers. 1-2 byte names are for internal protocol use only and are prohibited from registration at the protocol level. They will never be opened for registration to prevent unnecessary speculation.

Combination Rules
---
Names can be combined to form a special meaning. The protocol establishes the following basic rules:
1. Names are combined using the "@" symbol, such as Alice@sat20.
2. Both parties need to sign and agree to the combination, meaning that the combination represents a contractual relationship.
3. The latter name, such as "sat20," belongs to a higher-level organizational form, such as a company or club.

Compatibility
----
The SAT20 Name Service is compatible with the major name services currently on the BTC network. For example, taking .btc as an example, a name like 1.btc will be treated as a whole, rather than splitting it into the name "1" and the namespace ".btc". As our development progresses, we plan to be compatible with these name services (read-only, without support for minting):
1. .btc
2. .x
3. Others

Note that names with a "." and names without a "." are different names. For example, 123.btc and 123 are two independent names with no relationship to each other.

Monopolistic Resources
----
Names are core resources and also assets. For example, the name "Pearl" as a ticker name is a name automatically held by the address that deployed the ticker. If a name has already been registered, other people cannot deploy a ticker for that name. By registering a name, one automatically gains all the permissions associated with that name, and the SAT20 protocol maintains these permissions.

Royalties
----
The owner of a resource will automatically receive royalties based on a configurable tax rate when the resource is used. The resource owner automatically receives royalty income.