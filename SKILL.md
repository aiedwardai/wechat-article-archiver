---
name: wechat-article-archiver
description: "Archive WeChat and general web articles to local HTML + images. Use when a user wants to download, save, archive, or backup an article URL (mp.weixin.qq.com or any web page). Also supports optional publishing to WordPress via REST API."
---

# WeChat/Web Article Archiver

Archive articles (WeChat + general web) to local HTML + images.
Optionally publish to WordPress.

## Usage

`ash
python scripts/archive_wechat.py https://mp.weixin.qq.com/s/XXXX
python scripts/archive_wechat.py https://example.com/article --wp
`

## Trigger

Use when user asks to save/backup/archive an article URL, whether from WeChat (mp.weixin.qq.com) or any other web page.

## Key lessons baked in

### 1. Image replacement (CRITICAL for WeChat)
WeChat articles use <img data-src="URL" type="block" alt="..." />.

**DO NOT** replace just data-src:
`python
# BAD: produces <img <img src="..." /> type="block" ... />
re.sub(r'data-src="..."', '<img src="..." />', body)
`

**DO** replace the entire <img> tag:
`python
# GOOD
re.sub(r'<img[^>]*data-src="..."[^>]*>', '<img src="..." />', body)
`

### 2. Relative image URLs
Non-WeChat articles often use relative paths (../images/x.jpg). These are resolved to absolute URLs using urllib.parse.urljoin.

### 3. Encoding detection
Try UTF-8 first, fallback to GBK, then GB2312. Chinese edu/gov sites frequently use non-UTF-8 encodings.

### 4. Content cleaning
Strips: scripts, styles, iframes, nav, header, footer, sidebar, breadcrumbs, pagination, comments, ads.

### 5. Font sizing
WordPress strips <style> tags from post content. Use inline <div style="font-size:14px"> instead.

### 6. Unicode escapes
All Chinese text uses \uXXXX escapes to avoid PowerShell pipe encoding corruption.

### 7. WordPress notes
- GET /posts/{id}?edit=true may not return content.raw
- Always POST complete HTML when updating
- Media upload uses image/jpeg content type
- Categories: JianNews=10, JianInsight=7

## Output

`
archive_YYYYMMDD_HHMM_title/
  index.html    # offline-ready archive
  images/
    img_01.jpg
    ...
`

## Files

| File | Purpose |
|------|---------|
| SKILL.md | Codex skill instructions |
| scripts/archive_wechat.py | Core archiving script |
| agents/openai.yaml | UI metadata |
