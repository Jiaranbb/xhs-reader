---
name: xhs-reader
description: >
  从小红书或 Twitter/X 链接自动提取内容并保存到 Obsidian。
  当用户发的链接包含 xhslink、xiaohongshu、x.com、twitter.com，
  或提到「保存小红书」「保存推文」时触发。
  全自动执行，无需用户确认。
  Author: 嘉然 | GitHub: https://github.com/Jiaranbb/xhs-reader
---

# xhs-reader

提取小红书 / Twitter 内容 → 保存到 Obsidian。遇到问题读 `references/gotchas.md`。

所有 `{变量名}` 来自 `config.json`，执行时替换为实际值。

**全自动模式：整个流程不中断等待用户确认，一次性跑完所有步骤。** 默认不下载图片/视频，用户事后说"下载"再补下载。

## 工具映射

不同 AI agent 平台的工具名不同，以下是本 Skill 使用的通用操作与各平台对应关系：

| 通用操作 | Claude Code | OpenClaw | 说明 |
|--------|------------|----------|------|
| 打开浏览器标签页 | `tabs_context_mcp` + `navigate` | `browser.open` | 打开指定 URL |
| 执行页面 JS | `javascript_tool` | `browser.evaluate` | 在当前页面执行 JavaScript |
| HTTP 下载 | `WebFetch` | `http.get` | 下载文件或获取网页内容 |
| 读取文件 | `Read` | `fs.read` | 读取本地文件 |
| 写入文件 | `Write` | `fs.write` | 写入本地文件 |
| 执行命令 | `Bash` | `shell.run` | 执行终端命令 |

**以下工作流中使用「通用操作」列的名称描述操作。请根据你的 agent 平台替换为实际工具。**

## 触发条件

- 消息中包含 `xhslink.com` / `xiaohongshu.com` / `explore/`
- 消息中包含 `x.com` / `twitter.com`（推文链接）
- 提到「保存小红书」「收藏小红书」「保存推文」

## 工作流

**按 Gate 0→1→2→3→4→5→6→7 顺序执行，全程无中断。** Gate 4 仅视频笔记执行。

### Gate 0: 环境检查（首次）

1. 读取文件 `config.json`
2. **若 `obsidian_vault` 为空字符串**，执行首次配置引导：
   a. 询问用户「请提供你的 Obsidian Vault 绝对路径（例如 /Users/xxx/Documents/My Vault）」
   b. 用户回答后，将路径写入 `config.json` 的 `obsidian_vault` 字段
   c. 检测本 skill 的安装目录（即 `config.json` 所在目录），将 `scripts_path` 更新为该目录下 `scripts` 子目录的**绝对路径**
   d. 输出简要提示：「配置完成。如需视频逐字稿功能，请安装 faster-whisper 和 ffmpeg，详见 setup.md。」
3. **若 `scripts_path` 是相对路径（以 `./` 开头）**，将其替换为绝对路径并写入 `config.json`
4. 确保分类目录存在，逐条执行：
   ```
   mkdir -p "{obsidian_vault}/{save_root}/素材"
   mkdir -p "{obsidian_vault}/{save_root}/灵感"
   mkdir -p "{obsidian_vault}/{save_root}/参考"
   mkdir -p "{obsidian_vault}/{save_root}/学习资料"
   mkdir -p "{obsidian_vault}/{save_root}/其他"
   ```
5. 视频笔记时检查 ASR 依赖：执行命令 `python3 -c "import faster_whisper"` + `which ffmpeg`，缺失则在笔记中标注并跳过 ASR

**检查点：** `obsidian_vault` 路径有效，`scripts_path` 为绝对路径，分类目录已创建。

### Gate 1: 链接解析 + 平台识别

1. 从用户消息中提取链接，**立即保存为 `ORIGINAL_LINK`，后续不可修改此变量**
   - `ORIGINAL_LINK` 就是用户发送的原始文本中的链接，例如 `http://xhslink.com/o/xxx` 或 `https://x.com/user/status/123`
   - **严格规则：`ORIGINAL_LINK` 必须是用户发送的原始链接原文，不可替换为解析后的 xiaohongshu.com/explore/... 长链接。笔记中所有「原链接」字段都使用此值。**
2. 识别平台：
   - 链接包含 `xhslink.com` 或 `xiaohongshu.com` → **PLATFORM = XHS**
   - 链接包含 `x.com` 或 `twitter.com` → **PLATFORM = Twitter**
3. 如果是 XHS 短链接（xhslink.com），**必须用浏览器打开**（curl 返回 404，原因是 JS 重定向）：
   - 打开浏览器标签页 → 导航到短链接 URL → 等待 3 秒 → 读取最终 URL 作为 `NOTE_URL`
   - **注意：`NOTE_URL` 仅用于数据提取，写入笔记时仍使用 `ORIGINAL_LINK`**
4. 如果是 Twitter 链接，直接使用原链接作为 `NOTE_URL`
5. 如果是完整 xiaohongshu.com 链接，直接使用

**检查点：** `ORIGINAL_LINK`（用户发送的原始链接，不可被覆盖）、`NOTE_URL`（用于数据提取的完整 URL）、`PLATFORM`（XHS 或 Twitter）。

