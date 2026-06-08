# Kitty Markdown Viewer

`kitty-md` renders Markdown with kitty terminal features: large headings, clickable links, inline images, and Unicode boxed tables.

```bash
kitty-md
cat README.md | kitty-md
kitty-md README.md
kitty-md file1.md - file2.md
kitty-md https://example.com/README.md
```

Running `kitty-md` with no arguments in an interactive terminal shows help. When stdin is piped, no-argument mode renders the piped Markdown. Use `-` to read stdin explicitly among other inputs.

Config is created silently on first run at:

```text
~/.config/kitty-md/config.toml
~/.config/kitty-md/themes/dark.toml
~/.config/kitty-md/themes/light.toml
```

`kitty-md --init-config` creates the same files but refuses to overwrite existing files.

Build a Python-required single executable:

```bash
python3 scripts/build_zipapp.py
./dist/kitty-md README.md
```
