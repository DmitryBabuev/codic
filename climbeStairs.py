import math


class Solution:
    def climbStairs_old(self, n: int):
        one_step = 0
        two_steps = 0
        if n == 0:
            return 1
        if n >= 1:
            one_step = self.climbStairs_old(n - 1)
            if n >= 2:
                two_steps = self.climbStairs_old(n-2)
        return one_step + two_steps

    def climbStairs(self, n: int):
        return round((((1+math.sqrt(5))/2) ** (n+1)) / math.sqrt(5))

n = 4
print(Solution().climbStairs_old(n))
print(Solution().climbStairs(n))

