# WeChat/Web Article Archiver

Archive articles (WeChat + general web) to local HTML + images.
Optionally publish to WordPress via REST API.

## Quick Start

`ash
# Local archive
python scripts/archive_wechat.py https://example.com/article

# Archive + publish to WordPress
python scripts/archive_wechat.py https://example.com/article --wp
`

## Features

- WeChat article support (mp.weixin.qq.com) with data-src handling
- General web article support with multi-strategy body extraction
- Automatic encoding detection (UTF-8, GBK, GB2312)
- Relative image URL resolution
- Navigation/sidebar/ads stripping
- WordPress image upload and publishing
- Local offline-ready archive with images

## Design decisions

See SKILL.md for detailed documentation of all lessons learned from production use.

## License

MIT

## New in latest version

- **Lazy load handling**: Automatically strips a3 Lazy Load / WP Rocket lazy attributes (data-src, noscript, etc.) from source articles
- **--html-file flag**: Pre-fetch pages that block urllib (like Baidu Baike) with curl, then archive from local file
- **data-no-lazy**: Adds skip-lazy hints to prevent WP-side lazy load interference