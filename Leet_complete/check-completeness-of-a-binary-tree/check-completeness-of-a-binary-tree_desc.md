Can you solve this real interview question? Check Completeness of a Binary Tree - Given the root of a binary tree, determine if it is a complete binary tree.

In a complete binary tree [http://en.wikipedia.org/wiki/Binary_tree#Types_of_binary_trees], every level, except possibly the last, is completely filled, and all nodes in the last level are as far left as possible. It can have between 1 and 2h nodes inclusive at the last level h.

 

Example 1:

![Example 1](./image_1.png)


Input: root = [1,2,3,4,5,6]
Output: true
Explanation: Every level before the last is full (ie. levels with node-values {1} and {2, 3}), and all nodes in the last level ({4, 5, 6}) are as far left as possible.


Example 2:

![Example 2](./image_2.png)


Input: root = [1,2,3,4,5,null,7]
Output: false
Explanation: The node with value 7 isn't as far left as possible.


 

Constraints:

 * The number of nodes in the tree is in the range [1, 100].
 * 1 <= Node.val <= 1000

---

## Images

- Image 1: `image_1.png`
- Image 2: `image_2.png`
