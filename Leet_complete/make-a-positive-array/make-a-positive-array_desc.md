Can you solve this real interview question? Make a Positive Array - You are given an array nums. An array is considered positive if the sum of all numbers in each subarray with more than two elements is positive.

You can perform the following operation any number of times:

 * Replace one element in nums with any integer between -1018 and 1018.

Find the minimum number of operations needed to make nums positive.

 

Example 1:

Input: nums = [-10,15,-12]

Output: 1

Explanation:

The only subarray with more than 2 elements is the array itself. The sum of all elements is (-10) + 15 + (-12) = -7. By replacing nums[0] with 0, the new sum becomes 0 + 15 + (-12) = 3. Thus, the array is now positive.

Example 2:

Input: nums = [-1,-2,3,-1,2,6]

Output: 1

Explanation:

The only subarrays with more than 2 elements and a non-positive sum are:

Subarray Indices Subarray Sum Subarray After Replacement (Set nums[1] = 1) New Sum nums[0...2] [-1, -2, 3] 0 [-1, 1, 3] 3 nums[0...3] [-1, -2, 3, -1] -1 [-1, 1, 3, -1] 2 nums[1...3] [-2, 3, -1] 0 [1, 3, -1] 3

Thus, nums is positive after one operation.

Example 3:

Input: nums = [1,2,3]

Output: 0

Explanation:

The array is already positive, so no operations are needed.

 

Constraints:

 * 3 <= nums.length <= 105
 * -109 <= nums[i] <= 109