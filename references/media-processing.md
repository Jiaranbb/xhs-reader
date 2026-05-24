# 媒体处理

## 视频笔记

优先使用页面或平台已经提供的字幕/文案。只有在没有可用字幕且用户需要逐字稿时，才使用本地 ASR。

没有可用字幕的视频：

1. 下载视频：

```bash
yt-dlp -o "/tmp/xhs_video.%(ext)s" "$YTDLP_URL"
```

2. 提取音频：

```bash
ffmpeg -i /tmp/xhs_video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 /tmp/xhs_audio.wav
```

3. 运行 ASR：

```bash
python3 {scripts_path}/xhs_extract.py --url "/tmp/xhs_audio.wav" --action transcribe --asr-model {asr_model}
```

如果缺少 `faster-whisper` 或 `ffmpeg`，写入：`无字幕，且本地 ASR 依赖缺失`。继续保存笔记。

严格逐字稿规则：保留字幕或 ASR 原文。有时间戳就保留时间戳。不要总结、改写或缩短逐字稿。

视频嵌入格式：

```html
<video src="{video URL or local relative path}" controls></video>
```

## 图片含大量文字

图片中有大量文字时使用 OCR。

1. 下载图片：

```bash
curl -sL -o "/tmp/xhs_img_$i.webp" "${IMAGES[$i-1]}"
```

2. OCR 优先级：
   - 本地可用的 Tesseract OCR
   - agent 的图片理解能力
   - Gemini CLI 或同类视觉模型
   - 浏览器截图兜底，且必须先通过账号安全门禁

Tesseract 示例：

```bash
python3 -c "from PIL import Image; img=Image.open('/tmp/xhs_img_$i.webp'); img=img.convert('RGB'); img.save('/tmp/xhs_img_$i.jpg','JPEG',quality=85)"
python3 -c "
import pytesseract
from PIL import Image
all_text = []
for i in range(1, $IMAGE_COUNT + 1):
    img = Image.open(f'/tmp/xhs_img_{i}.jpg')
    text = pytesseract.image_to_string(img, lang='chi_sim+eng')
    all_text.append(text.strip())
print('\n\n'.join(all_text))
"
```

3. 将 OCR 文本与 `desc` 去重。保留完整 OCR 文本，只删除正文中重复的部分。
4. 清理临时文件：

```bash
rm -f /tmp/xhs_img_*.webp /tmp/xhs_img_*.jpg
```

## 普通图文笔记

使用 `desc` 作为正文。不需要 OCR。只有在有帮助或用户要求下载图片时，才列出图片 URL。
