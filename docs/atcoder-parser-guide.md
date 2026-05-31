# AtCoder Parser Guide

How to parse algorithmic tasks and their editorials from AtCoder. Scope: **English content only** (`?lang=en`), text editorials only (video editorials skipped).

## 1. URL scheme

A contest is identified by a **contest type** + **number**. The type must be a separate variable, because AtCoder has several contest series (`abc`, `arc`, `agc`, ...).

```python
contest_type = "abc"          # "abc" | "arc" | "agc" | "ahc" | ...
number       = 460
contest_id   = f"{contest_type}{number}"   # "abc460"

TASKS_URL     = f"https://atcoder.jp/contests/{contest_id}/tasks?lang=en"
EDITORIAL_URL = f"https://atcoder.jp/contests/{contest_id}/editorial?lang=en"
TASK_URL      = f"https://atcoder.jp/contests/{contest_id}/tasks/{contest_id}_a?lang=en"
```

Always append `?lang=en`. English is the target; pages still ship Japanese DOM nodes (see notes), so language must be filtered explicitly.

## 2. Task list — `/contests/{id}/tasks`

Tasks live in a single table:

```
table.table-bordered.table-striped > tbody > tr
```

Each `<tr>` has 4 `<td>`:

| td index | content | selector |
|----------|---------|----------|
| 0 | task letter (`A`) + link | `td:nth-child(1) a` |
| 1 | task title (`Mod While Positive`) | `td:nth-child(2) a` |
| 2 | time limit (`2 sec`) | `td:nth-child(3)` |
| 3 | memory limit (`1024 MiB`) | `td:nth-child(4)` |

The href is the same on both links: `/contests/abc460/tasks/abc460_a`.
The **task slug** is the last path segment (`abc460_a`); the letter is the part after `_`.

```html
<td class="text-center no-break"><a href="/contests/abc460/tasks/abc460_a">A</a></td>
<td><a href="/contests/abc460/tasks/abc460_a">Mod While Positive</a></td>
<td class="text-right">2 sec</td>
<td class="text-right">1024 MiB</td>
```

Output: `[(letter, title, task_url), ...]`.

## 3. Task statement — task page

The statement lives in `div#task-statement`. It contains **two** language blocks:

```
#task-statement span.lang-ja      ← skip
#task-statement span.lang-en      ← keep this one
```

Inside the English block, content is split into `div.part` blocks. The `<h3>` inside each part is the section name:

| English `<h3>` | meaning |
|----------------|---------|
| Problem Statement | statement body |
| Constraints | constraints |
| Input | input format |
| Output | output format |
| Sample Input N | sample input #N — text in `<pre>` |
| Sample Output N | sample output #N — text in `<pre>` |

Notes:
- Math is rendered with MathJax: `<var>N</var>` and `\( ... \)`. Keep the raw text or convert as needed.
- Sample I/O is plain text inside `<pre>`.

```html
<span class="lang-en">
  <div class="part"><h3>Problem Statement</h3><p>...</p></div>
  <div class="part"><h3>Constraints</h3><ul>...</ul></div>
  <div class="io-style">
    <div class="part"><h3>Input</h3>...</div>
    <div class="part"><h3>Output</h3>...</div>
  </div>
  <div class="part"><h3>Sample Input 1</h3><pre>8 5</pre></div>
  <div class="part"><h3>Sample Output 1</h3><pre>3</pre></div>
  ...
</span>
```

## 4. Editorial index — `/contests/{id}/editorial`

There is **no table**. The page is a repeating sequence of `<h3>` + `div.editorial-section`:

- `<h3>Overall Editorial</h3>` — whole-contest editorial; skip (usually video).
- `<h3>A - Mod While Positive <a href="/contests/abc460/tasks/abc460_a">…</a></h3>` — per-task header.
  - Task letter + title are in the `<h3>` text.
  - The inner `<a>` links back to the task page.
- The following `div.editorial-section > ul > li` are the editorial entries for that task.

