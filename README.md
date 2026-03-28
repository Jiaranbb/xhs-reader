# xhs-reader

一键保存小红书 / Twitter 笔记到 Obsidian，自动提取文字、图片 OCR、视频逐字稿和热门评论。

## 功能

- 发送小红书或 Twitter 分享链接即可自动处理
- 支持图文笔记和视频笔记
- 图文笔记自动识别图片中的文字（OCR）
- 视频笔记自动转录为逐字稿（ASR）
- 提取热门评论 Top 10（小红书）
- 根据内容关键词自动分类保存
- 整理为格式化的 Obsidian Markdown 笔记
- 可选下载图片/视频到本地永久保存

## 使用方式

直接发送小红书分享链接或分享文本：

```
http://xhslink.com/o/xxxxx
```

或者说「保存小红书 + 链接」即可触发。Twitter/X 链接同样支持。

## 安装

### Claude Code

将本目录复制到 Claude Code 的 Skills 目录：

```bash
cp -r xhs-reader ~/.claude/skills/
```

### OpenClaw

```bash
clawhub install xhs-reader
```

### 其他 AI Agent

将本目录放到你的 agent 能读取的 skills 目录中。核心文件是 `SKILL.md`，其中包含完整的工作流指令。

## 配置

首次使用前，编辑 `config.json` 设置你的 Obsidian Vault 路径：

```json
{
  "obsidian_vault": "~/Documents/My Vault",
  ...
}
```

详细配置说明见 [setup.md](setup.md)。

## 前置条件

1. AI agent 环境（Claude Code / OpenClaw / 其他支持 Skill 的 agent）
2. Chrome 浏览器已登录小红书（未登录会导致数据不完整）
3. Python 3.9+
4. （可选）视频逐字稿依赖：
   ```bash
   pip install faster-whisper
   brew install ffmpeg  # macOS
   ```

## 目录结构

```
xhs-reader/
├── SKILL.md              # 核心工作流（agent 读取此文件执行）
├── config.json           # 用户配置（Vault 路径、分类等）
├── setup.md              # 首次配置引导
├── assets/
│   └── note-template.md  # Obsidian 笔记模板
├── scripts/
│   └── xhs_extract.py    # Python 数据提取 & ASR 引擎
├── references/
│   ├── extract-js.md     # 浏览器数据提取 JS 代码
│   ├── comments-js.md    # 评论提取 JS 代码
│   └── gotchas.md        # 常见问题与解决方案
├── README.md
└── LICENSE
```

## 声明

本项目仅供个人学习和研究使用。请尊重小红书平台的内容版权及用户隐私，不得将本工具用于批量爬取、商业用途或任何违反平台服务条款的行为。使用者应自行承担使用风险。

## 关于作者

**嘉然** — AI 效率工具爱好者

- 公众号：**嘉然学习笔记**
- GitHub：https://github.com/Jiaranbb/xhs-reader

如果觉得有用，欢迎 Star 和关注交流～
