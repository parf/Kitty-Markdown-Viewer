# 🐱 cat-md

### Markdown that looks like the web — right inside your terminal

*Big headings. Clickable links. Real inline images. Boxed tables. Syntax colors.*
*Powered by [kitty](https://sw.kovidgoyal.net/kitty/)'s modern terminal protocols.*

```bash
cat-md README.md
```

---

## ✨ Why cat-md?

Plain `cat` dumps raw Markdown. Pagers strip the formatting. `cat-md` renders your
`.md` files the way you'd see them in a browser — **without leaving the terminal**.

| 🌐 On the web | 🖥️ In your terminal with `cat-md` |
| :--- | :--- |
| Huge page titles | 🔠 Genuinely **large** H1/H2 headings (not just bold) |
| Clickable hyperlinks | 🔗 Real clickable links — click the label, not the URL |
| Embedded images | 🖼️ Actual inline images via `kitten icat` |
| Styled code blocks | 🎨 Syntax-highlighted code in tidy Unicode boxes |
| Clean tables | 📊 Boxed, aligned, auto-wrapping tables |
| Light / dark pages | 🌗 Auto light/dark theme from your terminal background |

---

## 🚀 Quick start

```bash
cat-md README.md             # render a file
cat README.md | cat-md       # render piped Markdown
cat-md notes.md TODO.md       # render several files in order
cat-md https://example.com/README.md   # render Markdown straight from the web
cat-md a.md - b.md            # mix files with stdin using "-"
```

> 💡 **Tip** — run `cat-md` with no arguments in an interactive shell to see help.
> Pipe something in and it renders the piped Markdown instead.

---

## 🎁 What you get

Everything below renders automatically — no flags, no setup.

### 🔠 Headings that actually look like headings
`# H1` and `## H2` render at real large text scale, `### H3` gets a colored
underline rule, and `H4`–`H6` step down gracefully.

### 🔗 Web-like links
- `[Label](https://…)` → a clickable **Label** (the URL stays hidden, just like the web)
- Bare `https://`, `ftp://`, and `mailto:` links become clickable too — automatically.

### 🖼️ Inline images
`![alt](photo.png)` displays the **real image** in the terminal, with the caption
shown beneath it. Local paths and remote URLs both work.

### 🎨 Code blocks with syntax highlighting
Fenced code is drawn in a clean Unicode box with language-aware colors for:

> `json` · `python` · `rust` · `c++` · `php` · `html` · `bash`/`sh`

…plus `diff` blocks get **red/green** add & remove highlighting. 🟥🟩

### 📊 Tables
GitHub-style pipe tables render as boxed Unicode tables with proper column
alignment (`:--`, `:-:`, `--:`) and automatic cell wrapping to fit your width.

### ✅ Task lists & callouts
- `- [x]` → ✅  and  `- [ ]` → ⬜
- GitHub-style callouts get icons & color:

| Markdown | Renders as |
| :-- | :-- |
| `> [!NOTE]` | 🛈 Note |
| `> [!TIP]` | 💡 Tip |
| `> [!IMPORTANT]` | ⬥ Important |
| `> [!WARNING]` | ⚠️ Warning |
| `> [!CAUTION]` | ⛔ Caution |

### 🪄 Smart text touches
- 📅 **Dates** (`2026-06-08`) are highlighted
- 🔢 **Large numbers** (`431204928`) get readable digit grouping
- 📁 **File paths** are colored
- ✍️ **Footnotes**, **definition lists**, and YAML **front matter** are all handled
- **Bold**, *italic*, ~~strikethrough~~, and `inline code` — as expected

> 🧪 **See it all in action:** `cat-md DEMO.md`

---

## ⚙️ Options

| Flag | What it does |
| :-- | :-- |
| `--theme dark\|light\|detect` | Force a theme (default: detect from terminal background) |
| `--width N` | Render to a fixed column width |
| `--table-style unicode\|plain` | Boxed tables (default) or minimal plain tables |
| `--config PATH` | Use an alternate config file |
| `--init-config` | Create default config & theme files (won't overwrite) |

---

## 🎨 Theming

`cat-md` auto-detects whether your terminal is light or dark and picks a matching
theme. On first run it silently creates editable config and theme files:

```text
~/.config/cat-md/config.toml
~/.config/cat-md/themes/dark.toml
~/.config/cat-md/themes/light.toml
```

Tweak any color in those theme files to taste. To regenerate the defaults
(without clobbering existing files):

```bash
cat-md --init-config
```

---

## 📦 Install

Requires **Python 3.11+** and the **kitty** terminal for the full experience
(large text, images, and clickable links).

```bash
pip install .
```

Or build a single self-contained executable (only needs Python on the target machine):

```bash
python3 scripts/build_zipapp.py
./dist/cat-md README.md
```

---

Made for the terminal that purrs. 🐾

*Renders best in [kitty](https://sw.kovidgoyal.net/kitty/) — other terminals show a graceful subset.*
