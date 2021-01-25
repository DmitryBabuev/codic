class Solution:
    def __init__(self):
        self.char_map = {}
        self.board = []

    def exist(self, board: list, word: str):
        self.char_map = self.input2map(board)
        self.board = board
        if word[0] not in self.char_map:
            return False
        for index_tuple in self.char_map.get(word[0]):
            i, j = index_tuple
            if self.search(word, i, j, [], 0):
                return True

    def search(self, word, column, row, path, depth):
        char = word[0]
        depth += 1
        path.append((column, row))
        if len(word) == 1:
            return True
        if char not in self.char_map:
            return False
        top = (column+1, row)
        bot = (column-1, row)
        left = (column, row-1)
        right = (column, row+1)
        for index_pair in [top, bot, left, right]:
            i, j = index_pair
            path = path[:depth]
            if (i < 0 or j < 0 or i >= len(self.board) or j >= len(self.board[0])) or index_pair in path: continue
            if self.board[i][j] == word[1]:
                if self.search(word[1:], i, j, path, depth):
                    return True
        return False

    def input2map(self, board):
        char_map = {}
        for i, line in enumerate(board):
            for j, char in enumerate(line):
                if char not in char_map:
                    char_map.setdefault(char, [(i, j)])
                else:
                    char_map.get(char).append((i, j))
        return char_map


if __name__ == '__main__':
    inp = [["C","A","A"],["A","A","A"],["B","C","D"]]
    wrd = "AAB"
    print(Solution().exist(inp, wrd))

""