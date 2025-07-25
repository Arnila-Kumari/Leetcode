Can you solve this real interview question? Delete Leaves With a Given Value - Given a binary tree root and an integer target, delete all the leaf nodes with value target.

Note that once you delete a leaf node with value target, if its parent node becomes a leaf node and has the value target, it should also be deleted (you need to continue doing that until you cannot).

 

Example 1:

![Example 1](./image_1.png)


Input: root = [1,2,3,2,null,2,4], target = 2
Output: [1,null,3,null,4]
Explanation: Leaf nodes in green with value (target = 2) are removed (Picture in left). 
After removing, new nodes become leaf nodes with value (target = 2) (Picture in center).


Example 2:

![Example 2](./image_2.png)


Input: root = [1,3,3,3,2], target = 3
Output: [1,3,null,null,2]


Example 3:

![Example 3](./image_3.png)


Input: root = [1,2,null,2,null,2], target = 2
Output: [1]
Explanation: Leaf nodes in green with value (target = 2) are removed at each step.


 

Constraints:

 * The number of nodes in the tree is in the range [1, 3000].
 * 1 <= Node.val, target <= 1000

---

## Images

- Image 1: `image_1.png`
- Image 2: `image_2.png`
- Image 3: `image_3.png`
