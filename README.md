# xhs-reader

Developer notes for the standalone Xiaohongshu reader skill.

## Role

`xhs-reader` handles:

- Xiaohongshu short links and web links.
- Markdown note creation.
- Optional image/video download.
- Visible comments and interaction metadata.
- OCR or transcript fallback when useful.

## Trigger Hints

Use this skill when the user provides:

- Xiaohongshu links: `xhslink.com`, `xiaohongshu.com`, or `explore/`.
- Note-saving requests: `保存一下`, `保存小红书`, `收藏小红书`, `帮我存一下`.
- Media-only requests: `只下载视频`, `下载视频`, `下载图片`, `把视频发我`.
- Note plus original media requests: `需要原视频`, `原视频也需要`, `同时下载视频`.

## User Intents

| Intent | Behavior |
|--------|----------|
| `save_note` | Save a Markdown note |
| `download_media` | Download image or video only |
| `save_note_with_media` | Save a note and download original video |

Media type can be passed as `media_type=image` or `media_type=video`.

## Safety Model

This skill does not use a Xiaohongshu logged-in account by default.

Before extraction, open the web page and follow `references/account-safety.md`:

- Stop if a real logged-in account state is detected.
- Close phone, QR, or verification login popups when no real account signal is present.
- Do not export cookies, tokens, or localStorage.

## Configure

Set `obsidian_vault` in `config.json`.

```json
{
  "obsidian_vault": "",
  "save_root": "00-Inbox/小红书",
  "scripts_path": "scripts"
}
```

If `obsidian_vault` is empty, ask the user for a save directory or run:

```bash
python3 scripts/xhs_extract.py --init --vault "/path/to/notes"
```

## Dependencies

- `yt-dlp`: metadata and media download.
- `ffmpeg`: local audio/video handling.
- `faster-whisper`: optional ASR fallback.

Check the environment:

```bash
python3 scripts/xhs_extract.py --doctor
```

## Maintenance

- Keep trigger hints in `SKILL.md` aligned with the user intents above.
- Keep long workflow details in `references/`.
- Update `references/extract-js.md` and `references/comments-js.md` when Xiaohongshu page structure changes.
- Update `assets/` when Markdown output format changes.

## Author

嘉然 | 公众号「嘉然学习笔记」
