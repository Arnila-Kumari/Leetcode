Can you solve this real interview question? 01 Matrix - Given an m x n binary matrix mat, return the distance of the nearest 0 for each cell.

The distance between two cells sharing a common edge is 1.

 

Example 1:

![Example 1](./image_1.png)


Input: mat = [[0,0,0],[0,1,0],[0,0,0]]
Output: [[0,0,0],[0,1,0],[0,0,0]]


Example 2:

![Example 2](./image_2.png)


Input: mat = [[0,0,0],[0,1,0],[1,1,1]]
Output: [[0,0,0],[0,1,0],[1,2,1]]


 

Constraints:

 * m == mat.length
 * n == mat[i].length
 * 1 <= m, n <= 104
 * 1 <= m * n <= 104
 * mat[i][j] is either 0 or 1.
 * There is at least one 0 in mat.

 

Note: This question is the same as 1765: https://leetcode.com/problems/map-of-highest-peak/ [https://leetcode.com/problems/map-of-highest-peak/description/]

---

## Images

- Image 1: `image_1.png`
- Image 2: `image_2.png`
