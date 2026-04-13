"""
TLB Replacement Algorithm Benchmark
CS Operating Systems — Programming Assignment

Compares: OPT, LRU, FIFO, Clock, Random
Scenarios: Hot-Loop, Multi-Locality, Random, Thrashing
Metrics:   hit rate, miss rate, avg latency, effective process lifespan

Cost model: TLB hit = 1 cycle, TLB miss = 100 cycles
"""

import random
from collections import OrderedDict, deque

random.seed(42)

HIT_COST  = 1
MISS_COST = 100


# ── Workload Generators ───────────────────────────────────────────────

def gen_hot_loop(n=2000, addr_space=64, hot_size=8):
    """One small hot region (90% of accesses) + random cold accesses."""
    hot  = list(range(hot_size))
    cold = list(range(hot_size, addr_space))
    return [random.choice(hot) if random.random() < 0.90 else random.choice(cold)
            for _ in range(n)]

def gen_multi_locality(n=2000, addr_space=64, num_regions=3, region_size=6):
    """Several hot regions with equal probability, models multi-phase workloads."""
    stride  = addr_space // (num_regions + 1)
    regions = [list(range(i*stride, i*stride + region_size)) for i in range(1, num_regions+1)]
    cold    = [p for p in range(addr_space) if not any(p in r for r in regions)]
    return [random.choice(random.choice(regions)) if random.random() < 0.75
            else random.choice(cold) for _ in range(n)]

def gen_random(n=2000, addr_space=64):
    """Uniform random — no locality, worst-case baseline."""
    return [random.randrange(addr_space) for _ in range(n)]

def gen_thrashing(n=2000, tlb_size=8, addr_space=64):
    """Working set = TLB size + 2; every eviction causes an immediate conflict."""
    ws = list(range(min(tlb_size + 2, addr_space)))
    return [ws[i % len(ws)] for i in range(n)]


# ── Replacement Algorithms ────────────────────────────────────────────

def sim_opt(accesses, tlb_size):
    tlb, hits, misses = [], 0, 0
    for i, pg in enumerate(accesses):
        if pg in tlb:
            hits += 1
        else:
            misses += 1
            if len(tlb) < tlb_size:
                tlb.append(pg)
            else:
                # evict page whose next use is farthest away
                def next_use(p):
                    try:    return accesses.index(p, i + 1)
                    except: return len(accesses)          # never used again
                tlb.remove(max(tlb, key=next_use))
                tlb.append(pg)
    return hits, misses

def sim_lru(accesses, tlb_size):
    order = OrderedDict()
    hits, misses = 0, 0
    for pg in accesses:
        if pg in order:
            hits += 1
            order.move_to_end(pg)
        else:
            misses += 1
            if len(order) >= tlb_size:
                order.popitem(last=False)
            order[pg] = None
    return hits, misses

def sim_fifo(accesses, tlb_size):
    tlb, queue, hits, misses = set(), deque(), 0, 0
    for pg in accesses:
        if pg in tlb:
            hits += 1
        else:
            misses += 1
            if len(tlb) >= tlb_size:
                tlb.discard(queue.popleft())
            tlb.add(pg)
            queue.append(pg)
    return hits, misses

def sim_clock(accesses, tlb_size):
    frames = [None] * tlb_size
    ref    = [False] * tlb_size
    ptr    = 0
    page_slot = {}
    hits, misses = 0, 0
    for pg in accesses:
        if pg in page_slot:
            hits += 1
            ref[page_slot[pg]] = True
        else:
            misses += 1
            while ref[ptr]:          # second-chance sweep
                ref[ptr] = False
                ptr = (ptr + 1) % tlb_size
            if frames[ptr] is not None:
                del page_slot[frames[ptr]]
            frames[ptr]    = pg
            ref[ptr]       = True
            page_slot[pg]  = ptr
            ptr = (ptr + 1) % tlb_size
    return hits, misses

