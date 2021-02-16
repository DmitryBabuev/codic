class Solution:
    def maxProfit(self, prices: list) -> int:
        profit = 0
        current_active = 0
        i = 0
        bought_flag = False
        while i < len(prices):
            if i == len(prices) - 1:
                if bought_flag:
                    profit += prices[i] - current_active
                break
            elif prices[i] < prices[i+1] and not bought_flag:
                current_active = prices[i]
                bought_flag = True
            elif bought_flag:
                best_deal, best_deal_index = self.find_next_biggest(prices, i)
                profit += best_deal - current_active
                current_active = 0
                bought_flag = False
                i = best_deal_index + 1
                continue
            i += 1
        return profit

    def find_next_biggest(self, sub_prices: list, start_index):
        value = 0
        index = 0
        for i in range(start_index, len(sub_prices)):
            if sub_prices[i] > value:
                value = sub_prices[i]
                index = i
        return value, index


inp = [1,2]
print(Solution().maxProfit(inp))
