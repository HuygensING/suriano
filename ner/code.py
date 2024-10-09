import re


APOS_RE = re.compile(r"""['‘]""")


def normalizeChars(text):
    return APOS_RE.sub("’", text)