def sim_random(accesses, tlb_size):
    tlb, hits, misses = [], 0, 0
    for pg in accesses:
        if pg in tlb:
            hits += 1
        else:
            misses += 1
            if len(tlb) < tlb_size:
                tlb.append(pg)
            else:
                tlb[random.randrange(tlb_size)] = pg
    return hits, misses


ALGORITHMS = {
    "OPT":    sim_opt,
    "LRU":    sim_lru,
    "FIFO":   sim_fifo,
    "Clock":  sim_clock,
    "Random": sim_random,
}


# ── Run & Print ───────────────────────────────────────────────────────

def run(label, accesses, tlb_size):
    total = len(accesses)
    print(f"\n  Scenario: {label}  |  TLB size: {tlb_size}  |  Accesses: {total}")
    print(f"  {'Algorithm':<10} {'Hits':>6} {'Misses':>7} {'Hit%':>7} {'AvgLat':>9} {'Lifespan':>10}")
    print("  " + "-" * 55)
    for name, fn in ALGORITHMS.items():
        h, m = fn(list(accesses), tlb_size)
        hit_rate = h / total
        avg_lat  = hit_rate * HIT_COST + (1 - hit_rate) * MISS_COST
        lifespan = round(1_000_000 / avg_lat)   # accesses within 1M-cycle budget
        print(f"  {name:<10} {h:>6} {m:>7} {hit_rate*100:>6.1f}% {avg_lat:>9.2f} {lifespan:>10,}")


def sweep(label, accesses, sizes):
    total = len(accesses)
    print(f"\n  Hit rate vs TLB size — {label}")
    header = f"  {'TLB':>5}" + "".join(f"  {a:>8}" for a in ALGORITHMS)
    print(header)
    print("  " + "-" * (len(header) - 2))
    for ts in sizes:
        row = f"  {ts:>5}"
        for fn in ALGORITHMS.values():
            h, m = fn(list(accesses), ts)
            row += f"  {h/(h+m)*100:>7.1f}%"
        print(row)


if __name__ == "__main__":
    N          = 2000
    ADDR_SPACE = 64
    TLB        = 8
    SIZES      = [4, 8, 12, 16, 24, 32]

    print("=" * 60)
    print("TLB REPLACEMENT ALGORITHM BENCHMARK")
    print(f"Hit cost={HIT_COST} cycle   Miss cost={MISS_COST} cycles")
    print("=" * 60)

    scenarios = {
        "Hot-Loop":       gen_hot_loop(N, ADDR_SPACE),
        "Multi-Locality": gen_multi_locality(N, ADDR_SPACE),
        "Random":         gen_random(N, ADDR_SPACE),
        "Thrashing":      gen_thrashing(N, TLB, ADDR_SPACE),
    }

    # Main results at TLB=8
    print("\n── RESULTS AT TLB SIZE = 8 ──────────────────────────────")
    for label, accesses in scenarios.items():
        run(label, accesses, TLB)

    # Sweep: hit rate vs TLB size
    print("\n\n── HIT RATE vs TLB SIZE ─────────────────────────────────")
    for label, accesses in scenarios.items():
        sweep(label, accesses, SIZES)

    # Optimality gap
    print("\n\n── OPTIMALITY GAP: OPT vs LRU (TLB=8) ──────────────────")
    print(f"  {'Scenario':<18} {'OPT':>7} {'LRU':>7} {'Gap':>8}")
    print("  " + "-" * 44)
    for label, accesses in scenarios.items():
        ho, mo = sim_opt(list(accesses), TLB)
        hl, ml = sim_lru(list(accesses), TLB)
        opt_hr = ho / (ho + mo) * 100
        lru_hr = hl / (hl + ml) * 100
        print(f"  {label:<18} {opt_hr:>6.1f}% {lru_hr:>6.1f}% {opt_hr-lru_hr:>+7.1f}pp")