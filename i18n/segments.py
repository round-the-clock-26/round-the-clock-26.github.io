"""Split the JS bundle into template-literal text segments (between ` and ${ / }).
Returns [(start, end, text)] for every static segment."""
import re

def segments(s):
    out, i, n = [], 0, len(s)
    stack = []  # brace depth per open ${ ... }
    prev = ''   # last significant char outside strings, for regex detection
    def read_tpl(i):
        # i points just after a backtick or after the closing } of ${...}
        start = i
        while i < n:
            c = s[i]
            if c == '\\': i += 2; continue
            if c == '`': out.append((start, i, s[start:i])); return i + 1, False
            if c == '$' and s[i+1:i+2] == '{': out.append((start, i, s[start:i])); return i + 2, True
            i += 1
        raise ValueError('unterminated template')
    depth = 0
    while i < n:
        c = s[i]
        if c == '`':
            i, opened = read_tpl(i + 1)
            if opened: stack.append(depth); depth = 0
            prev = 'x'; continue
        if c in '"\'':
            j = i + 1
            while s[j] != c: j += 2 if s[j] == '\\' else 1
            i = j + 1; prev = 'x'; continue
        if c == '/' and prev in '(,=:[!&|?{};+-*%<>~^' and s[i+1:i+2] not in '/*':
            j, cls = i + 1, False
            while True:
                d = s[j]
                if d == '\\': j += 2; continue
                if d == '[': cls = True
                elif d == ']': cls = False
                elif d == '/' and not cls: break
                j += 1
            i = j + 1; prev = 'x'; continue
        if c == '{': depth += 1
        elif c == '}':
            if depth == 0 and stack:
                depth = stack.pop()
                i, opened = read_tpl(i + 1)
                if opened: stack.append(depth); depth = 0
                prev = 'x'; continue
            depth -= 1
        if not c.isspace(): prev = c if not (c.isalnum() or c in '_$') else 'x'
        if c == ')' or c == ']': prev = 'x'
        i += 1
    assert not stack
    return out

PROSE = re.compile(r'[A-Za-z]{2,}')
def is_text(t):
    if not PROSE.search(t): return False
    if t.startswith(('http', './', '#team')) or t.endswith(('.jpg', '.webp')): return False
    if re.fullmatch(r'[a-z0-9_\-\.\[\]=" :#>*(),]+', t) and ' ' not in t.strip(): return False  # keys, selectors
    if re.fullmatch(r'\[data-[^\]]*\]', t) or t.startswith(('[data-', '.', 'rgb', '--', 'precision', 'attribute vec')): return False
    return True
