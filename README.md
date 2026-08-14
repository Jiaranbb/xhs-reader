# xhs-reader — AI Agent 小红书内容提取技能

发送一条链接，自动提取全部内容保存到本地。

```
小红书链接 → 内容提取 → 自动分类 → Markdown 笔记
```

## 它能干什么

发送一条小红书链接，自动提取内容，整理为 Markdown 笔记并分类保存。

### 小红书图文笔记

| 步骤 | 说明 |
|------|------|
| 图片文字识别 | OCR 逐张读取图片中的文字，合并为完整文本 |
| 正文提取 | 保留原文段落结构，自动去重（图片文字与正文重复时精简正文） |
| 热门评论 | 按点赞排序提取 Top 10 |
| 图片下载 | 默认不下载，可事后说「下载图片」保存到本地 |

### 小红书视频笔记

| 步骤 | 说明 |
|------|------|
| 视频逐字稿 | ASR 语音转文字，带时间戳（需安装依赖） |
| 正文提取 | 保留原文内容和标签 |
| 热门评论 | 按点赞排序提取 Top 10 |
| 视频预览 | 默认在笔记中插入视频链接，可在 Obsidian 直接播放 |
| 视频下载 | 可事后说「下载视频」保存到本地永久观看 |

### 通用能力

| 功能 | 说明 |
|------|------|
| 自动分类 | 根据内容归入创作素材或知识资源 |
| 自动标签 | 保留原笔记标签，自动添加小红书来源标签 |

