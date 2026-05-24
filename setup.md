# 配置参考

首次使用 xhs-reader 时，agent 会自动引导你完成基础配置（Obsidian Vault 路径）。以下是补充说明。

初始化命令：

```bash
python3 scripts/xhs_extract.py --init --vault "/你的保存目录"
```

这个命令会写入 `config.json`，并创建默认目录：

```text
00-Inbox/小红书/多媒体/
00-Inbox/小红书/创作素材/
00-Inbox/小红书/知识资源/
```

## 账号安全

本 skill 不使用任何小红书登录账号。不要在小红书登录状态下运行浏览器提取，也不要为了提取内容引导用户登录。

小红书默认先打开网页版链接。打开或切换到目标页面后，如果 agent 使用的是用户可能登录过的浏览器会话，运行 `yt-dlp`、脚本提取、页面 JS、评论提取、媒体 URL 提取、截图 OCR 或保存内容前，必须先检测当前页面是否已登录：

- 未登录：可以继续按未登录能力提取。
- 已登录：立即停止，并提示用户退出登录或切换到未登录隔离浏览器环境。
- 无法确认且疑似主浏览器：按不安全处理，停止浏览器提取。

如果页面只弹出「手机号登录 / 二维码 / 获取验证码 / 登录后推荐更懂你的笔记」登录窗，但没有当前账号头像、侧边栏「我」、账号菜单或退出登录等真实账号信号，视为未登录提示。默认关闭登录窗（`Esc` 或右上角 `X`）后继续，不要求用户登录。

未登录状态下可能出现：
- 评论、互动数不可用或不完整
- 视频源质量较低
- 部分内容无法获取

这些都应标注为未登录环境限制，不能要求用户登录。

## 工具依赖

首次使用建议先运行：

```bash
python3 scripts/xhs_extract.py --doctor
```

`yt-dlp` 是基础依赖，用于元数据提取和媒体下载。`faster-whisper` + `ffmpeg` 只是本地 ASR 兜底，用于没有可用字幕但仍需要语音转文字的情况。

```bash
# Windows
winget install yt-dlp

# macOS
brew install yt-dlp

# Linux / 通用 Python 环境
pipx install yt-dlp
```

可选：本地 ASR 兜底依赖。只有在没有可用字幕、仍需要语音转文字时安装：

```bash
pip install faster-whisper
brew install ffmpeg          # macOS
sudo apt install ffmpeg
```

不安装 `faster-whisper` / `ffmpeg` 也可以使用已有字幕生成逐字稿；只是在没有字幕时不能做本地 ASR 兜底。不安装 `yt-dlp` 会影响媒体下载和部分元数据提取。

## 权限配置

根据你使用的 AI agent 平台，可能需要开启以下能力：

- 执行终端命令：`python3`、`yt-dlp`、`curl`、`mkdir`、`ffmpeg`。
- 读写本地文件：保存 Markdown、媒体和 `config.json`。
- 打开网页并读取页面内容。
- 执行页面 JavaScript 或等价的 DOM 提取能力。
- 下载公开图片或视频资源。

如果 agent 使用隔离浏览器，仍需确认该浏览器没有小红书登录态；如果 agent 使用用户主浏览器，打开小红书页面后必须立刻检测登录态。检测到真实登录态就停止，不运行 `yt-dlp` 或页面提取。只出现登录弹窗时默认关闭弹窗后继续。

## config.json 字段说明

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `obsidian_vault` | Obsidian Vault 绝对路径 | `""`（首次使用时 agent 会询问） |
| `save_root` | Vault 内的保存根目录 | `00-Inbox/小红书` |
| `attachments_dir` | 附件目录名 | `_attachments` |
| `categories` | 分类列表 | 多媒体/创作素材/知识资源 |
| `asr_model` | ASR 模型 | `small`（可改为 `medium`） |
| `scripts_path` | 脚本目录路径 | 首次使用时自动设为绝对路径 |
