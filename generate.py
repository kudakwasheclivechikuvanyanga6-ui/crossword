
import sys

from crossword import Crossword, Variable


class CrosswordCreator:

    def __init__(self, crossword):
        self.crossword = crossword
        self.domains = {
            variable: set(crossword.words)
            for variable in crossword.variables
        }

    def print(self, assignment):
        crossword = self.crossword
        letters = self.letter_grid(assignment)

        for i in range(crossword.height):
            for j in range(crossword.width):
                if crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        from PIL import Image, ImageDraw, ImageFont

        crossword = self.crossword
        letters = self.letter_grid(assignment)

        cell_size = 100
        cell_border = 2

        image = Image.new(
            "RGBA",
            (
                crossword.width * cell_size,
                crossword.height * cell_size
            ),
            "black"
        )

        font = ImageFont.truetype(
            "assets/fonts/OpenSans-Regular.ttf", 80
        )

        draw = ImageDraw.Draw(image)

        for i in range(crossword.height):
            for j in range(crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]

                if crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")

                    if letters[i][j]:
                        _, _, w, h = draw.textbbox(
                            (0, 0), letters[i][j], font=font
                        )

                        draw.text(
                            (
                                rect[0][0] + (cell_size - w) / 2,
                                rect[0][1] + (cell_size - h) / 2 - 10
                            ),
                            letters[i][j],
                            fill="black",
                            font=font
                        )

        image.save(filename)

    def letter_grid(self, assignment):
        crossword = self.crossword

        letters = [
            [None for _ in range(crossword.width)]
            for _ in range(crossword.height)
        ]

        for variable, word in assignment.items():
            for k in range(len(word)):
                i = variable.i
                j = variable.j

                if variable.direction == Variable.ACROSS:
                    j += k
                else:
                    i += k

                letters[i][j] = word[k]

        return letters

    def enforce_node_consistency(self):
        for variable in self.domains:
            self.domains[variable] = {
                word
                for word in self.domains[variable]
                if len(word) == variable.length
            }

    def revise(self, x, y):
        revised = False
        overlap = self.crossword.overlaps[x, y]

        if overlap is None:
            return False

        i, j = overlap

        for word_x in set(self.domains[x]):
            if not any(
                word_x[i] == word_y[j]
                for word_y in self.domains[y]
            ):
                self.domains[x].remove(word_x)
                revised = True

        return revised

    def ac3(self, arcs=None):
        if arcs is None:
            queue = [
                (x, y)
                for x in self.crossword.variables
                for y in self.crossword.neighbors(x)
            ]
        else:
            queue = list(arcs)

        while queue:
            x, y = queue.pop(0)

            if self.revise(x, y):
                if not self.domains[x]:
                    return False

                for neighbor in self.crossword.neighbors(x):
                    if neighbor != y:
                        queue.append((neighbor, x))

        return True

    def assignment_complete(self, assignment):
        return set(assignment) == self.crossword.variables

    def consistent(self, assignment):
        words = list(assignment.values())

        if len(words) != len(set(words)):
            return False

        for variable, word in assignment.items():
            if len(word) != variable.length:
                return False

            for neighbor in self.crossword.neighbors(variable):
                if neighbor not in assignment:
                    continue

                overlap = self.crossword.overlaps[
                    variable, neighbor
                ]

                i, j = overlap

                if word[i] != assignment[neighbor][j]:
                    return False

        return True

    def order_domain_values(self, var, assignment):
        def conflicts(word):
            count = 0

            for neighbor in self.crossword.neighbors(var):
                if neighbor in assignment:
                    continue

                overlap = self.crossword.overlaps[var, neighbor]

                if overlap is None:
                    continue

                i, j = overlap

                for neighbor_word in self.domains[neighbor]:
                    if word[i] != neighbor_word[j]:
                        count += 1

            return count

        return sorted(self.domains[var], key=conflicts)

    def select_unassigned_variable(self, assignment):
        unassigned = [
            variable
            for variable in self.crossword.variables
            if variable not in assignment
        ]

        return min(
            unassigned,
            key=lambda variable: (
                len(self.domains[variable]),
                -len(self.crossword.neighbors(variable))
            )
        )

    def backtrack(self, assignment):
        if self.assignment_complete(assignment):
            return assignment

        variable = self.select_unassigned_variable(assignment)

        for value in self.order_domain_values(variable, assignment):
            new_assignment = assignment.copy()
            new_assignment[variable] = value

            if self.consistent(new_assignment):
                result = self.backtrack(new_assignment)

                if result is not None:
                    return result

        return None

    def solve(self):
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack({})


def main():
    if len(sys.argv) not in [3, 4]:
        sys.exit(
            "Usage: python generate.py "
            "structure words [output]"
        )

    crossword = Crossword(sys.argv[1], sys.argv[2])
    creator = CrosswordCreator(crossword)

    assignment = creator.solve()

    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)

        if len(sys.argv) == 4:
            creator.save(assignment, sys.argv[3])


if __name__ == "__main__":
    main()
