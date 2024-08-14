Instructions
====

The SAT20 asset issuance protocol only includes the "deploy" and "mint" instructions. There is no need for a "transfer" instruction.

deploy
----

| KEY | Required | Description |
| :---: | :---: | :------- |
| p	| Yes | Protocol name: ordx |
| op | Yes | Instruction: deploy |
| tick | Yes | Ticker name: 3 to 16 characters (4 characters reserved for BRC-20) |
| lim | No | Token limit for each mint, default is 10,000. If minting a special token on a specific sat, the default is 1. |
| selfmint | No | Proportion of self-minting (two decimal places). Only addresses holding the ticker are allowed to mint (parent-child inscription). |
| max | No | Total minting limit, a 64-bit integer. |
| block | No | Start and end heights for minting (start-end). |
| attr | No | Requirements for satoshi attributes, e.g., "rar=uncommon;trz=8", extensible. |
| des | No | Description content. |

For example, a ticker for a fair launch:
{   
  "p": "ordx",  
  "op": "deploy",  
  "tick": "satoshi",  
  “block”: "830000-833144",  
  "lim": "10000"  
}

Or a ticker under the control of a project:
{   
  "p": "ordx",  
  "op": "deploy",  
  "tick": "Gamever",  
  "selfmint": "100%",  
  "max": "1000000000",  
  "lim": "10000"  
}

Rules for deploying tickers:
1. The ticker name must not have been used before, or the deployer must own the ticker (DID).
2. If the block parameter is provided, the deploy must be confirmed at a height greater than start height plus 1000.
Tickers that violate these rules are considered invalid.

"attr" is an extensible attribute designed to filter out increasingly special satoshis. Currently supported attributes include:
1. rar: Rarity, as defined in Ordinals: common, uncommon, rare, epic, legendary, mythic.
2. trz: Trailing zeros, the number of zeros at the end of the satoshi's identifier, e.g., trz=8 indicates that the satoshi's identifier has 8 zeros at the end.
3. Custom attributes will be supported in the future.

mint
----

| KEY | Required | Description |
| :---: | :---: | :------- |
| p	| Yes | Protocol name: ordx |
| op | Yes | Instruction: mint |
| tick | Yes | Ticker name: 3 to 16 characters (4 characters reserved for BRC-20) |
| amt | No | Number of tokens to mint, default is equal to lim and cannot exceed lim. |
| sat | No | Serial number of the satoshi. For tickers with specified attributes, the minting requires satisfying the specified satoshi. |

For example:
{  
  "p": "ordx",  
  "op": "mint",  
  "tick": "satoshi"  
}

Each time minting occurs, the following rule checks must be performed:
1. The protocol must be "ordx".
2. The operation must be "mint".
3. The ticker must have been deployed previously.
4. The "amt" must be less than or equal to the "lim" specified in the deploy.
5. If the deploy includes "selfmint":
  * Only addresses holding the ticker can mint (parent-child inscription).
  * The total minted amount, including the current mint, must not exceed max*selfmint.
6. If the deploy includes "max": The total minted amount, including the current mint, must not exceed max.
7. If the deploy includes "block": The block height for the current minting must be within the specified range.
8. If the deploy includes "attr": During minting, the specified satoshi must meet the following attribute requirements:
    * If "rar" attribute is provided, check if the satoshi falls under that rarity.
    * If "trz" attribute is provided, check if the satoshi's identifier has enough trailing zeros.
    * If custom attributes are provided, check according to the defined rules.

If the above rules are not met, the current minting is considered invalid.