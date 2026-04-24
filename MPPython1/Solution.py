from collections import deque, defaultdict
import heapq

class Solution:
    def __init__(self, problem, isp, graph, info):
        self.isp = isp
        self.graph = graph
        self.info = info

    def output_paths(self):
        C = self.info["list_clients"]
        caps = dict(self.info["bandwidths"])
        alpha = self.info["alphas"]
        pay = self.info["payments"]

        # ---------- shortest distances ----------
        dist = {self.isp: 0}
        q = deque([self.isp])
        while q:
            u = q.popleft()
            for v in self.graph.get(u, []):
                if v not in dist:
                    dist[v] = dist[u] + 1
                    q.append(v)

        # ---------- widest path ----------
        def widest(target):
            if target not in dist:
                return None 
            
            best = {self.isp: float('inf')}
            parent = {self.isp: None}
            heap = [(-float('inf'), self.isp)]
            seen = set()

            while heap:
                neg_bw, u = heapq.heappop(heap)
                if u in seen:
                    continue
                seen.add(u)

                if u == target:
                    path,cur = [], target
                    while cur is not None:
                        path.append(cur)
                        cur = parent[cur]
                    return list(reversed(path))
                for v in self.graph.get(u, []):
                    if v not in seen:
                        bw = min(-neg_bw, caps.get(v, float('inf')))
                        if bw > best.get(v,-1):
                            best[v] = bw
                            parent[v] =u
                            heapq.heappush(heap, (-bw, v))

        # ---------- allocate bandwidth + detect slow ----------
        def allocate(paths):
            usage = defaultdict(int)

            for p in paths.values():
                for n in p:
                    if n != self.isp:
                        usage[n] += 1

            bw = {}
            slow = []

            for c, p in paths.items():
                bw[c] = min(
                    (caps[n] / usage[n] for n in p if n != self.isp),
                    default=float('inf')
                )

                required = dist.get(c, float('inf')) / alpha[c]
                if bw[c] < required:
                    slow.append(c)

            return bw, usage, slow

        # ---------- initial paths ----------
        paths = {}
        for c in C: 
            p = widest(c)
            if p:
                paths[c] = p 

        # ---------- main loop (guarantee all satisfied) ----------
        while True:
            bw, usage, slow_clients = allocate(paths)
            if not slow_clients:
                break

            changed = False

            # --- try rerouting ---
            for c in slow_clients:
                congested_nodes = sorted(
                    paths[c][1:-1],
                    key=lambda n: usage[n],
                    reverse=True
                )

                for bad in congested_nodes:
                    prev = {self.isp: None}
                    q = deque([self.isp])

                    found = False
                    while q:
                        u = q.popleft()
                        for v in self.graph.get(u, []):
                            if v == bad or v in prev:
                                continue
                            prev[v] = u
                            if v == c:
                                found = True
                                break
                            q.append(v)
                        if found:
                            break

                    if found:
                        path, cur = [], c
                        while cur is not None:
                            path.append(cur)
                            cur = prev[cur]
                        paths[c] = list(reversed(path))
                        changed = True
                        break

                if changed:
                    break

            if changed:
                continue

            # --- upgrade bottlenecks ---
            better = False
            for c in slow_clients:
                required = dist.get(c, float('inf')) / alpha[c]

                for n in paths[c]:
                    if n == self.isp:
                        continue
                
                    share = caps[n] / max(usage[n], 1)
                    if share < required:
                        caps[n] = required * usage[n]
                        better = True
            if better == False:
                break 
                        


        # ---------- priorities ----------
        priorities = {
            c: pay[c] * (dist.get(c, 1) / alpha[c]) / max(bw.get(c, 1e-9), 1e-9)
            for c in C
        }

        return paths, caps, priorities