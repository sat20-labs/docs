序数
====

SAT20 strictly assigns ordinal numbers to satoshis based on their order of creation, ensuring a **one-to-one correspondence between ordinal numbers and satoshis, with a continuous increase**. This means that within the valid range, each ordinal number corresponds to a satoshi, and each satoshi corresponds to an ordinal number. This strict one-to-one relationship is permanent. The basic principles of ordinal numbers are as follows:
1. The ordinal number of the first satoshi is 0.
2. The numbering follows the order of creation without any gaps.
3. Satoshis are transferred in a first-in, first-out manner.
4. In reward transactions, the rewarded satoshis are the first inputs, followed by other transactions' satoshis as fees in sequential order.
5. The rewarded quantity matches the actual reward quantity exactly.

The ordinal number theory of SAT20 is derived from the Ordinals protocol, but there are fundamental differences between them:
1. The Ordinals protocol considers satoshis to be destroyable, and in fact, 2,895,502,904 satoshis have already been destroyed within the Ordinals ordinal number theory system before block 840000. This result can be confirmed by querying the Ordinals website (https://ordinals.com/status).
2. The Ordinals protocol assigns ordinal numbers to satoshis based on theory, resulting in many ordinal numbers that do not have actual satoshis corresponding to them. For example, at height 840,000, which is the fourth halving, the first satoshi of the block, called "epic," has the ordinal number 1,968,750,000,000,000. This might give the impression that 19,687,500 BTC have already been issued. However, in reality, before this height, there were slightly less than 19,687,497.2 BTC in circulation, as there were many reward blocks that were not fully claimed. Therefore, in the Ordinals ordinal number theory, for the epic satoshi with the ordinal number 1,968,750,000,000,000 at the fourth halving, there are many ordinal numbers before it that do not have corresponding satoshis.

SAT20 does not directly adopt the ordinal number theory of the Ordinals protocol, mainly because we consider satoshis to be non-destructible. This fundamental difference from the ordinal number theory of the Ordinals protocol makes it impossible for us to develop SAT20 assets based on the Ordinals ordinal number theory. Fortunately, the ordinal number theory of Ordinals has officially entered the BIP process. We look forward to the satoshis having a formal numbering rule as soon as possible, and we hope that the numbering of satoshis will better align with the fundamental principles of BTC and be based on the actual situation. Once there is a standardized scheme for satoshi numbering, we will respond promptly to the standard satoshi numbering rules, which will not affect the security of SAT20 assets.

Furthermore, SAT20 fully supports Ordinals NFTs because Ordinals NFTs are assets bound to satoshis, which align with the definition of SAT20 assets. In other words, Ordinals NFTs are also a type of SAT20 asset.

(Note: The Ordinals theory now has an official BIP number and has entered the consideration process. The possibility of the Ordinals theory becoming a BTC standard is very high. Ultimately, the encoding scheme used by the Ordinals theory will become the encoding scheme for SAT20. For more details, please refer to: https://github.com/bitcoin/bips/pull/1408)