# Contributing

Thank you for your interest in UniUbi robotics projects.

Please keep contributions focused and easy to review:

1. Open an issue for larger API, behavior, or directory changes.
2. Include tests, examples, or reproduction steps when applicable.
3. Do not commit secrets, credentials, calibration data, private datasets, or unreviewed vendor binaries.
4. Document compatibility and safety impact for user-facing changes.
5. By contributing, you agree that your contribution will be licensed under this repository's license.

## How-to authoring

New or substantially revised How-to guides should cover goal and scope,
prerequisites, a minimal procedure, expected results, success criteria, safety
and cleanup, troubleshooting, and next steps. Every executable step must have
an observable result. Keep English and Simplified Chinese guides synchronized.

新增或大幅修订 How-to 时，应覆盖目标与范围、前置条件、最小步骤、预期
结果、成功标准、安全与清理、失败排查和继续阅读。每个可执行步骤都必须
绑定可观察结果，中英文版本必须同步更新。

## Offline documentation checks

Run from the repository root with Python 3.9 or newer:

```sh
python3 scripts/check_docs.py --self-test
python3 scripts/check_docs.py
git diff --check
```

GitHub Actions runs the Python checks and checks committed whitespace over the
PR base-to-HEAD range or push before-to-HEAD range. A new branch push checks the
latest commit, including root commits. Locally, `git diff --check` checks
uncommitted changes. The checker validates local Markdown
inline links (including images), links to this repository on GitHub
`blob/main`, `raw/main`, and `raw.githubusercontent.com`, Markdown heading
anchors and explicit HTML `id`/`name` anchors, fenced code block closure, and
English/Simplified Chinese file pairs under `docs/` and for root README/CONTEXT.
Code fences and inline code are excluded from link checks. Heading anchors
retain Chinese characters and use numeric suffixes for repeated headings.

This is a bounded structural checker, not a complete Markdown parser: reference
links, HTML links, multiline link syntax, and renderer-specific extensions are
outside its parsing scope. It does not fetch external sites, inspect targets in
other repositories, execute examples, prove translation semantic equivalence,
or establish successful real-robot validation. Review those separately and
record the actual validation evidence in the pull request.

离线检查只验证本仓库链接目标和文档结构；中英文文件配对不代表翻译语义
一致，也不代表示例已执行或真机验证通过。请在 PR 中记录对应的人工审阅
与实际验证证据。
