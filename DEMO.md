# Markdown Feature Demo

A polished sample document for testing terminal Markdown rendering in `cat-md`.

> [!NOTE]
> This sample document covers typical Markdown features used in project notes and technical docs.

## Table of Contents

1. [Images](#images)
2. [Headings and Text](#headings-and-text)
3. [Lists and Task Lists](#lists-and-task-lists)
4. [Links](#links)
5. [Blockquotes and Callouts](#blockquotes-and-callouts)
6. [Code and Syntax Highlighting](#code-and-syntax-highlighting)
7. [Tables](#tables)

---

## Images

![Bender pointing on the moon](assets/examples/bender-moon.png)

---

## Headings and Text

### Heading Level 3

#### Heading Level 4

##### Heading Level 5

###### Heading Level 6

This paragraph contains **bold**, *italic*, ***bold italic***, ~~strikethrough~~, and `inline code`.

You can also combine styles like **bold with `code` inside** and links like [inline links](https://github.com/parf/Kitty-Markdown-Viewer).

---

## Lists and Task Lists

### Unordered List

- Terminal confetti budget approved
- Documentation drafted with only minor wizardry
- Review items:
  - Confirm launch date with the calendar spirits
  - Confirm owner for QA victory dance
  - Confirm rollback checklist is not decorative

### Ordered List

1. Name the feature before it names itself
2. Build a prototype that looks accidentally finished
3. Run validation until the edge cases confess
4. Publish notes with exactly one dramatic flourish

### Task List

- [x] Teach the terminal to purr in OSC 8
- [x] Add suspiciously polished code samples
- [ ] Convince legal that emoji checkboxes are binding
- [ ] Ship before the coffee gets cold

---

## Links

Inline: [Project homepage](https://github.com/parf/Kitty-Markdown-Viewer "Project repository")

Repository: <https://github.com/parf/Kitty-Markdown-Viewer>

Email: <sergey.porfiriev@gmail.com>

Reference style: [Renderer roadmap][roadmap]

---

## Blockquotes and Callouts

> A clear release note is better than a long release note.
>
> - Engineering Handbook

> [!TIP]
> Keep checklists short and observable.

> [!WARNING]
> Do not deploy irreversible data migrations without a rollback plan.

Nested quote:

> Terminal wisdom
> > Pretty output counts as morale
> > Fast feedback prevents heroic debugging

---

## Code and Syntax Highlighting

Inline command: `cat-md DEMO.md`

```bash
# Render the demo
cat-md DEMO.md
cat DEMO.md | cat-md
```

```python
def crackSHA3(payload: str, rounds: int) -> str:
    return f"{payload} survived {rounds} theatrical hashes"


if __name__ == "__main__":
    print(crackSHA3("Morgan", 7))
```

```cpp
#include <iostream>
#include <string>

std::string forgeQuantumBadge(const std::string& name, int entropy_bits) {
    return name + " unlocked " + std::to_string(entropy_bits) + " entropy bits";
}

int main() {
    std::cout << forgeQuantumBadge("Taylor", 42) << std::endl;
}
```

```rust
fn defuseYamlKraken(name: &str, anchors: usize) -> String {
    format!("{name} defused {anchors} suspicious anchors")
}

fn main() {
    println!("{}", defuseYamlKraken("Jordan", 108));
}
```

```php
<?php

function summonCacheDragon(string $name, int $cacheHits): string {
    return "{$name} summoned {$cacheHits} cache sparks";
}

echo summonCacheDragon("Riley", 1204) . PHP_EOL;
```

```html
<section class="summary" data-count="1204">
  <h2>Renderer demo</h2>
  <a href="https://github.com/parf/Kitty-Markdown-Viewer">Project homepage</a>
</section>
```

```json
{
  "name": "cat-md-demo",
  "version": "1.0.0",
  "features": ["kitty-headings", "osc8-links", "inline-images", "callouts", "tables"]
}
```

```diff
- status: pending
+ status: shipped
```

## Tables

| Milestone | Owner | Due Date   | Status      |
| :-------- | :---- | :--------- | :---------- |
| Glyph Lab | Morgan | 2026-06-08 | Complete    |
| Link Forge | Taylor | 2026-06-15 | In Progress |
| Moon Launch | Jordan | 2026-06-22 | Planned     |

| Left aligned | Center aligned | Right aligned |
| :----------- | :------------: | ------------: |
| giant titles |     loud       |             7 |
| warning bells |   glowing    |            42 |
| table boxes  |    squared    |           108 |
| parser gears |    humming    |          1204 |
| render polish |  sparkling   |         48217 |
| image portals |   embedded   |        309884 |
| link lasers  |   clickable   |     431204928 |

[roadmap]: https://github.com/parf/Kitty-Markdown-Viewer "Renderer roadmap"
