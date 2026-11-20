# Fix ordinal suffixes

Bug report against the `inflection` library in `/app`:

> `inflection.ordinalize(11)` returns `'11st'`, but it should be `'11th'`.
> The same goes for 12 (`'12th'`) and 13 (`'13th'`), and for numbers such as
> 111, 1012 and -213. Other numbers look right (`'1st'`, `'22nd'`, `'103rd'`).

Find and fix the bug.

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
