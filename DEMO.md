# Markdown Feature Demo

A polished sample document for testing terminal Markdown rendering in `cat-md`.

> [!NOTE]
> This demo intentionally focuses on features that currently render cleanly in the terminal.

## Table of Contents

1. [Headings and Text](#headings-and-text)
2. [Lists and Task Lists](#lists-and-task-lists)
3. [Links](#links)
4. [Blockquotes and Callouts](#blockquotes-and-callouts)
5. [Code and Syntax Highlighting](#code-and-syntax-highlighting)
6. [Tables](#tables)

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

- Project kickoff complete
- Documentation drafted
- Review items:
  - Confirm release date
  - Confirm owner for QA
  - Confirm rollout checklist

### Ordered List

1. Define scope
2. Build prototype
3. Run validation
4. Publish notes

### Task List

- [x] Create initial brief
- [x] Add code samples
- [ ] Final legal review
- [ ] Publish release blog

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

> Quarter goals
> > Stability first
> > Improve developer feedback loops

---

## Code and Syntax Highlighting

Inline command: `cat-md DEMO.md`

```bash
# Render the demo
cat-md DEMO.md
cat DEMO.md | cat-md
```

```python
def summarize(name: str, tasks_done: int) -> str:
    return f"{name} completed {tasks_done} tasks"


if __name__ == "__main__":
    print(summarize("Morgan", 7))
```

```cpp
#include <iostream>
#include <string>

std::string summarize(const std::string& name, int tasks_done) {
    return name + " completed " + std::to_string(tasks_done) + " tasks";
}

int main() {
    std::cout << summarize("Taylor", 42) << std::endl;
}
```

```rust
fn summarize(name: &str, tasks_done: usize) -> String {
    format!("{name} completed {tasks_done} tasks")
}

fn main() {
    println!("{}", summarize("Jordan", 108));
}
```

```php
<?php

function summarize(string $name, int $tasksDone): string {
    return "{$name} completed {$tasksDone} tasks";
}

echo summarize("Riley", 1204) . PHP_EOL;
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

---

## Tables

| Milestone | Owner | Due Date   | Status      |
| :-------- | :---- | :--------- | :---------- |
| Spec      | Morgan | 2026-06-08 | Complete    |
| MVP       | Taylor | 2026-06-15 | In Progress |
| Launch    | Jordan | 2026-06-22 | Planned     |

| Left aligned | Center aligned | Right aligned |
| :----------- | :------------: | ------------: |
| headings     |      big       |             7 |
| callouts     |    styled      |            42 |
| tables       |     boxed      |           108 |
| parser       |     ready      |          1204 |
| renderer     |    polished    |         48217 |
| images       |    embedded    |        309884 |
| links        |   clickable    |     431204928 |

[roadmap]: https://github.com/parf/Kitty-Markdown-Viewer "Renderer roadmap"
