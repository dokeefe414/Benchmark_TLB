# Benchmark_TLB

This project benchmarks four TLB replacement algorithms (OPT, LRU, FIFO, Random) across three different memory access scenarios to see how each one performs under different conditions.

#Algorithms

OPT – evicts whichever page won't be used for the longest time. Not a real algorithm since it requires knowing the future, but useful as a benchmark ceiling.
LRU – evicts the page that hasn't been used in the longest time.
FIFO – evicts whichever page has been sitting in the TLB the longest.
Random – evicts a random page.


#Scenarios

Hot Loop – simulates a loop where 90% of accesses hit the same small set of pages
Random – completely random accesses with no pattern
Thrashing – the working set is slightly larger than the TLB, so something always has to get evicted


#Results

Hot Loop (TLB=8):
OPT 79.2%   LRU 58.9%   FIFO 54.9%   Random 58.0%
Random accesses (TLB=8):
OPT 42.1%   LRU 15.3%   FIFO 14.9%   Random 16.5%
Thrashing (TLB=8):
OPT 77.0%   Random 62.5%   LRU 0.0%   FIFO 0.0%
Hit rate vs TLB size (Hot Loop):
TLB     OPT     LRU    FIFO   Random
  4    55.6%   30.1%   30.8%   33.5%
  8    81.5%   61.9%   59.2%   61.1%
 16    93.2%   90.9%   83.2%   84.3%
 32    95.2%   93.7%   93.7%   93.1%

#Takeaways

LRU does the best when there's a clear access pattern like a loop. When accesses are random, all algorithms perform about the same since there's nothing to predict. The most interesting result is thrashing — LRU and FIFO both drop to 0% because the cyclic pattern causes them to always evict the wrong page, while Random avoids this just by being unpredictable. Bigger TLB helps a lot up to a point, but once it can fit the working set the gains level off.
