Can you solve this real interview question? Maximum Number of Distinct Elements After Operations - You are given an integer array nums and an integer k.

You are allowed to perform the following operation on each element of the array at most once:

 * Add an integer in the range [-k, k] to the element.

Return the maximum possible number of distinct elements in nums after performing the operations.

 

Example 1:

Input: nums = [1,2,2,3,3,4], k = 2

Output: 6

Explanation:

nums changes to [-1, 0, 1, 2, 3, 4] after performing operations on the first four elements.

Example 2:

Input: nums = [4,4,4,4], k = 1

Output: 3

Explanation:

By adding -1 to nums[0] and 1 to nums[1], nums changes to [3, 5, 4, 4].

 

Constraints:

 * 1 <= nums.length <= 105
 * 1 <= nums[i] <= 109
 * 0 <= k <= 109