Can you solve this real interview question? Smallest String Starting From Leaf - You are given the root of a binary tree where each node has a value in the range [0, 25] representing the letters 'a' to 'z'.

Return the lexicographically smallest string that starts at a leaf of this tree and ends at the root.

As a reminder, any shorter prefix of a string is lexicographically smaller.

 * For example, "ab" is lexicographically smaller than "aba".

A leaf of a node is a node that has no children.

 

Example 1:

![Example 1](./image_1.png)


Input: root = [0,1,2,3,4,3,4]
Output: "dba"


Example 2:

![Example 2](./image_2.png)


Input: root = [25,1,3,1,3,0,2]
Output: "adz"


Example 3:

![Example 3](./image_3.png)


Input: root = [2,2,1,null,1,0,null,0]
Output: "abc"


 

Constraints:

 * The number of nodes in the tree is in the range [1, 8500].
 * 0 <= Node.val <= 25

---

## Images

- Image 1: `image_1.png`
- Image 2: `image_2.png`
- Image 3: `image_3.png`
