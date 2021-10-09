import math
import re


def similar(a, b):
    # return SequenceMatcher(None, a, b).ratio()
    score = 0
    for word in b.split():  # for every word in your string
        if word in a:  # if it is in your bigger string increase score
            score += 1
    return score


if __name__ == '__main__':
    a = "free the guy"
    b = "free guy"
    print(similar(a, b))
