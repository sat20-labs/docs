Asset Issuance Modes
====

There are three main modes for issuing SAT20 assets, primarily adjusted based on the following three parameters:
1. selfmint: Proportion of self-minting, must be set along with the max parameter.
2. max: Total supply of the token.
3. block: Block height range for minting.

Project-led Mode
----

For projects led by the issuer, two modes are available:

1. Complete Control
selfmint: 100%  
max: 64-bit integer, must be set.  
block: Optional parameter, can be set or not.  

In this mode, only the address holding the deploy NFT can mint tokens, and the assets will be fully controlled by the project. Stablecoins, for example, are typically minted by the project team.

2. Partial Control
selfmint: A value less than 100%, such as 10%.  
max: 64-bit integer, must be set.  
block: Must be set, and the starting block should be at least 1,000 blocks after the deployment confirmation.  

In this mode, the address holding the deploy NFT can mint tokens, but not exceeding the set proportion. Any excess minting is considered invalid. Other addresses can participate in minting following the rules of a fair launch.  

Fair Launch
----
selfmint: Not set.  
max: 64-bit integer, optional.  
block: Must be set, and the starting block should be at least 1,000 blocks after the deployment confirmation.  

This mode is primarily community-led, focusing on fair minting by community members, controlled by the block parameter. The deployment confirmation block must be at least 1,000 blocks before the starting block; otherwise, the ticker is considered invalid. If a max limit is set and the total supply reaches that limit before the end block is reached, further minting is considered invalid. Once the end block is reached, minting is no longer possible, even if the max limit has not been reached.  

Unrestricted Mode
----
selfmint: Not set.  
max: Optional.  
block: Not set.  

In this mode, minting is not restricted by the parameters mentioned above, but rather by other factors specified by the project team. For example, it may require minting to continue on a specific rare satoshi or ticker.  

Through these mode settings, we aim to provide projects with complete flexibility and allow participants to clearly understand the type of project they are engaging with.  