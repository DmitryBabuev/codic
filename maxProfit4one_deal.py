class Solution:
    def maxProfit(self, prices: list) -> int:
        profit = 0
        buy_candidate = float('inf')
        for index, value in enumerate(prices):
            if value < buy_candidate:
                buy_candidate = value
            elif profit < value-buy_candidate:
                profit = value-buy_candidate
        return profit

inp = [7,6,4,3,1]
print(Solution().maxProfit(inp))