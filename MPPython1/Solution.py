from Traversals import bfs_path
import heapq
from collections import deque, defaultdict
from Simulator import Simulator
import sys

class Solution:

    def __init__(self, problem, isp, graph, info):
        self.problem = problem
        self.isp = isp
        self.graph = graph
        self.info = info

    def output_paths(self):
        paths, bandwidths, priorities = {}, {}, {}

        caps     = dict(self.info["bandwidths"])
        alphas   = self.info["alphas"]
        betas    = self.info["betas"]
        payments = self.info["payments"]
        clients  = self.info["list_clients"]
        rural    = set(self.info.get("rural_clients", []))  # R — never unsubscribe
        subset   = self.info["s"]                           # S — FCC test group
        rho_law  = self.info["rho_lawsuit"]
        rho_fcc  = self.info["rho_fcc"]
        A        = self.info["A"]
        B        = self.info["B"]
        Z        = self.info["Z"]

        # ----------------------------------------------------------------
        # BFS hop counts from ISP — used as delay lower bound
        # ----------------------------------------------------------------
        dist, q = {self.isp: 0}, deque([self.isp])
        while q:
            u = q.popleft()
            for v in self.graph.get(u, []):
                if v not in dist: dist[v] = dist[u] + 1; q.append(v)

        def widest(target, caps):
            """Max-bottleneck Dijkstra — best bandwidth path to target."""
            heap, seen = [(-float('inf'), self.isp, [self.isp])], set()
            while heap:
                neg, u, path = heapq.heappop(heap)
                if u in seen: continue
                seen.add(u)
                if u == target: return path
                for v in self.graph.get(u, []):
                    if v not in seen:
                        heapq.heappush(heap, (-min(-neg, caps.get(v, float('inf'))), v, path + [v]))

        def alloc(paths, caps):
            """Split each node's bandwidth equally among clients sharing it."""
            usage = defaultdict(int)
            for p in paths.values():
                for n in p:
                    if n != self.isp: usage[n] += 1
            return {c: min((caps.get(n, float('inf')) / usage[n] for n in p if n != self.isp), default=float('inf'))
                    for c, p in paths.items()}

        def complainers(bw, caps, group):
            """Clients in group whose effective bandwidth falls below their β threshold."""
            return [c for c in group if c in bw and bw[c] < dist.get(c, float('inf')) / betas[c]]

        def penalty(comps, group, rho, fine):
            """Fine if complaint count clears the floor threshold."""
            return fine if len(comps) >= int(rho * len(group)) else 0

        # ----------------------------------------------------------------
        # Step 1: Sort clients — high payers first, but deprioritize rural
        # since their infinite alpha means they never trigger pen0
        # ----------------------------------------------------------------
        nonrural = [c for c in clients if c not in rural]
        rural_clients = [c for c in clients if c in rural]
        
        non_rural_ranked = sorted(nonrural, key=lambda c: payments[c], reverse=True )
        rural_ranked = sorted(rural_clients, 
                              key= lambda c: payments[c],
                              reverse=True)
        ranked = sorted(clients,
                        key=lambda c: (payments[c] if c not in rural else payments[c] * 0.5),
                        reverse=True)

        # ----------------------------------------------------------------
        # Step 2: Route via widest path
        # ----------------------------------------------------------------
        paths = {c: p for c in ranked if (p := widest(c, caps))}

        # ----------------------------------------------------------------
        # Step 3: Reroute unsatisfied non-rural clients (rural never leave
        # so only fix them if it doesn't cost routing quality for others)
        # ----------------------------------------------------------------
        for _ in range(3):
            bw   = alloc(paths, caps)
            # rural clients have alpha=inf so skip them for unsubscribe check
            slow = [c for c in paths if c not in rural
                    and bw[c] < dist.get(c, float('inf')) / alphas[c]]
            if not slow: break
            for c in slow:
                for node in sorted(paths[c][1:-1], key=lambda n: sum(n in p for p in paths.values()), reverse=True):
                    prev, q = {self.isp: None}, deque([self.isp])
                    while q:
                        u = q.popleft()
                        for v in self.graph.get(u, []):
                            if v == node or v in prev: continue
                            prev[v] = u
                            if v == c:
                                path, cur = [], u
                                while cur: path.append(cur); cur = prev[cur]
                                paths[c] = list(reversed(path)) + [c]
                                q.clear(); break
                        else: continue
                        break
                    else: continue
                    break

        # ----------------------------------------------------------------
        # Step 4: Set priorities
        # Higher priority = lower delay = less likely to complain/unsubscribe
        # Give highest priority to high-paying non-rural clients at risk,
        # then high-paying rural clients (they pay but won't leave),
        # lowest to rural clients with low payments
        # ----------------------------------------------------------------
        bw = alloc(paths, caps)
        for c in clients:
            if c in rural:
                # rural clients won't leave — lower base priority, scaled by payment
                priorities[c] = payments[c] / (betas[c] + 1)
            else:
                # non-rural: weight by payment and how close they are to threshold
                slack = bw.get(c, 0) / max((dist.get(c, 1) / alphas[c]), 1e-9)
                # lower slack = more urgent = higher priority
                priorities[c] = payments[c] / max(slack, 1e-9)

        # ----------------------------------------------------------------
        # Step 5: Assess penalties and decide whether to upgrade bandwidths
        # ----------------------------------------------------------------
        new_caps     = dict(caps)
        bw           = alloc(paths, new_caps)
        law_comps    = complainers(bw, new_caps, clients)
        fcc_comps    = complainers(bw, new_caps, subset)
        base_penalty = penalty(law_comps, clients, rho_law, A) + penalty(fcc_comps, subset, rho_fcc, B)

        if base_penalty > 0:
            usage = defaultdict(int)
            for p in paths.values():
                for n in p:
                    if n != self.isp: usage[n] += 1

            upgrade_cost = 0
            to_fix = sorted(set(law_comps + fcc_comps), key=lambda c: payments[c], reverse=True)

            for c in to_fix:
                bottleneck = min(
                    (n for n in paths[c] if n != self.isp),
                    key=lambda n: new_caps.get(n, float('inf')) / max(usage[n], 1),
                    default=None
                )
                if not bottleneck: continue

                needed   = dist.get(c, float('inf')) / betas[c] * usage[bottleneck]
                current  = new_caps.get(bottleneck, float('inf'))
                if needed > current:
                    upgrade_cost    += needed - current
                    new_caps[bottleneck] = needed

            bw          = alloc(paths, new_caps)
            new_law     = complainers(bw, new_caps, clients)
            new_fcc     = complainers(bw, new_caps, subset)
            new_penalty = penalty(new_law, clients, rho_law, A) + penalty(new_fcc, subset, rho_fcc, B)

            # revert if upgrades cost more than the penalty they prevent
            if (base_penalty - new_penalty) <= (upgrade_cost * Z):
                new_caps = caps

        # ----------------------------------------------------------------
        # Step 6: Final bandwidth map — b'u for every non-ISP node
        # ----------------------------------------------------------------
        bandwidths = {n: new_caps.get(n, caps.get(n, 0)) for n in caps}

        # WARNING: DO NOT MODIFY THE LINE BELOW, OR BAD THINGS WILL HAPPEN
        return (paths, bandwidths, priorities)
