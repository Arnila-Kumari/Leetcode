Can you solve this real interview question? Maximum Total Area Occupied by Pistons - There are several pistons in an old car engine, and we want to calculate the maximum possible area under the pistons.

You are given:

 * An integer height, representing the maximum height a piston can reach.
 * An integer array positions, where positions[i] is the current position of piston i, which is equal to the current area under it.
 * A string directions, where directions[i] is the current moving direction of piston i, 'U' for up, and 'D' for down.

Each second:

 * Every piston moves in its current direction 1 unit. e.g., if the direction is up, positions[i] is incremented by 1.
 * If a piston has reached one of the ends, i.e., positions[i] == 0 or positions[i] == height, its direction will change.

Return the maximum possible area under all the pistons.

 

Example 1:

Input: height = 5, positions = [2,5], directions = "UD"

Output: 7

Explanation:

The current position of the pistons has the maximum possible area under it.

Example 2:

Input: height = 6, positions = [0,0,6,3], directions = "UUDU"

Output: 15

Explanation:

After 3 seconds, the pistons will be in positions [3, 3, 3, 6], which has the maximum possible area under it.

 

Constraints:

 * 1 <= height <= 106
 * 1 <= positions.length == directions.length <= 105
 * 0 <= positions[i] <= height
 * directions[i] is either 'U' or 'D'.