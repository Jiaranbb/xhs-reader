# 配置参考

首次使用 xhs-reader 时，agent 会自动引导你完成基础配置（Obsidian Vault 路径）。以下是补充说明。

## 浏览器登录

确保浏览器已登录小红书账号（访问 xiaohongshu.com）。未登录会导致：
- 评论点赞数失真
- 视频质量较低
- 部分内容无法获取

## 视频转录依赖（可选）

如果你需要提取视频笔记的逐字稿，需要安装：

```bash
# macOS
pip install faster-whisper
brew install ffmpeg

# Linux
pip install faster-whisper
sudo apt install ffmpeg
```

不安装也可以正常使用，只是视频笔记不会有逐字稿。

## 权限配置

根据你使用的 AI agent 平台，可能需要配置工具权限：

**Claude Code：** 在 skill 目录下创建 `.claude/settings.local.json`：
```json
{
  "permissions": {
    "allow": [
      "Bash(python3 *)",
      "Bash(curl *)",
      "Bash(mkdir *)",
      "WebFetch(domain:xhscdn.com)",
      "WebFetch(domain:xiaohongshu.com)",
      "Write(path:/你的Vault路径/**)",
      "Read(path:/你的Vault路径/**)"
    ]
  }
}
```

**OpenClaw：** 权限由 workspace 配置管理，通常无需额外设置。

**其他 agent：** 请确保 agent 有执行终端命令、读写文件和操作浏览器的权限。

## config.json 字段说明

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `obsidian_vault` | Obsidian Vault 绝对路径 | `""`（首次使用时 agent 会询问） |
| `save_root` | Vault 内的保存根目录 | `00-Inbox/小红书` |
| `attachments_dir` | 附件目录名 | `_attachments` |
| `categories` | 分类列表 | 素材/灵感/参考/学习资料/其他 |
| `asr_model` | ASR 模型 | `small`（可改为 `medium`） |
| `scripts_path` | 脚本目录路径 | 首次使用时自动设为绝对路径 |
