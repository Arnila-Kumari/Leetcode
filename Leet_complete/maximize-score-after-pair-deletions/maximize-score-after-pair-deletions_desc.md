Can you solve this real interview question? Maximize Score After Pair Deletions - You are given an array of integers nums. You must repeatedly perform one of the following operations while the array has more than two elements:

 * Remove the first two elements.
 * Remove the last two elements.
 * Remove the first and last element.

For each operation, add the sum of the removed elements to your total score.

Return the maximum possible score you can achieve.

 

Example 1:

Input: nums = [2,4,1]

Output: 6

Explanation:

The possible operations are:

 * Remove the first two elements (2 + 4) = 6. The remaining array is [1].
 * Remove the last two elements (4 + 1) = 5. The remaining array is [2].
 * Remove the first and last elements (2 + 1) = 3. The remaining array is [4].

The maximum score is obtained by removing the first two elements, resulting in a final score of 6.

Example 2:

Input: nums = [5,-1,4,2]

Output: 7

Explanation:

The possible operations are:

 * Remove the first and last elements (5 + 2) = 7. The remaining array is [-1, 4].
 * Remove the first two elements (5 + -1) = 4. The remaining array is [4, 2].
 * Remove the last two elements (4 + 2) = 6. The remaining array is [5, -1].

The maximum score is obtained by removing the first and last elements, resulting in a total score of 7.

 

Constraints:

 * 1 <= nums.length <= 105
 * -104 <= nums[i] <= 104