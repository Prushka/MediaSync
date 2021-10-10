import re

if __name__ == '__main__':
    a = "s0e3"
    b = "abnc"
    pattern = re.compile("^(s\d+e\d+)$")
    print(bool(pattern.match("s190e22")))
    print(re.findall(r'\d+', 's190e22'))