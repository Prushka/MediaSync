import math
import re

if __name__ == '__main__':
    a = "$#123 ab !' the centimer$# $#abbbc$#"
    m = re.findall('\$#(.+?)\$#', a)
    if m:
        for w in m:
            print(w)
