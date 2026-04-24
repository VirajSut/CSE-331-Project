from Traversals import bfs_path
import heapq
from collections import deque, defaultdict

class Solution:

    def __init__(self, problem, isp, graph, info):
        self.problem = problem
        self.isp = isp
        self.graph = graph
        self.info = info

    def output_paths(self):
        paths, bandwidths, priorities = {}, {}, {}

        clients = self.info["list_clients"]
        orig_bw = self.info["bandwidths"]
        alphas  = self.info["alphas"]
        pays    = self.info["payments"]
        Z       = self.info.get("Z", 0)

        dist, q = {self.isp: 0}, deque([self.isp])
        while q:
            u = q.popleft()
            for v in self.graph.get(u, []):
                if v not in dist: dist[v] = dist[u] + 1; q.append(v)

        def widest(target, caps):
            heap, seen = [(-float('inf'), self.isp, [self.isp])], set()
            while heap:
                neg, u, path = heapq.heappop(heap)
                if u in seen: continue
                seen.add(u)
                if u == target: return path
                for v in self.graph.get(u, []):
                    if v not in seen:
                        heapq.heappush(heap, (-min(-neg, caps.get(v, float('inf'))), v, path + [v]))

        def alloc(caps):
            use = defaultdict(int)
            for p in paths.values():
                for n in p:
                    if n != self.isp: use[n] += 1
            return {c: min((caps.get(n, float('inf')) / use[n] for n in paths[c] if n != self.isp),
                           default=float('inf')) for c in paths}, use

        def slow(bw): return [c for c in clients if bw.get(c, 0) < dist.get(c, float('inf')) / alphas[c]]

        caps  = dict(orig_bw)
        paths = {c: p for c in sorted(clients, key=lambda c: pays[c], reverse=True) if (p := widest(c, caps))}

        for _ in range(5):
            bw, use = alloc(caps)
            if not slow(bw): break
            for c in slow(bw):
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
                                paths[c] = list(reversed(path)) + [c]; q.clear(); break
                        else: continue
                        break
                    else: continue
                    break

        # one unsatisfied client wipes all revenue — always upgrade
        bw, use = alloc(caps)
        for c in sorted(slow(bw), key=lambda c: pays[c], reverse=True):
            bot = min((n for n in paths[c] if n != self.isp), key=lambda n: caps.get(n, float('inf')) / max(use[n], 1), default=None)
            if bot and (needed := dist.get(c, float('inf')) / alphas[c] * use[bot]) > caps.get(bot, float('inf')):
                caps[bot] = needed

        bw, _      = alloc(caps)
        priorities = {c: pays[c] / max(bw.get(c, 1e-9) / max(dist.get(c, 1) / alphas[c], 1e-9), 1e-9) for c in clients}
        bandwidths = {n: caps.get(n, orig_bw.get(n, 0)) for n in orig_bw}

        # WARNING: DO NOT MODIFY THE LINE BELOW, OR BAD THINGS WILL HAPPEN
        return (paths, bandwidths, priorities)
