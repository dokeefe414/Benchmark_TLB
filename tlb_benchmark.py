import random
from collections import deque

random.seed(42)

# -------------------------------------------------
# Cost model: hit = 1 cycle, miss = 100 cycles
# -------------------------------------------------
HIT_COST  = 1
MISS_COST = 100

# -------------------------------------------------
# Workload Scenarios
# -------------------------------------------------
def scenario_hot_loop(n=1000, addr_space=50):
    """One small working set, accessed 90% of the time."""
    hot  = list(range(10))
    cold = list(range(10, addr_space))
    return [random.choice(hot) if random.random() < 0.9
            else random.choice(cold) for _ in range(n)]

def scenario_random(n=1000, addr_space=50):
    """Completely random accesses — no locality."""
    return [random.randrange(addr_space) for _ in range(n)]

def scenario_thrashing(n=1000, tlb_size=8):
    """Working set is just bigger than the TLB — causes constant evictions."""
    ws = list(range(tlb_size + 2))
    return [ws[i % len(ws)] for i in range(n)]

# -------------------------------------------------
# Replacement Algorithms
# -------------------------------------------------
def run_lru(accesses, tlb_size):
    tlb = []   # front = LRU end, back = MRU end
    hits = 0
    for page in accesses:
        if page in tlb:
            hits += 1
            tlb.remove(page)
            tlb.append(page)        # move to MRU end
        else:
            if len(tlb) >= tlb_size:
                tlb.pop(0)          # evict least recently used
            tlb.append(page)
    return hits

def run_fifo(accesses, tlb_size):
    tlb   = set()
    queue = deque()
    hits  = 0
    for page in accesses:
        if page in tlb:
            hits += 1
        else:
            if len(tlb) >= tlb_size:
                tlb.remove(queue.popleft())   # evict oldest
            tlb.add(page)
            queue.append(page)
    return hits

def run_random_algo(accesses, tlb_size):
    tlb  = []
    hits = 0
    for page in accesses:
        if page in tlb:
            hits += 1
        else:
            if len(tlb) >= tlb_size:
                tlb.pop(random.randrange(len(tlb)))   # evict random entry
            tlb.append(page)
    return hits

def run_opt(accesses, tlb_size):
    tlb  = []
    hits = 0
    for i, page in enumerate(accesses):
        if page in tlb:
            hits += 1
        else:
            if len(tlb) >= tlb_size:
                # evict the page whose next use is farthest away
                def next_use(p):
                    try:    return accesses.index(p, i + 1)
                    except: return len(accesses)   # never used again
                tlb.remove(max(tlb, key=next_use))
            tlb.append(page)
    return hits

# -------------------------------------------------
# Print results for one scenario
# -------------------------------------------------
def run_scenario(name, accesses, tlb_size=8):
    n = len(accesses)
    print(f"\n{name}  (TLB size={tlb_size}, accesses={n})")
    print(f"  {'Algorithm':<10} {'Hit Rate':>10} {'Avg Latency':>13} {'Lifespan':>10}")
    print(f"  {'-'*47}")
    for label, fn in [("OPT", run_opt), ("LRU", run_lru),
                      ("FIFO", run_fifo), ("Random", run_random_algo)]:
        hits     = fn(list(accesses), tlb_size)
        hit_rate = hits / n
        avg_lat  = hit_rate * HIT_COST + (1 - hit_rate) * MISS_COST
        lifespan = round(1_000_000 / avg_lat)
        print(f"  {label:<10} {hit_rate*100:>9.1f}% {avg_lat:>13.2f} {lifespan:>10,}")

# -------------------------------------------------
# Main
# -------------------------------------------------
if __name__ == "__main__":
    print("TLB REPLACEMENT ALGORITHM BENCHMARK")
    print("Hit cost=1 cycle, Miss cost=100 cycles")

    TLB = 8

    run_scenario("Scenario 1: Hot Loop",  scenario_hot_loop(),                tlb_size=TLB)
    run_scenario("Scenario 2: Random",    scenario_random(),                   tlb_size=TLB)
    run_scenario("Scenario 3: Thrashing", scenario_thrashing(tlb_size=TLB),   tlb_size=TLB)

    # Show how hit rate changes with TLB size (Hot Loop)
    print("\n\nHit rate vs TLB size  (Hot Loop scenario)")
    print(f"  {'TLB':>5}  {'OPT':>8}  {'LRU':>8}  {'FIFO':>8}  {'Random':>8}")
    print(f"  {'-'*47}")
    accesses = scenario_hot_loop()
    for size in [4, 8, 16, 32]:
        row = f"  {size:>5}"
        for fn in [run_opt, run_lru, run_fifo, run_random_algo]:
            h = fn(list(accesses), size)
            row += f"  {h/len(accesses)*100:>7.1f}%"
        print(row)