### Gate 2: 数据提取

#### 如果 PLATFORM = XHS

**优先 Path A（脚本）→ 失败降级 Path B（浏览器）**

- **Path A:** 执行命令 `python3 {scripts_path}/xhs_extract.py --url "$NOTE_URL" --action extract`
  - 成功：解析返回的 JSON
  - 失败（报错或返回含 `error` 的 JSON）：转 Path B
- **Path B:** 用浏览器打开 NOTE_URL → **读取文件 `references/extract-js.md`** → 执行页面 JS（文件中的第一段代码） → 解析返回的 JSON
- 记录以下变量：`title`, `desc`, `type`（"video" 或 "normal"）, `tags`, `images`（URL 列表）, `video`（URL）, `author`, `likes`, `collects`, `commentCount`

#### 如果 PLATFORM = Twitter

1. 用浏览器打开 NOTE_URL → 等待 3 秒
2. 执行页面 JS 提取：
   ```javascript
   (() => {
     const tweet = document.querySelector('article [data-testid="tweetText"]');
     const author = document.querySelector('[data-testid="User-Name"]');
     const hasVideo = !!document.querySelector('video, [data-testid="videoPlayer"]');
     const imgs = [...document.querySelectorAll('article img[src*="pbs.twimg.com/media"]')].map(i => i.src);
     const text = tweet ? tweet.innerText : '';
     return JSON.stringify({
       title: text.substring(0, 30),
       desc: text,
       type: hasVideo ? 'video' : 'normal',
       tags: [],
       images: imgs,
       author: author ? author.textContent.split('@')[0].trim() : '',
       platform: 'twitter'
     });
   })()
   ```
3. 解析返回的 JSON，设置 `type`、`author` 等变量

**检查点：** `title`, `desc`, `type`, `tags`, `images`, `author`。视频笔记还需 `video` URL（XHS）或标记需要 yt-dlp（Twitter）。

### Gate 3: 图片文字提取

逐张处理 `images` 列表中的每张图片，不可跳过。

- **优先：** HTTP 下载图片 → 读取文件（视觉识别）→ 提取图中文字
- **降级（下载失败/403/404）：** 在浏览器中打开图片或截图 → 视觉识别文字
- **输出：** 将所有图片文字合并为一整块连续文本 `IMAGE_TEXT`，完整保留不删减
- **默认不保存原始图片到笔记中**（用户事后说"下载图片"再补）

**检查点：** `IMAGE_TEXT`（所有图片识别文字合并后的文本）。

### Gate 4: 视频 ASR（仅当 type = "video" 时执行，否则跳过）

#### 如果 PLATFORM = XHS
1. 获取视频 URL，**保留完整查询参数**（`?sign=xxx&t=xxx`）
2. 如果 URL 被安全过滤 → 读取文件 `references/extract-js.md` 中「完整签名 URL」部分，用 `document.title` 中转方法获取
3. 执行命令 `python3 {scripts_path}/xhs_extract.py --url "$VIDEO_URL" --action transcribe --asr-model {asr_model}`

#### 如果 PLATFORM = Twitter
1. **获取视频 mp4 直链**：执行命令 `yt-dlp -f "http-832" --get-url "$ORIGINAL_LINK"` → 保存为 `VIDEO_MP4_URL`
2. **优先：yt-dlp 字幕提取**（秒级）
   - 执行命令 `yt-dlp --write-subs --write-auto-subs --sub-lang "zh,zh-Hans,zh-CN,en" --sub-format vtt --skip-download -o "/tmp/twitter_subs" "$ORIGINAL_LINK"`
   - 如果生成了 .vtt 文件 → 解析 VTT 文本作为逐字稿
   - 如果没有字幕文件 → 转降级方案
3. **降级：本地 ASR**（分钟级）
   - 执行命令 `yt-dlp -o "/tmp/twitter_video.mp4" "$ORIGINAL_LINK"`
   - 执行命令 `ffmpeg -i /tmp/twitter_video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 /tmp/twitter_audio.wav`
   - 执行命令 `python3 {scripts_path}/xhs_extract.py --url "/tmp/twitter_audio.wav" --action transcribe --asr-model {asr_model}`
   - 清理临时文件：`rm -f /tmp/twitter_video.mp4 /tmp/twitter_audio.wav /tmp/twitter_subs*`

#### 通用规则
- 失败则在笔记中标注「视频转录失败：{原因}」并继续
- **默认不下载视频**，用 `<video src="URL" controls></video>` 嵌入（必须带 `controls` 属性）
- Twitter 视频用 `VIDEO_MP4_URL` 嵌入
- XHS 视频用 H.264 masterUrl 嵌入，**保留完整签名参数**
- 用户事后说"下载视频"再补下载到本地

**检查点：** `TRANSCRIPT`（逐字稿文本），或失败原因标注。

**严格规则：逐字稿必须原文保留 ASR 输出的每一行（含时间戳），禁止总结、改写、缩写或省略任何内容。**

### Gate 5: 热门评论（Top 10）

