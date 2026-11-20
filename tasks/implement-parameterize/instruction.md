# Implement `parameterize`

In the `inflection` library in `/app`, the body of `parameterize` has been removed. Implement it.

`parameterize(string, separator='-')` turns arbitrary text into a URL slug.
It must behave exactly as follows:

1. Transliterate: apply Unicode NFKD normalisation, then drop every character
   that is not ASCII (the existing `transliterate()` helper does this).
2. Replace every maximal run of characters that are **not** ASCII letters,
   ASCII digits, `-` or `_` with a single `separator`. (`-` and `_` in the
   input are kept as they are, whatever the separator is.)
3. If `separator` is not empty:
   - collapse any run of two or more consecutive `separator` characters into
     one `separator`;
   - then remove one leading `separator` and one trailing `separator`, if
     present.
4. Lower-case the result.

Callers only ever pass a single-character separator or the empty string.

Examples:

```
parameterize("Donald E. Knuth")              -> "donald-e-knuth"
parameterize("Trailing bad characters!@#")   -> "trailing-bad-characters"
parameterize("Squeeze   separators")         -> "squeeze-separators"
parameterize("Malmö")                        -> "malmo"
parameterize("Donald E. Knuth", "_")         -> "donald_e_knuth"
parameterize("With-some-dashes", "_")        -> "with-some-dashes"
parameterize("Donald E. Knuth", "")          -> "donaldeknuth"
parameterize("a -- b")                       -> "a-b"
```

## Rules

- Work in `/app`. The library is `/app/inflection/__init__.py`.
- **Only `/app/inflection/__init__.py` is graded.** Put your whole fix in that
  file; other files you create or edit are ignored.
- Keep every public function name and signature unchanged, and keep the
  library dependency-free (standard library only).
- A few visible tests are in `/app/tests` (`cd /app && python -m pytest -q`).
  They are deliberately incomplete. The hidden grader checks many more inputs,
  including randomly generated ones, and also checks that every other function
  in the library still behaves correctly.