> **需要同时支持小红书、Twitter/X、YouTube、B 站？** 推荐使用组合入口 [content-reader](https://github.com/Jiaranbb/content-reader)，它会按链接类型路由到对应平台 skill。

---

## 登录与账号安全

xhs-reader 默认不使用小红书登录账号。请不要在小红书已登录状态下运行本 skill；使用登录账号抓取内容可能触发平台风控或账号处罚。

运行时会先打开小红书网页并检查登录状态：

- 如果检测到已登录账号，会停止提取，并提示你退出登录或切换到未登录的隔离浏览器。
- 如果只是弹出手机号、二维码或验证码登录窗，会默认关闭弹窗后继续。
- 不会导出或保存 cookie、token、localStorage 等登录信息。

未登录状态下，部分评论、互动数、视频源或图片源可能不完整；其中点赞、收藏、评论数等互动数据可能和登录状态下看到的数据存在偏差。这是平台限制，skill 会尽量保存可见内容，并在必要时标注限制。

---

## 快速开始

### 1. 安装到你的 AI Agent

**Claude Code：**
```bash
git clone https://github.com/Jiaranbb/xhs-reader.git ~/.claude/skills/xhs-reader
```

**OpenClaw：**
```bash
clawhub install xhs-reader
```

**其他 Agent：** 将本目录放到 agent 能读取的 skills 目录中。

### 2. 首次使用

直接发送一条小红书链接，agent 会自动引导你完成配置：
- 询问你的保存路径（Obsidian Vault 或任意本地文件夹）
- 自动写入配置文件
- 创建分类目录

无需手动编辑任何文件。笔记以 Markdown 格式保存，兼容 Obsidian、Logseq、Typora 等任何 Markdown 工具。

---

## 依赖说明

推荐安装：

```bash
# macOS
brew install yt-dlp ffmpeg

# Windows
winget install yt-dlp

# Linux / 通用 Python 环境
pipx install yt-dlp
```

可选安装：

```bash
pip install faster-whisper
```

| 能力 | 依赖 | 说明 |
|------|------|------|
| 图片文字识别 | LLM 视觉能力 | 依赖大模型本身的多模态能力，无需额外安装 |
| 元数据 / 媒体下载 | `yt-dlp` | 推荐安装，用于提取元数据和下载图片、视频 |
| 视频处理 | `ffmpeg` | 下载、转音频、本地 ASR 时使用 |
| 本地转写 | `faster-whisper` | 没有可用字幕且需要逐字稿时才需要 |
| 数据提取 | Python 3.9+ | 运行提取脚本 |

不安装 `ffmpeg` / `faster-whisper` 也可以正常保存普通图文笔记；只是在没有可用字幕时不能做本地 ASR 兜底。不安装 `yt-dlp` 会影响媒体下载和部分元数据提取。

---

## 使用方式

直接发送链接即可，全自动处理：

```
http://xhslink.com/o/xxxxx          → 自动提取并保存
保存小红书 http://xhslink.com/...    → 同上
保存一下，需要原视频 http://xhslink.com/... → 保存笔记并下载原视频
```

保存后还可以追加操作：

```
下载图片    → 图片保存到本地，永久可用
下载视频    → 视频保存到本地，永久可用
```

---

## 跨平台兼容

本 Skill 不绑定特定 AI Agent，通过工具映射表适配不同平台：

| 通用操作 | Claude Code | OpenClaw |
|---------|------------|----------|
| 打开浏览器 | `tabs_context_mcp` + `navigate` | `browser.open` |
| 执行页面 JS | `javascript_tool` | `browser.evaluate` |
| HTTP 下载 | `WebFetch` | `http.get` |
| 读写文件 | `Read` / `Write` | `fs.read` / `fs.write` |
| 执行命令 | `Bash` | `shell.run` |

---

## 项目结构

```
xhs-reader/
├── SKILL.md                  # 核心工作流（Agent 读取执行）
├── config.json               # 用户配置（首次使用自动填写）
├── setup.md                  # 配置参考文档
├── assets/
│   └── note-template.md      # Obsidian 笔记模板
├── scripts/
│   └── xhs_extract.py        # Python 数据提取 & ASR 引擎
├── references/
│   ├── extract-js.md          # 浏览器数据提取 JS
│   ├── comments-js.md         # 评论提取 JS
│   └── gotchas.md             # 常见问题与解决方案
├── README.md
└── LICENSE
```

---

## 声明

本项目仅供个人学习和研究使用。请尊重小红书平台的内容版权及用户隐私，不得将本工具用于批量爬取、商业用途或任何违反平台服务条款的行为。使用者应自行承担使用风险。

## 相关项目

- [ecommerce-helper](https://github.com/Jiaranbb/ecommerce-helper) — 从新品研究、人民币定价到商详与社媒内容的完整电商素材包 Skill；
- [report-helper](https://github.com/Jiaranbb/report-helper) — 一句话启动长篇深度研究，并生成带来源的报告与 PDF；
- [content-reader](https://github.com/Jiaranbb/content-reader) — 保存小红书、Twitter／X、YouTube 和 B 站内容的组合型 Agent Skills；
- [pdf-reader](https://github.com/Jiaranbb/pdf-reader) — 将 PDF 转换成带页码与质量指标的 Markdown；
- [dreamy-photo](https://github.com/Jiaranbb/dreamy-photo) — 保留真实主体细节的梦幻化照片编辑 Skill；
- [autoskin-codex](https://github.com/Jiaranbb/autoskin-codex) — 可预览、可撤销的 Codex 桌面主题定制工具；
- [jiucai-helper](https://github.com/Jiaranbb/jiucai-helper) — 将投资方法和纪律整理成可验证的个人投资决策 Skill。

更多原创项目见 [Jiaranbb 的 GitHub 主页](https://github.com/Jiaranbb?tab=repositories)。

## 关于作者

**嘉然 Jiaran（Jiaranbb）** — 独立开发者／AI Builder

持续把自己真正需要的工作流做成可复用的 AI 工具与 Skills。

- 个人网站：[c.aoao.ai](https://c.aoao.ai)
- GitHub：[github.com/Jiaranbb](https://github.com/Jiaranbb)
- X／Twitter：[@_jiaran](https://x.com/_jiaran)
- 微信：`evadebot`
- 公众号：**嘉然学习笔记**
- 项目问题：[GitHub Issues](https://github.com/Jiaranbb/xhs-reader/issues)

## License

[CC BY-NC 4.0](LICENSE) — 可自由使用和修改，需署名，禁止商业用途。
