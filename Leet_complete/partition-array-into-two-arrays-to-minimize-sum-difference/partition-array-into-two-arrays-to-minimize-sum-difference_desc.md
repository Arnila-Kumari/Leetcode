Can you solve this real interview question? Partition Array Into Two Arrays to Minimize Sum Difference - You are given an integer array nums of 2 * n integers. You need to partition nums into two arrays of length n to minimize the absolute difference of the sums of the arrays. To partition nums, put each element of nums into one of the two arrays.

Return the minimum possible absolute difference.

 

Example 1:

example-1 ![Example 1](./image_1.png)


Input: nums = [3,9,7,3]
Output: 2
Explanation: One optimal partition is: [3,9] and [7,3].
The absolute difference between the sums of the arrays is abs((3 + 9) - (7 + 3)) = 2.


Example 2:


Input: nums = [-36,36]
Output: 72
Explanation: One optimal partition is: [-36] and [36].
The absolute difference between the sums of the arrays is abs((-36) - (36)) = 72.


Example 3:

example-3 ![Example 2](./image_2.png)


Input: nums = [2,-1,0,4,-2,-9]
Output: 0
Explanation: One optimal partition is: [2,4,-9] and [-1,0,-2].
The absolute difference between the sums of the arrays is abs((2 + 4 + -9) - (-1 + 0 + -2)) = 0.


 

Constraints:

 * 1 <= n <= 15
 * nums.length == 2 * n
 * -107 <= nums[i] <= 107

---

## Images

- Image 1: `image_1.png`
- Image 2: `image_2.png`
