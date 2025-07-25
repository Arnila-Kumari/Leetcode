Can you solve this real interview question? Sum of Nodes with Even-Valued Grandparent - Given the root of a binary tree, return the sum of values of nodes with an even-valued grandparent. If there are no nodes with an even-valued grandparent, return 0.

A grandparent of a node is the parent of its parent if it exists.

 

Example 1:

![Example 1](./image_1.png)


Input: root = [6,7,8,2,7,1,3,9,null,1,4,null,null,null,5]
Output: 18
Explanation: The red nodes are the nodes with even-value grandparent while the blue nodes are the even-value grandparents.


Example 2:

![Example 2](./image_2.png)


Input: root = [1]
Output: 0


 

Constraints:

 * The number of nodes in the tree is in the range [1, 104].
 * 1 <= Node.val <= 100

---

## Images

- Image 1: `image_1.png`
- Image 2: `image_2.png`
