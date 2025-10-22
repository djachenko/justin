from functools import cache
from typing import List, Tuple, Generator
import os


def load_dictionary(file_path: str) -> Generator[str, None, None]:
    """Load a dictionary from a file, yielding each word."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    try:
        with open(file_path, 'r') as file:
            for line in file:
                yield line.strip()
    except IOError as e:
        raise IOError(f"Error occurred while trying to read the file: {file_path}") from e


def damerau_levenshtein_distance(s1: str, s2: str) -> int:
    d = {}
    lenstr1 = len(s1)
    lenstr2 = len(s2)

    for i in range(-1, lenstr1):
        d[i, -1] = i + 1

    for j in range(-1, lenstr2):
        d[-1, j] = j + 1

    for i in range(lenstr1):
        for j in range(lenstr2):
            if s1[i] == s2[j]:
                cost = 0
            else:
                cost = 1

            d[i, j] = min(
                d[i - 1, j] + 1,  # deletion
                d[i, j - 1] + 1,  # insertion
                d[i - 1, j - 1] + cost,  # substitution
            )

            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[i, j] = min(
                    d[i, j],
                    d[i - 2, j - 2] + 1
                )  # transposition

    return d[lenstr1 - 1, lenstr2 - 1]


# noinspection PyPep8Naming
def wf(s1: str, s2: str):
    D = {
        (-1, -1): 0
    }

    M = len(s1)
    N = len(s2)

    insert_price = 1
    delete_price = 1
    replace_price = 1

    rangeN = [i + 1 for i in range(N)]
    rangeM = [i + 1 for i in range(M)]

    for j in range(len(s2)):
        D[-1, j] = D[-1, j - 1] + insert_price

    for i in range(len(s1)):
        D[i, -1] = D[i - 1, -1] + delete_price

        for j in range(len(s2)):
            if s1[i] != s2[j]:
                replace_price = 1
            else:
                replace_price = 0

            D[i, j] = min(
                D[i - 1, j] + delete_price,
                D[i, j - 1] + insert_price,
                D[i - 1, j - 1] + replace_price
            )

    return D[M - 1, N - 1]


def wf_r(s1: str, s2: str) -> int:
    def m(a: str, b: str) -> int:
        if a == b:
            return 0
        else:
            return 1

    @cache
    def D(i: int, j: int) -> int:
        if i == -1 and j == -1:
            return 0

        if i == -1:
            return j + 1

        if j == -1:
            return i + 1

        return min(
            D(i, j - 1) + 1,
            D(i - 1, j) + 1,
            D(i - 1, j - 1) + m(s1[i], s2[j])
        )

    return D(len(s1) - 1, len(s2) - 1)


if __name__ == '__main__':
    print(damerau_levenshtein_distance("polynomial", "exponential"))
    print(damerau_levenshtein_distance("x", "x"))

    exit(0)


def wagner_fischer(word1: str, word2: str, threshold: int) -> float:
    if abs(len(word1) - len(word2)) > threshold:
        return float('inf')

    if len(word1) < len(word2):
        word1, word2 = word2, word1

    previous_row_distances = range(len(word1) + 1)

    for i2, c2 in enumerate(word2):
        current_row_distances = [i2 + 1]
        min_distance = float('inf')

        for i1, c1 in enumerate(word1):
            if c1 == c2:
                current_row_distances.append(previous_row_distances[i1])
            else:
                current_row_distances.append(1 + min(
                    previous_row_distances[i1],
                    previous_row_distances[i1 + 1],
                    current_row_distances[-1]
                ))

            min_distance = min(min_distance, current_row_distances[-1])

        previous_row_distances = current_row_distances

        if min_distance > threshold:
            return float('inf')

    return previous_row_distances[-1]


def spell_check(word: str, dictionary: Generator[str, None, None], top: int, threshold: float) \
        -> List[Tuple[str, float]]:
    results = []

    for w in dictionary:
        if abs(len(word) - len(w)) <= threshold:
            distance = wagner_fischer(word, w, threshold)

            if distance < threshold:
                threshold = distance

            results.append((w, distance))

    return sorted(results, key=lambda x: x[1])[:top]


def print_help():
    print("\n📜 Commands:")
    print("  🔍 check <word> - Check the spelling of a word")
    print("  ⚙️  settings - Display the settings menu")
    print("  🆘 help - Display this help menu")
    print("  🚪 bye - Exit the program")


def print_settings():
    print("\n ⚙️  Settings:")
    print("  📚 dictionary <file_path> - Load a different dictionary file.")
    print("  🎯 threshold <value> - Set the maximum Wagner-Fischer distance for suggestions.")
    print("  🔝 top <number> - Set the number of suggestions to display.")


def user_interface() -> None:
    dictionary = load_dictionary("words.txt")
    threshold = float('inf')
    top = 10

    print("\n🎉 Welcome to the spell checker. Type 'help' for a list of commands.")
    while True:
        command = input("\n🔹 Enter a command: ").strip().lower().split()
        action = command[0]

        if action == 'bye':
            print("\n👋 Exiting the spell checker. Goodbye!")
            break
        elif action == 'check':
            word = ' '.join(command[1:])
            suggestions = spell_check(word, dictionary, top, threshold)
            if suggestions:
                print(f"\n🔝 Top {top} suggestions for '{word}':")
                for i, (word, distance) in enumerate(suggestions):
                    if i == 0:
                        print(f"  ⭐ Closest match: {word} (Distance: {distance})")
                    else:
                        print(f"  - {word} (Distance: {distance})")
            else:
                print(f"\n❌ No suggestions found for '{word}'.")
        elif action == 'help':
            print_help()
        elif action == 'settings':
            print_settings()
        elif action == 'threshold':
            threshold = float(' '.join(command[1:]))
            print(f"\n🎯 Threshold set to {threshold}.")
        elif action == 'dictionary':
            file_path = ' '.join(command[1:])
            dictionary = load_dictionary(file_path)
            print(f"\n📚 Dictionary loaded from {file_path}.")
        elif action == 'top':
            top = int(' '.join(command[1:]))
            print(f"\n🔝 Number of suggestions set to {top}.")
        else:
            print("\n❌ Invalid command. Type 'help' for a list of commands.")


user_interface()
