# Gate 5: 评论提取 JavaScript

## 提取热门评论（Top 10）

用于 Chrome `javascript_tool`，从页面 DOM 提取一级评论并按点赞排序：

```javascript
(() => {
  const parents = document.querySelectorAll('.parent-comment');
  const results = [];
  parents.forEach(p => {
    const item = p.querySelector(':scope > .comment-item');
    if (!item) return;
    const name = item.querySelector('.author a.name')?.textContent?.trim() || '';
    const content = item.querySelector('.content .note-text')?.textContent?.trim() || '';
    const likeDiv = item.querySelector('.interactions > .like');
    const likeCount = likeDiv?.querySelector('.count')?.textContent?.trim() || '0';
    const likes = parseInt(likeCount.replace(/[^\d]/g, '')) || 0;
    if (content) results.push({ user: name, content: content.substring(0, 300), likes });
  });
  results.sort((a, b) => b.likes - a.likes);
  return JSON.stringify(results.slice(0, 10));
})()
```

## 选择器说明

- `.parent-comment` — 一级评论容器
- `:scope > .comment-item` — 直接子元素，排除子评论（回复）
- `.author a.name` — 用户名
- `.content .note-text` — 评论内容
- `.interactions > .like .count` — 点赞数（注意区分 `.reply .count` 回复数）

## 注意

- 这些 CSS 选择器基于 2026-03 的页面结构，小红书改版后可能失效
- 如果选择器失效，可用 `read_page` 或 `get_page_text` 作为降级方案
- 提取前需先滚动到评论区（scroll down 5-10 ticks）等待评论加载
