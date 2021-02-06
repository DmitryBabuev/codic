class Solution:
    def computeArea(self, A: int, B: int, C: int, D: int, E: int, F: int, G: int, H: int):
        grid = []
        sub_cubes = []
        sub_cubes_map = {}
        cubes = [((A, B), (C, D)), ((E, F), (G, H))]
        for x in sorted([A, C, E, G]):
            for y in sorted([B, D, F, H]):
                grid.append((x, y))
        j = 0
        for i in range(len(grid)):
            if i == 11:
                break
            if j == 3:
                j = 0
                continue
            sub_cube = (grid[i], grid[i+5])
            for k in cubes:
                if self.if_in(k, sub_cube):
                    if sub_cube not in sub_cubes_map:
                        sub_cubes_map.setdefault(sub_cube, self.area(sub_cube))
            j += 1
        result = 0
        for cube in sub_cubes_map.items():
            _, value = cube
            result += value
        return result

    def if_in(self, default_cube, tested_cube):
        if default_cube[0][0] <= tested_cube[0][0] and default_cube[0][1] <= tested_cube[0][1]:
            if default_cube[1][0] >= tested_cube[1][0] and default_cube[1][1] >= tested_cube[1][1]:
                return True
        return False

    def area(self, cube):
        return abs(cube[0][0] - cube[1][0]) * abs(cube[0][1] - cube[1][1])



print(Solution().computeArea(-2,-2,2,2 ,2,2,4,4))

