# Fix case-conversion bugs

Two bug reports against the `inflection` library in `/app`:

> 1. `inflection.titleize("HTMLTidyGenerator")` returns `'Htmltidy Generator'`
>    instead of `'Html Tidy Generator'`, and
>    `inflection.tableize("HTMLPage")` returns `'htmlpages'` instead of
>    `'html_pages'`.
> 2. `inflection.humanize("paid")` returns `'Pa'` instead of `'Paid'`, while
>    `humanize("author_id")` should still give `'Author'`.

Fix the root causes in the library. Several public functions are built on top
of each other, so check which function is actually responsible before you
change anything.

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
