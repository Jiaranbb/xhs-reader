# xhs-reader — AI Agent 小红书/Twitter 内容提取技能

发送一条链接，自动提取全部内容保存到本地。

```
小红书/Twitter 链接 → 内容提取 → 自动分类 → Markdown 笔记
```

## 它能干什么

发送一条小红书或 Twitter 链接，自动提取全部内容，整理为 Markdown 笔记并分类保存。

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

### Twitter/X

| 步骤 | 说明 |
|------|------|
| 推文提取 | 完整文本、作者、图片 |
| 视频处理 | 提取视频逐字稿，默认插入视频链接，可选下载 |

### 通用能力

| 功能 | 说明 |
|------|------|
| 自动分类 | 根据内容关键词归入 素材 / 灵感 / 参考 / 学习资料 / 其他 |
| 自动标签 | 保留原笔记标签，自动添加来源标签（#小红书 / #Twitter） |

> **其他内容源？** YouTube 视频和播客的逐字稿提取推荐使用 [podcast-transcript-txt-skill](https://github.com/KingJing1/podcast-transcript-txt-skill)。

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

| 能力 | 依赖 | 说明 |
|------|------|------|
| 图片文字识别 | LLM 视觉能力 | 依赖大模型本身的多模态能力，无需额外安装 |
| 视频逐字稿 | `faster-whisper` + `ffmpeg` | 本地 ASR 语音识别，需手动安装 |
| 数据提取 | Python 3.9+ | 运行提取脚本 |

视频逐字稿依赖安装：

```bash
pip install faster-whisper
brew install ffmpeg          # macOS
# sudo apt install ffmpeg    # Linux
```

不装也能正常使用，只是视频笔记不会有逐字稿。

---

## 使用方式

直接发送链接即可，全自动处理：

```
http://xhslink.com/o/xxxxx          → 自动提取并保存
保存小红书 http://xhslink.com/...    → 同上
https://x.com/user/status/123456    → 提取 Twitter 内容
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

## 许可

[CC BY-NC 4.0](LICENSE) — 可自由使用和修改，需署名，禁止商业用途。

---

## 关于作者

**嘉然** — AI 效率工具爱好者

- 公众号：**嘉然学习笔记**
- GitHub：https://github.com/Jiaranbb/xhs-reader

如果觉得有用，欢迎 Star 和关注交流～
