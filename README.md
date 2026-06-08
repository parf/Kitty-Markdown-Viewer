# Cat Markdown Viewer

`cat-md` renders Markdown with kitty terminal features: large headings, clickable links, inline images, and Unicode boxed tables.

```bash
cat-md
cat README.md | cat-md
cat-md README.md
cat-md file1.md - file2.md
cat-md https://example.com/README.md
```

Running `cat-md` with no arguments in an interactive terminal shows help. When stdin is piped, no-argument mode renders the piped Markdown. Use `-` to read stdin explicitly among other inputs.

Config is created silently on first run at:

```text
~/.config/cat-md/config.toml
~/.config/cat-md/themes/dark.toml
~/.config/cat-md/themes/light.toml
```

`cat-md --init-config` creates the same files but refuses to overwrite existing files.

Build a Python-required single executable:

```bash
python3 scripts/build_zipapp.py
./dist/cat-md README.md
```
