Can you solve this real interview question? Clone N-ary Tree - Given a root of an N-ary tree, return a deep copy [https://en.wikipedia.org/wiki/Object_copying#Deep_copy] (clone) of the tree.

Each node in the n-ary tree contains a val (int) and a list (List[Node]) of its children.


class Node {
    public int val;
    public List<Node> children;
}


Nary-Tree input serialization is represented in their level order traversal, each group of children is separated by the null value (See examples).

 

Example 1:

![Example 1](./image_1.png)


Input: root = [1,null,3,2,4,null,5,6]
Output: [1,null,3,2,4,null,5,6]


Example 2:

![Example 2](./image_2.png)


Input: root = [1,null,2,3,4,5,null,null,6,7,null,8,null,9,10,null,null,11,null,12,null,13,null,null,14]
Output: [1,null,2,3,4,5,null,null,6,7,null,8,null,9,10,null,null,11,null,12,null,13,null,null,14]


 

Constraints:

 * The depth of the n-ary tree is less than or equal to 1000.
 * The total number of nodes is between [0, 104].

 

Follow up: Can your solution work for the graph problem [https://leetcode.com/problems/clone-graph/]?

---

## Images

- Image 1: `image_1.png`
- Image 2: `image_2.png`
