# 工作流

## 模式选择

| 模式 | 触发条件 | 输出 |
|------|----------|------|
| 只保存多媒体 | 用户说 `只下载视频`、`下载这个视频`、`下载图片`、`刚才那条下载视频`、`刚才那条下载图片`、`把视频发我`，或明确只要媒体文件 | 视频 / 图片文件，保存到 `00-Inbox/小红书/多媒体/` |
| 保存笔记 + 原视频 | 用户要求保存 / 收藏，同时说 `需要原视频`、`原视频也需要` 或 `同时下载视频` | Markdown 笔记 + 视频文件 |
| 保存笔记 | 用户要求保存 / 收藏，或只发送链接 | Markdown 笔记，保存到 `创作素材` 或 `知识资源` |

用户明确只要文件时，走「只保存多媒体」。用户要求保存笔记且需要原视频时，保存 Markdown 并下载视频。其他情况默认走「保存笔记」。

## 只保存多媒体

1. 用浏览器打开用户发送的小红书原始链接。
2. 执行 `references/account-safety.md`。检测到真实登录态就停止；只出现登录弹窗时关闭弹窗后继续。
3. 读取当前 tab URL 作为 `YTDLP_URL`；无法读取时使用 `ORIGINAL_LINK`。
4. 判断用户要的媒体：
   - `只下载视频`、`下载这个视频`、`刚才那条下载视频`、`把视频发我`：下载视频。
   - `下载图片`、`刚才那条下载图片`：下载图片。
   - 表达不明确时：如果有视频优先下载视频，否则保存图片。
5. 如果用户提到上一条笔记但没有提供链接，使用当前对话里最近一次保存的笔记上下文；没有上下文时要求用户补链接。
6. 优先用 `yt-dlp` 下载：

```bash
mkdir -p "{obsidian_vault}/00-Inbox/小红书/多媒体/笔记标题"
cd "{obsidian_vault}/00-Inbox/小红书/多媒体/笔记标题"
yt-dlp -o "%(title)s.%(ext)s" "$YTDLP_URL"
```

7. `yt-dlp` 失败时，在已通过账号安全门禁的页面使用 `references/extract-js.md` 获取媒体 URL，再用 `curl` 下载。
   - 如果 `yt-dlp` 报 `No video formats found`，通常说明当前笔记是图文笔记或没有可下载视频。用户要下载图片时，不要终止；继续用脚本或页面 JS 提取 `images`，再逐张下载。

## 保存笔记

### Step 1：解析链接并提取数据

1. 用浏览器打开 `ORIGINAL_LINK`，短链接也直接打开，让网页完成跳转。
2. 执行 `references/account-safety.md`。检测到真实登录态就停止；只出现登录弹窗时关闭弹窗后继续。
3. 读取最终 tab URL 作为 `YTDLP_URL`；无法读取时使用 `ORIGINAL_LINK`。
4. 运行：

```bash
yt-dlp --dump-single-json --skip-download "$YTDLP_URL" 2>/dev/null
```

5. `yt-dlp` 失败时降级：
   - Path A：`python3 {scripts_path}/xhs_extract.py --url "$YTDLP_URL" --action extract`
   - Path B：读取 `references/extract-js.md`，在已通过账号安全门禁的页面提取数据
   - 如果 `yt-dlp` 报 `No video formats found`，不要直接判定失败；这常见于图文笔记，继续走 Path A / Path B。

笔记里的链接字段始终使用用户发送的 `ORIGINAL_LINK`。

记录变量：`title`、`desc`、`type`、`tags`、`images`、`video`、`author`、`likes`、`collects`、`commentCount`。

### Step 2：媒体处理

按笔记类型选择处理方式：

- 视频笔记：读取 `references/media-processing.md#视频笔记`。
- 图片有大量文字：读取 `references/media-processing.md#图片含大量文字`。
- 普通图文：使用 `desc` 作为正文，必要时列出图片 URL。

如果用户说了 `需要原视频`、`原视频也需要` 或 `同时下载视频`，在元数据提取后下载原视频，并在 Markdown 笔记中链接或嵌入本地视频路径。

### Step 3：评论

账号安全门禁通过后，滚动到评论区，使用 `references/comments-js.md` 提取可见的热门评论。评论不可见时说明限制并继续。

### Step 4：选择模板

| 用途 | 判断依据 | 模板 | 保存路径 |
|------|----------|------|----------|
| 创作素材 | 可复用于写作、选题、社交文案、内容角度 | `assets/template-creative.md` | `00-Inbox/小红书/创作素材/` |
| 知识资源 | 教程、方法、参考资料、研究、学习型内容 | `assets/template-knowledge.md` | `00-Inbox/小红书/知识资源/` |

拿不准时默认保存为知识资源。

### Step 5：写入 Markdown

1. 如果用户提供了自己的 Vault schema / CLAUDE.md / 保存规则，优先遵循。否则使用本 skill 的模板。
2. 读取选定模板并完整填写。
3. 不要把调试日志、报错堆栈或提取过程写入最终笔记正文。

Frontmatter 规则：

- 使用 YAML 语法，字段冒号用英文冒号。
- `tags` 必须是数组格式：`[tag1, tag2]`。
- 不要写入个人专属字段。
- 创作素材必须包含 `品牌`、`情绪`、`场景`、`平台`。

区域裁剪：

- 视频笔记：保留所有模板区域。
- 图片有大量文字：保留 `媒体文字内容`，正文与 OCR 内容去重。
- 普通笔记：删除 `媒体文字内容` 和 `视频` 区域。

文件名：`YYYY-MM-DD-标题.md`，移除不安全字符，标题控制在约 50 个字符内。

H1 标题格式：`# YYYY-MM-DD 标题`。
