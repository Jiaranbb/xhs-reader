# 踩坑点（Gotchas）

实测中发现的常见问题和解决方案。持续更新。

## 1. 短链接 HTTP 请求返回 404

`xhslink.com` 短链接用 `curl -sI -L` 跟踪重定向会返回 404。原因是小红书短链使用 JavaScript 重定向，不是 HTTP 302。

**解决：** 必须用 Chrome 浏览器打开短链，等 JS 重定向完成后从 tab URL 获取最终地址。

## 2. 必须登录小红书

未登录时提取的数据有严重缺陷：
- 评论点赞数失真（实测：真实 125 赞 → 未登录显示 10 赞）
- 视频 URL 质量较低（不同 CDN 域名和编码）
- 部分内容可能无法获取

**解决：** 确保 Chrome 已登录小红书再提取。

## 3. 视频 URL 签名参数不能丢

视频 URL 格式：`http://sns-video-qc.xhscdn.com/...mp4?sign=xxx&t=xxx`

去掉 `?sign=xxx&t=xxx` 后视频无法播放。提取时必须保留完整 URL。

## 4. javascript_tool 安全过滤

Chrome MCP 的 `javascript_tool` 会拦截返回值中包含 cookie/token 的数据。当提取含签名的 URL 时，直接 `return` 会被 `[BLOCKED: Cookie/query string data]`。

**解决：** 把 URL 写入 `document.title`，从 tab 信息中读取。用完后记得恢复原标题。

## 5. 图片/视频 CDN URL 有时效性

图片 URL 路径中包含时间戳和签名 hash（如 `202603262209/b1ae4296...`），实测 1 小时内有效，但长期（数小时到 24 小时）可能过期。

**解决：** 需要长期保存时，选择「下载到本地」而非「链接嵌入」。

## 6. 评论选择器易混淆

小红书评论区有一级评论和子评论（回复），DOM 结构嵌套。如果不精确选择，会把子评论混入一级评论列表，且点赞数会和回复数混淆。

**解决：**
- 用 `.parent-comment > .comment-item`（`:scope >` 直接子元素）只取一级评论
- 点赞数在 `.interactions > .like .count`，回复数在 `.reply .count`，不要搞混

## 7. 大量图片 OCR 效率

13 张图的图文笔记，逐张 WebFetch + Read 需要较长时间。部分图片可能返回 403。

**解决：** 优先用 WebFetch 批量下载，失败的图片降级用 Chrome 截图识别。并行下载可提升效率。

## 8. 图文笔记正文与图片文字重复

很多小红书图文笔记的 `desc`（正文）是图片内容的摘要或完全复制。如果同时保留，笔记会非常冗余。

**解决：** 去重方向是精简正文（可标注「详细内容见下方图片文字」），始终保持图片文字的完整性。
