Can you solve this real interview question? Find a Corresponding Node of a Binary Tree in a Clone of That Tree - Given two binary trees original and cloned and given a reference to a node target in the original tree.

The cloned tree is a copy of the original tree.

Return a reference to the same node in the cloned tree.

Note that you are not allowed to change any of the two trees or the target node and the answer must be a reference to a node in the cloned tree.

 

Example 1:

![Example 1](./image_1.png)


Input: tree = [7,4,3,null,null,6,19], target = 3
Output: 3
Explanation: In all examples the original and cloned trees are shown. The target node is a green node from the original tree. The answer is the yellow node from the cloned tree.


Example 2:

![Example 2](./image_2.png)


Input: tree = [7], target =  7
Output: 7


Example 3:

![Example 3](./image_3.png)


Input: tree = [8,null,6,null,5,null,4,null,3,null,2,null,1], target = 4
Output: 4


 

Constraints:

 * The number of nodes in the tree is in the range [1, 104].
 * The values of the nodes of the tree are unique.
 * target node is a node from the original tree and is not null.

 

Follow up: Could you solve the problem if repeated values on the tree are allowed?

---

## Images

- Image 1: `image_1.png`
- Image 2: `image_2.png`
- Image 3: `image_3.png`
