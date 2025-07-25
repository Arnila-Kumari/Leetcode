Can you solve this real interview question? Validate Binary Tree Nodes - You have n binary tree nodes numbered from 0 to n - 1 where node i has two children leftChild[i] and rightChild[i], return true if and only if all the given nodes form exactly one valid binary tree.

If node i has no left child then leftChild[i] will equal -1, similarly for the right child.

Note that the nodes have no values and that we only use the node numbers in this problem.

 

Example 1:

![Example 1](./image_1.png)


Input: n = 4, leftChild = [1,-1,3,-1], rightChild = [2,-1,-1,-1]
Output: true


Example 2:

![Example 2](./image_2.png)


Input: n = 4, leftChild = [1,-1,3,-1], rightChild = [2,3,-1,-1]
Output: false


Example 3:

![Example 3](./image_3.png)


Input: n = 2, leftChild = [1,0], rightChild = [-1,-1]
Output: false


 

Constraints:

 * n == leftChild.length == rightChild.length
 * 1 <= n <= 104
 * -1 <= leftChild[i], rightChild[i] <= n - 1

---

## Images

- Image 1: `image_1.png`
- Image 2: `image_2.png`
- Image 3: `image_3.png`
