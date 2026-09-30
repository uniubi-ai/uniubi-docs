#!/usr/bin/env python3
"""Offline structural checks; inline Markdown links are the primary supported syntax."""
import argparse
import html
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPO = "uniubi-ai/uniubi-docs"
LINK = re.compile(r'!?\[(?:[^\]\n]|\\.)*\]\(\s*(<[^>]+>|[^\s()]+(?:\([^()]*\)[^\s()]*)*)(?:\s+["\'][^\n]*?["\'])?\s*\)')

def visible_lines(text):
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if match:
            marker, tail = match.groups()
            if fence is None:
                fence = (marker[0], len(marker), number)
            elif marker[0] == fence[0] and len(marker) >= fence[1] and not tail.strip():
                fence = None
            continue
        if fence is None:
            yield number, line
    if fence:
        raise ValueError(f"line {fence[2]}: unclosed fenced code block")

def slug(text):
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"!?\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = html.unescape(text).lower()
    text = ''.join(c for c in text if c.isalnum() or c in '_- ')
    return text.replace(' ', '-')

def anchors(lines):
    result, counts = set(), {}
    previous = None
    for _, line in lines:
        result.update(re.findall(r'<[^>]+\b(?:id|name)\s*=\s*["\']([^"\']+)["\']', line))
        heading = re.match(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        title = heading.group(1) if heading else None
        if previous and re.match(r"^ {0,3}(?:=+|-+)\s*$", line):
            title = previous.strip()
        if title is not None:
            base = slug(title)
            candidate = base
            index = counts.get(base, 0)
            while candidate in result:
                index += 1
                candidate = f"{base}-{index}"
            counts[base] = index
            result.add(candidate)
        previous = line if line.strip() else None
    return result

def local_target(root, source, href):
    url = urlsplit(html.unescape(href.strip('<>')))
    if url.scheme or url.netloc:
        prefixes = []
        if url.netloc.lower() == 'github.com':
            prefixes = [f'/{REPO}/blob/main/', f'/{REPO}/raw/main/']
        elif url.netloc.lower() == 'raw.githubusercontent.com':
            prefixes = [f'/{REPO}/main/']
        for prefix in prefixes:
            if url.path.startswith(prefix):
                return root / unquote(url.path[len(prefix):]), unquote(url.fragment)
        return None
    path = unquote(url.path)
    if not path:
        return source, unquote(url.fragment)
    return ((root / path.lstrip('/')) if path.startswith('/') else source.parent / path), unquote(url.fragment)

def check(root):
    root = root.resolve()
    errors, parsed = [], {}
    files = sorted(root.rglob('*.md'))
    files = [p for p in files if '.git' not in p.relative_to(root).parts]
    for path in files:
        try:
            parsed[path.resolve()] = list(visible_lines(path.read_text(encoding='utf-8')))
        except ValueError as exc:
            errors.append(f'{path.relative_to(root)}: {exc}')
    for path, lines in parsed.items():
        for number, line in lines:
            # Inline code examples are not documentation links.
            line = re.sub(r'(`+).*?\1', '', line)
            for match in LINK.finditer(line):
                target = local_target(root, path, match.group(1))
                if target is None:
                    continue
                dest, fragment = target
                dest = dest.resolve()
                label = f'{path.relative_to(root)}:{number}: {match.group(1)}'
                if not dest.is_relative_to(root):
                    errors.append(f'{label}: target escapes repository')
                elif not dest.exists():
                    errors.append(f'{label}: missing target')
                elif fragment and dest.suffix.lower() == '.md':
                    if dest not in parsed:
                        errors.append(f'{label}: target Markdown could not be parsed')
                    elif fragment not in anchors(parsed[dest]):
                        errors.append(f'{label}: missing anchor #{fragment}')
    paired = [p for p in files if p.is_relative_to(root / 'docs') or p.name in ('README.md', 'README.zh-CN.md', 'CONTEXT.md', 'CONTEXT.zh-CN.md') and p.parent == root]
    for path in paired:
        name = path.name
        counterpart = path.with_name(name.replace('.zh-CN.md', '.md') if name.endswith('.zh-CN.md') else name[:-3] + '.zh-CN.md')
        if not counterpart.is_file():
            errors.append(f'{path.relative_to(root)}: missing language pair {counterpart.name}')
    return errors

class SelfTests(unittest.TestCase):
    def test_anchors(self):
        lines = list(visible_lines('# 中文 标题\n# 中文 标题\n```md\n# hidden\n```\n<a id="explicit"></a>\n'))
        self.assertEqual(anchors(lines), {'中文-标题', '中文-标题-1', 'explicit'})
    def test_fences(self):
        with self.assertRaises(ValueError):
            list(visible_lines('~~~python\nx = 1'))
        self.assertEqual(list(visible_lines('````\n```\n````')), [])
    def test_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'sample.md').write_text('# 中文\n[x](missing.md)\n[x](#absent)\n[x](https://github.com/uniubi-ai/uniubi-docs/blob/main/missing.md)\n', encoding='utf-8')
            errors = check(root)
            self.assertEqual(len(errors), 3)
            self.assertTrue(any('missing anchor' in error for error in errors))
    def test_code_label_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'sample.md').write_text('[`foo`](missing.md)\n`[example](ignored.md)`\n', encoding='utf-8')
            errors = check(root)
            self.assertEqual(len(errors), 1)
            self.assertIn('missing.md', errors[0])
    def test_pairing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'docs').mkdir()
            (root / 'docs/a.md').write_text('# A', encoding='utf-8')
            self.assertIn('missing language pair', check(root)[0])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        unittest.main(argv=['check_docs'], exit=True)
    else:
        issues = check(Path(__file__).resolve().parents[1])
        for issue in issues:
            print(issue)
        print(f'Documentation checks: {len(issues)} error(s)')
        raise SystemExit(bool(issues))
