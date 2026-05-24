# Account Safety Gate

本 skill 不使用任何小红书登录账号。小红书默认打开网页版链接；打开后必须检测登录态，通过后才运行 `yt-dlp` 或其他提取，检测到登录态就停止。

## 适用场景

允许先打开或切换到目标小红书页面用于检测。执行本门禁并确认未登录后，才能进行以下动作：

- 从当前 tab 读取最终链接并保存
- 运行 `yt-dlp` 提取元数据或下载媒体
- 浏览器 fallback
- 页面 JS / DOM 提取
- 评论提取
- 媒体 URL 提取
- 截图 OCR

## 检测原则

- 只返回 `loggedIn: true/false/unknown` 和 `signals` 信号名。
- 不输出 cookie、token、localStorage/sessionStorage 的具体值。
- `unknown` 且疑似用户主浏览器时，按不安全处理，停止浏览器提取。
- 不提供继续使用登录态的选项。
- 小红书登录弹窗（手机号登录、二维码、获取验证码、「登录后推荐更懂你的笔记」）不是已登录信号。确认没有真实账号信号后，默认关闭弹窗再继续。

## 登录信号

任一命中都视为已登录或高风险：

- 当前账号头像、当前账号菜单、侧边栏「我」入口、退出登录入口
- DOM 中出现明确的用户信息节点
- cookie/localStorage/sessionStorage 中存在明确登录键，但不要输出值；不要把泛化的 `user`、`login` 文案或登录弹窗缓存当成登录态
- 页面 URL 或接口状态显示已登录用户上下文

## 登录弹窗处理

登录态检测结果为 `loggedIn: false` 且页面有登录弹窗时，默认关闭弹窗。优先按 `Esc`；若无效，点击弹窗右上角 `X` / `关闭` 按钮。关闭后可继续读取页面、评论区可见内容或运行 `yt-dlp`。

如果关闭弹窗后出现真实登录信号，立即停止。

## 可执行 JS 模板

在小红书页面执行。结果只能用于安全判断，不要把 storage/cookie 值复制到日志或最终输出。

```javascript
(() => {
  const signals = [];
  const loginPrompts = [];
  const text = document.body?.innerText || "";

  if (/手机号登录|获取验证码|二维码|登录后推荐更懂你的笔记|新用户可直接登录/.test(text)) {
    loginPrompts.push("login-modal");
  }

  // Strong account-context signals only. Logged-out pages also show
  // "发布/通知/创作中心" and author profile links, so those are not enough.
  const sidebarText = [...document.querySelectorAll("aside, nav, [class*=side], [class*=sidebar]")]
    .map((el) => el.innerText || "")
    .join("\n");
  if (/(^|\n|\s)我($|\n|\s)/.test(sidebarText)) {
    signals.push("sidebar-me-entry");
  }

  const accountSelectors = [
    ["account-avatar", "[class*=account] [class*=avatar], [class*=user] [class*=avatar]"],
    ["user-menu", "[aria-label*='账号'], [aria-label*='个人菜单'], [class*=user][class*=menu]"],
    ["logout-entry", "a[href*='logout'], button[class*=logout], [class*=logout]"]
  ];
  for (const [name, selector] of accountSelectors) {
    if (document.querySelector(selector)) signals.push(name);
  }

  if (/退出登录|切换账号|账号设置/.test(text)) {
    signals.push("logged-in-text");
  }

  try {
    const cookieKeys = document.cookie
      .split(";")
      .map((item) => item.split("=")[0].trim().toLowerCase())
      .filter(Boolean);
    if (cookieKeys.some((key) => /web_session|sessionid|access.?token|uid|user.?id/.test(key))) {
      signals.push("cookie-login-key");
    }
  } catch (e) {}

  try {
    const storageKeys = [];
    for (let i = 0; i < localStorage.length; i++) storageKeys.push(localStorage.key(i).toLowerCase());
    for (let i = 0; i < sessionStorage.length; i++) storageKeys.push(sessionStorage.key(i).toLowerCase());
    if (storageKeys.some((key) => /web_session|sessionid|access.?token|uid|user.?id/.test(key))) {
      signals.push("storage-login-key");
    }
  } catch (e) {}

  const uniqueSignals = [...new Set(signals)];
  return JSON.stringify({
    loggedIn: uniqueSignals.length > 0,
    signals: uniqueSignals,
    loginPrompt: loginPrompts.length > 0,
    promptSignals: [...new Set(loginPrompts)]
  });
})()
```

## 固定停止提示

```text
当前小红书页面处于登录状态。为避免账号处罚风险，xhs-reader 不会使用登录账号抓取。请退出小红书登录或切换到未登录隔离浏览器环境后重试。
```
