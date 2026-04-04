from Traversals import bfs_path
import heapq
from collections import deque
from Simulator import Simulator


class Solution:

    def __init__(self, problem, isp, graph, info):
        self.problem = problem
        self.isp = isp
        self.graph = graph
        self.info = info

    def _widest_path(self, target, caps):
        heap = [(-float("inf"), self.isp, [self.isp])]
        best = {self.isp: float("inf")}
        while heap:
            neg, u, path = heapq.heappop(heap)
            w = -neg
            if w < best.get(u, -1):
                continue
            if u == target:
                return path
            for v in self.graph.get(u, []):
                nw = min(w, caps.get(v, float("inf")))
                if nw > best.get(v, -1):
                    best[v] = nw
                    heapq.heappush(heap, (-nw, v, path + [v]))
        return None

    def output_paths(self):
        g, isp = self.graph, self.isp
        info = self.info
        clients = info["list_clients"]
        caps = info["bandwidths"]
        alphas = info["alphas"]
        pays = info["payments"]

        dist = {isp: 0}
        q = deque([isp])
        while q:
            u = q.popleft()
            for v in g.get(u, []):
                if v not in dist:
                    dist[v] = dist[u] + 1
                    q.append(v)

        paths = dict(bfs_path(g, isp, clients))

        def sim_delays(p):
            sim = Simulator()
            sim.run(g, isp, clients, p, caps, None, None)
            return sim.get_delays(clients)

        for _ in range(5):
            d = sim_delays(paths)
            slow = [
                c for c in clients
                if c in dist and d.get(c, float("inf")) > alphas[c] * dist[c]
            ]
            if not slow:
                break
            for c in sorted(slow, key=pays.__getitem__, reverse=True):
                alt = self._widest_path(c, caps)
                if alt:
                    paths[c] = alt

        bandwidths = {}
        priorities = {}
        # Note: You do not need to modify all of the above. For Problem 1, only the paths variable needs to be modified. If you do modify a variable you are not supposed to, you might notice different revenues outputted by the Driver locally since the autograder will ignore the variables not relevant for the problem.
        # WARNING: DO NOT MODIFY THE LINE BELOW, OR BAD THINGS WILL HAPPEN
        return (paths, bandwidths, priorities)
