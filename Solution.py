from Traversals import bfs_path
import heapq
from collections import deque
from Simulator import Simulator
import sys

class Solution:

    def __init__(self, problem, isp, graph, info):
        self.problem = problem
        self.isp = isp
        self.graph = graph
        self.info = info

    def output_paths(self):
        """
        This method must be filled in by you. You may add other methods and subclasses as you see fit,
        but they must remain within the Solution class.
        """
        paths, bandwidths, priorities = {}, {}, {}
        
        paths = bfs_path(self.graph, self.isp, self.info["list_clients"])
        
        """
        Steps for problem 2:
        
        1) Find shortest path and distance using BFS
        
        2) Sort clients by payment(high to low)
        
        3) Track how many paths have passed through each node 
        
        4) For each client, find the path that avoids heavily loaded nodes while staying within 
        """
        "its not adding "
        
        
        "this is for the test"
        
        "this is for the test"
        # Note: You do not need to modify all of the above. For Problem 1, only the paths variable needs to be modified. If you do modify a variable you are not supposed to, you might notice different revenues outputted by the Driver locally since the autograder will ignore the variables not relevant for the problem.
        # WARNING: DO NOT MODIFY THE LINE BELOW, OR BAD THINGS WILL HAPPEN
        
        return (paths, bandwidths, priorities)
