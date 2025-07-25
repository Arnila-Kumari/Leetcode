Can you solve this real interview question? Inorder Successor in BST - Given the root of a binary search tree and a node p in it, return the in-order successor of that node in the BST. If the given node has no in-order successor in the tree, return null.

The successor of a node p is the node with the smallest key greater than p.val.

 

Example 1:

![Example 1](./image_1.png)


Input: root = [2,1,3], p = 1
Output: 2
Explanation: 1's in-order successor node is 2. Note that both p and the return value is of TreeNode type.


Example 2:

![Example 2](./image_2.png)


Input: root = [5,3,6,2,4,null,null,1], p = 6
Output: null
Explanation: There is no in-order successor of the current node, so the answer is null.


 

Constraints:

 * The number of nodes in the tree is in the range [1, 104].
 * -105 <= Node.val <= 105
 * All Nodes will have unique values.

---

## Images

- Image 1: `image_1.png`
- Image 2: `image_2.png`
