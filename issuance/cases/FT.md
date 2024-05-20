FT的铸造
====

每一个coin都绑定在聪上面，聪在哪里，coin就在哪里。以下是一些例子。


东方之珠
----
{   
  "p": "ordx",  
  "op": "deploy",  
  "tick": "Pearl",  
  "block": "828200-828800",  
  "lim": "10000",  
  "des": "The Oriental Pearl."    
}   
大概在2024年2月1日前后开启fair mint，持续到2月5日左右结束（由区块高度828200-828800决定有效的mint时间）。这是ordx协议的第一个token，也是一个meme币，仅供试验，没有价值，不要FOMO。  


还可以在稀有聪上铸造FT，这是我们计划做的试验：


矿工的翡翠
----
{  
  "p": "ordx",  
  "op": "deploy",  
  "tick": "Jades",  
  "lim": "1",  
  "attr": "rar=uncommon",  
  "des": "Miner's Jades."  
}  
每个区块的第一个sat才能mint成功，预计每个Jades值1个BTC。


数字黄金
----
{  
  "p": "ordx",  
  "op": "deploy",  
  "tick": "Golds",  
  "lim": "1",  
  "attr": "trz=8",  
  "des": "The first satoshi in a BTC"  
}  
每个BTC的第一个sat才能mint成功。该sat的序号的末尾是8个0。这意味着，每个token值一个BTC。

