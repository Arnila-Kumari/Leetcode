Can you solve this real interview question? Shortest Distance After Road Addition Queries I - You are given an integer n and a 2D integer array queries.

There are n cities numbered from 0 to n - 1. Initially, there is a unidirectional road from city i to city i + 1 for all 0 <= i < n - 1.

queries[i] = [ui, vi] represents the addition of a new unidirectional road from city ui to city vi. After each query, you need to find the length of the shortest path from city 0 to city n - 1.

Return an array answer where for each i in the range [0, queries.length - 1], answer[i] is the length of the shortest path from city 0 to city n - 1 after processing the first i + 1 queries.

 

Example 1:

Input: n = 5, queries = [[2,4],[0,2],[0,4]]

Output: [3,2,1]

Explanation:

![Example 1](./image_1.png)

After the addition of the road from 2 to 4, the length of the shortest path from 0 to 4 is 3.

![Example 2](./image_2.png)

After the addition of the road from 0 to 2, the length of the shortest path from 0 to 4 is 2.

![Example 3](./image_3.png)

After the addition of the road from 0 to 4, the length of the shortest path from 0 to 4 is 1.

Example 2:

Input: n = 4, queries = [[0,3],[0,2]]

Output: [1,1]

Explanation:

![Example 4](./image_4.png)

After the addition of the road from 0 to 3, the length of the shortest path from 0 to 3 is 1.

![Example 5](./image_5.png)

After the addition of the road from 0 to 2, the length of the shortest path remains 1.

 

Constraints:

 * 3 <= n <= 500
 * 1 <= queries.length <= 500
 * queries[i].length == 2
 * 0 <= queries[i][0] < queries[i][1] < n
 * 1 < queries[i][1] - queries[i][0]
 * There are no repeated roads among the queries.

---

## Images

- Image 1: `image_1.png`
- Image 2: `image_2.png`
- Image 3: `image_3.png`
- Image 4: `image_4.png`
- Image 5: `image_5.png`
