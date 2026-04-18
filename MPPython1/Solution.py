from Traversals import bfs_path
from collections import defaultdict

class Solution:

    def __init__(self, problem, isp, graph, info):
        self.problem = problem
        self.isp = isp
        self.graph = graph
        self.info = info

    def output_paths(self):
        paths, bandwidths, priorities = {}, {}, {}

        clients  = self.info["list_clients"]
        orig_bw  = self.info["bandwidths"]
        alphas   = self.info["alphas"]
        betas    = self.info["betas"]
        pays     = self.info["payments"]
        rural    = set(self.info.get("is_rural", {}).keys())
        subset   = self.info["s"]
        rho_l    = self.info["rho_lawsuit"]
        rho_f    = self.info["rho_fcc"]
        A, B, Z  = self.info["A"], self.info["B"], self.info["Z"]

        # find shortest path from ISP to each client
        paths = dict(bfs_path(self.graph, self.isp, clients))

        # rural clients use beta since their alpha is infinite
        priorities = {c: pays[c] / (betas[c] if c in rural else alphas[c]) for c in clients}

        # count how many clients pass through each node
        load = defaultdict(int)
        for c in clients:
            for u in paths[c][:-1]:
                load[u] += 1

        # bump up any node whose bandwidth is below its load
        skip = set(clients) | {self.isp}
        bandwidths = dict(orig_bw)
        for u, b in orig_bw.items():
            if u not in skip and b != float("inf") and b < load.get(u, 0):
                bandwidths[u] = load[u]

        # compute effective bandwidth each client receives after sharing
        def get_bandwidth(bw):
            use = defaultdict(int)
            for c in clients:
                for n in paths[c]:
                    if n != self.isp: use[n] += 1
            return {c: min((bw.get(n, float('inf')) / use[n]
                            for n in paths[c] if n != self.isp), default=float('inf'))
                    for c in clients}, use

        # clients who get less bandwidth than their complaint threshold
        def get_complainers(bw, group):
            return [c for c in group if bw.get(c, 0) < (len(paths[c]) - 1) / betas[c]]

        # penalty if enough clients complain
        def get_penalty(bw):
            law = len(get_complainers(bw, clients)) >= int(rho_l * len(clients))
            fcc = len(get_complainers(bw, subset))  >= int(rho_f * len(subset))
            return (A if law else 0) + (B if fcc else 0)

        # try upgrading bandwidths if it saves more than it costs
        bw, use = get_bandwidth(bandwidths)
        if get_penalty(bw) > 0:
            new_bw, cost = dict(bandwidths), 0
            complainers  = set(get_complainers(bw, clients) + get_complainers(bw, subset))
            for c in sorted(complainers, key=lambda c: pays[c], reverse=True):
                bot = min((n for n in paths[c] if n != self.isp),
                          key=lambda n: new_bw.get(n, float('inf')) / max(use[n], 1), default=None)
                if not bot: continue
                needed = (len(paths[c]) - 1) / betas[c] * use[bot]
                if needed > new_bw.get(bot, float('inf')):
                    cost += needed - new_bw[bot]
                    new_bw[bot] = needed
            bw, _ = get_bandwidth(new_bw)
            if get_penalty(bw) < get_penalty(dict(bandwidths)) - cost * Z:
                bandwidths = new_bw

        # WARNING: DO NOT MODIFY THE LINE BELOW, OR BAD THINGS WILL HAPPEN
        return (paths, bandwidths, priorities)