- **如果 PLATFORM = XHS**：在浏览器中向下滚动 5-10 次到评论区 → **读取文件 `references/comments-js.md`** → 执行页面 JS → 按点赞排序取前 10 条
- **如果 PLATFORM = Twitter**：跳过（Twitter 评论结构不同，暂不提取）
- 失败则标注原因，继续下一步

**检查点：** `COMMENTS`（评论列表，每条含 user/content/likes）或标注跳过/失败原因。

### Gate 6: 自动分类

根据 `title`、`desc`、`tags` 中的关键词匹配分类。**按顺序匹配，命中即停止：**

| 优先级 | 分类 | 关键词（标题/正文/标签中出现任一即命中） |
|--------|------|------|
| 1 | 学习资料 | 教程, 干货, 笔记, 学习, 方法论, 指南, 入门, 进阶, 教学, 科普 |
| 2 | 素材 | 模板, 素材, 资源, 工具, 推荐, 清单, 合集, 必备 |
| 3 | 灵感 | 灵感, 创意, 设计, 审美, 配色, 排版, 风格 |
| 4 | 参考 | 测评, 对比, 经验, 踩坑, 分享, 心得, 复盘, 避坑 |
| 5 | 其他 | 以上均未命中时的默认分类 |

自动添加来源 tag：XHS → `#小红书`，Twitter → `#Twitter`

**检查点：** `CATEGORY`（分类名）、`SOURCE_TAG`（来源标签）。

### Gate 7: 生成并保存

1. **读取文件 `assets/note-template.md`** 获取模板
2. **严格按模板结构填入数据**，不可省略任何区域，不可改变区域顺序。逐项说明：

| 模板区域 | 数据来源 | 严格规则 |
|---------|---------|---------|
| frontmatter（`---` 之间） | Gate 2 + Gate 6 | 所有字段必须填写，`原链接` 必须用 `ORIGINAL_LINK` |
| `## 正文内容` | Gate 2 的 `desc` | **原文粘贴，禁止总结改写** |
| `## 图片文字内容` | Gate 3 的 `IMAGE_TEXT` | **原文粘贴，禁止总结改写**；图文笔记必须包含此区域 |
| `## 视频逐字稿` | Gate 4 的 `TRANSCRIPT` | **原文粘贴 ASR 每一行（含时间戳），禁止总结改写**；仅视频笔记 |
| `## 视频` | Gate 4 的视频 URL | 必须用以下**精确格式**：`<video src="完整URL含参数" controls></video>` |
| `## 热门评论（Top 10）` | Gate 5 的 `COMMENTS` | 必须用 Markdown 表格格式，表头为 `# | 用户 | 评论内容 | 点赞` |
| 页脚署名行 | 模板末尾 | **必须保留，不可省略** |

3. **视频嵌入的精确写法**（不可使用其他格式）：
   ```html
   <video src="https://sns-video-xxx.xhscdn.com/xxx.mp4?sign=xxx&t=xxx" controls></video>
   ```
   - 必须是 `<video>` 标签，不是 `![]()`，不是 `[链接]()`
   - 必须包含 `controls` 属性
   - URL 必须保留完整的查询参数（`?sign=xxx&t=xxx`）

**裁剪规则：**
- 图文笔记（type="normal"）：去掉「封面图」「视频逐字稿」「视频」区域
- 视频笔记（type="video"）：保留所有区域
- 正文即使很短也完整保留
- 图片文字合并为一整块，不删减
- 正文与图片文字重复时精简正文，保留图片文字

**排版规则：**
- 保持原文段落结构和换行
- 编号列表（/01/）→ `###` 小标题
- 要点列表 → `-`，前半句加粗
- 关键概念和结论加粗
- 逐字稿每行紧挨，不加空行，不加说明文字，不用 `<details>` 折叠

4. 写入文件到 `{obsidian_vault}/{save_root}/{CATEGORY}/{标题}.md`
   - **`{CATEGORY}` 是 Gate 6 确定的分类名（素材/灵感/参考/学习资料/其他），必须保存到对应子目录，不可直接保存到 `{save_root}/` 根目录**
   - 文件名：去除特殊字符，限 50 字符

### 完成确认

输出：保存路径、分类、标签、内容概要

## 事后补充操作

用户保存后可以追加指令，直接执行无需再次提取：
- 「下载图片」→ 下载到 `{attachments_dir}/`，更新笔记插入本地图片
- 「下载视频」→ 下载到 `{attachments_dir}/`，更新笔记视频路径为本地

## 错误处理

| 场景 | 处理 |
|------|------|
| 短链接解析失败 | 用浏览器打开，不重试 curl |
| 反爬拦截 | 降级到浏览器 |
| 图片 403 | 降级到浏览器截图 |
| ASR 缺失 | 标注原因，跳过转录 |
| 评论失败 | 标注原因，继续保存 |
| JS 被安全过滤 | 读 `references/gotchas.md`，用 document.title 中转 |
| Twitter 视频下载失败 | yt-dlp 可能需要 cookies，提示用户检查登录状态 |
| Twitter 页面加载不全 | 等待时间延长到 5s，或刷新重试一次 |