Per `<li>`:

```html
<li>
  <span class="label label-default">Official</span>
  <a href="/contests/abc460/editorial/21036" target="_blank">Editorial</a>
  <span class="grey">by</span>
  <a href="/users/en_translator" class="username">en_translator</a>
</li>
```

- `a[href]` — the editorial link
- `span.label` — `Official` / `User`
- `a.username` — author
- `li.lang-other` — a **non-primary-language** entry (hidden by default via JS). Japanese 解説 entries carry this class; the English `Editorial` `<li>` does **not**.

### Filtering rules (English text only)

For each `<li>`, **keep** only when ALL hold:

1. **Text, not video** — href matches `^/contests/{id}/editorial/\d+$`.
   Skip video / external: those have `href="/jump?url=..."` **and** a `<span class="glyphicon glyphicon-film">` inside the `<a>`.
2. **English** — the `<li>` is **not** `class="lang-other"` (Japanese entries are `lang-other`; the English official editorial is plain `<li>`).

```python
def is_english_text_editorial(li, contest_id):
    a = li.select_one("a[href]")
    href = a["href"]
    is_text  = re.match(rf"^/contests/{contest_id}/editorial/\d+$", href)
    is_video = a.select_one("span.glyphicon-film") is not None or href.startswith("/jump")
    is_english = "lang-other" not in li.get("class", [])
    return bool(is_text) and not is_video and is_english
```

Output: `[(letter, [editorial_url, ...]), ...]`.

## 5. Editorial detail — `/contests/{id}/editorial/NNNN`

Fetch with `?lang=en`.

- Title: `h2.mt-1` → contains task link + the word "Editorial", author in `span.small`.
- Body: the first `<div>` after `<hr class="mt-1">`.
- **Do not read the editorial code.** Drop `<pre class="prettyprint linenums">` blocks (these are sample solution code). Keep `<p>`, math, lists.
- Body ends at `div.clearfix` (the "posted / last update" footer) — cut there.

```html
<h2 class="mt-1">
  <a href="/contests/abc460/tasks/abc460_a">A - Mod While Positive</a> Editorial
  <span class="small">by <a class="username">en_translator</a></span>
</h2>
<hr class="mt-1">
<div>
  <p>... explanation text ...</p>
  <pre class="prettyprint linenums"><code>... SKIP THIS ...</code></pre>
</div>
<div class="clearfix"> ... posted / last update ... </div>   ← stop here
```

## 6. End-to-end pipeline

```
1. GET tasks?lang=en
     → [(letter, title, task_url)]

2. (optional) GET each task_url?lang=en
     → parse #task-statement span.lang-en into sections

3. GET editorial?lang=en
     → for each per-task <h3> + editorial-section:
          li = filter(is_english_text_editorial)   # text + english only
       → [(letter, [editorial_url, ...])]

4. GET each editorial_url?lang=en
     → take h2.mt-1 title + body div after hr.mt-1
     → strip pre.prettyprint blocks
     → stop at div.clearfix
     → editorial text
```

## 7. Notes & gotchas

- **Language**: `?lang=en` sets the *default*, but the editorial index still contains Japanese `<li class="lang-other">` nodes in the DOM (hidden by JS, not removed). Filter by the `lang-other` class — do not rely on visual hiding.
- **Multiple editorials per task**: a task may have several entries (ja 解説, en Editorial, user editorial). After filtering you typically keep one English official editorial, sometimes plus an English user editorial (`span.label` = `User`).
- **Video editorials are skipped** entirely (e.g. ABC300 has many) — detected by `/jump?url=` href + `glyphicon-film`.
- **Contest type as variable**: keep `contest_type` separate from `number` so the same parser handles `abc`, `arc`, `agc`, etc.
- **Politeness / rate limiting**: AtCoder throttles aggressive scraping. Send a real `User-Agent`, add a delay between requests.
- **Parsing lib**: `BeautifulSoup` (lxml) — all selectors above are direct CSS selectors.