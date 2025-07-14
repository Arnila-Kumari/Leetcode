Can you solve this real interview question? Graph Valid Tree - You have a graph of n nodes labeled from 0 to n - 1. You are given an integer n and a list of edges where edges[i] = [ai, bi] indicates that there is an undirected edge between nodes ai and bi in the graph.

Return true if the edges of the given graph make up a valid tree, and false otherwise.

 

Example 1:

![Example 1](./image_1.png)


Input: n = 5, edges = [[0,1],[0,2],[0,3],[1,4]]
Output: true


Example 2:

![Example 2](./image_2.png)


Input: n = 5, edges = [[0,1],[1,2],[2,3],[1,3],[1,4]]
Output: false


 

Constraints:

 * 1 <= n <= 2000
 * 0 <= edges.length <= 5000
 * edges[i].length == 2
 * 0 <= ai, bi < n
 * ai != bi
 * There are no self-loops or repeated edges.

---

## Images

- Image 1: `image_1.png`
- Image 2: `image_2.png`
