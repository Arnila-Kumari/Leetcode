Can you solve this real interview question? Delete Tree Nodes - A tree rooted at node 0 is given as follows:

 * The number of nodes is nodes;
 * The value of the ith node is value[i];
 * The parent of the ith node is parent[i].

Remove every subtree whose sum of values of nodes is zero.

Return the number of the remaining nodes in the tree.

 

Example 1:

![Example 1](./image_1.png)


Input: nodes = 7, parent = [-1,0,0,1,2,2,2], value = [1,-2,4,0,-2,-1,-1]
Output: 2


Example 2:


Input: nodes = 7, parent = [-1,0,0,1,2,2,2], value = [1,-2,4,0,-2,-1,-2]
Output: 6


 

Constraints:

 * 1 <= nodes <= 104
 * parent.length == nodes
 * 0 <= parent[i] <= nodes - 1
 * parent[0] == -1 which indicates that 0 is the root.
 * value.length == nodes
 * -105 <= value[i] <= 105
 * The given input is guaranteed to represent a valid tree.

---

## Images

- Image 1: `image_1.png`
