#!/usr/bin/env python3
"""
xhs_extract.py - 小红书笔记数据提取 & 视频 ASR 转录

用法:
  # 提取笔记数据（返回 JSON）
  python3 xhs_extract.py --url "https://www.xiaohongshu.com/explore/xxx" --action extract

  # 视频 ASR 转录（返回纯文本）
  python3 xhs_extract.py --url "https://video-url.mp4" --action transcribe --asr-model small

  # 检查依赖
  python3 xhs_extract.py --doctor
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_ASR_MODEL = os.getenv("XHS_ASR_MODEL", "small").strip() or "small"
DEFAULT_MODEL_ROOT = Path(
    os.getenv("XHS_ASR_MODEL_ROOT", str(Path.home() / ".codex/models/faster-whisper"))
).expanduser()
SUPPORTED_ASR_MODELS = ("small", "medium")


# ---------------------------------------------------------------------------
# URL resolution
# ---------------------------------------------------------------------------

def resolve_short_url(url: str) -> str:
    """Follow redirects on xhslink.com short URLs to get the final URL."""
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.url
    except Exception:
        # Fallback: use curl
        try:
            result = subprocess.run(
                ["curl", "-sI", "-L", "-o", "/dev/null", "-w", "%{url_effective}", url],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
    return url


def normalize_url(raw_input: str) -> str:
    """Extract and normalize a Xiaohongshu note URL from various input formats."""
    text = raw_input.strip()

    # Extract xhslink short URL
    m = re.search(r'https?://xhslink\.com/\S+', text)
    if m:
        short_url = m.group(0).rstrip('.,;!?)')
        return resolve_short_url(short_url)

    # Extract full xiaohongshu.com URL
    m = re.search(r'https?://(?:www\.)?xiaohongshu\.com/\S+', text)
    if m:
        return m.group(0).rstrip('.,;!?)')

    # Handle discovery/item/xxx or explore/xxx
    m = re.search(r'(?:discovery/item|explore)/([a-f0-9]+)', text)
    if m:
        return f"https://www.xiaohongshu.com/explore/{m.group(1)}"

    # If it looks like a bare note ID (hex string)
    m = re.match(r'^[a-f0-9]{24}$', text)
    if m:
        return f"https://www.xiaohongshu.com/explore/{text}"

    return text


# ---------------------------------------------------------------------------
# HTTP extraction
# ---------------------------------------------------------------------------

def fetch_page_html(url: str) -> str:
    """Fetch page HTML with anti-scraping headers."""
    headers = {
        "User-Agent": UA,
        "Referer": "https://www.xiaohongshu.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_initial_state(html: str) -> Optional[Dict]:
    """Extract __INITIAL_STATE__ JSON from page HTML."""
    pattern = r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\})\s*</script>'
    m = re.search(pattern, html, re.DOTALL)
    if not m:
        # Try alternative pattern without closing script tag
        pattern2 = r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\})\s*;?\s*(?:</script>|window\.)'
        m = re.search(pattern2, html, re.DOTALL)
    if not m:
        return None

    raw = m.group(1)
    # Replace JavaScript undefined with null for valid JSON
    raw = re.sub(r'\bundefined\b', 'null', raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def parse_note_from_state(state: Dict) -> Dict[str, Any]:
    """Parse note data from __INITIAL_STATE__ JSON."""
    note_map = state.get("note", {}).get("noteDetailMap", {})
    if not note_map:
        raise ValueError("No noteDetailMap found in state")

    note_id = list(note_map.keys())[0]
    note = note_map[note_id].get("note", {})

    # Extract tags from desc and tagList
    tags = []
    tag_list = note.get("tagList", [])
    for t in tag_list:
        name = t.get("name", "").strip()
        if name:
            tags.append(name)

    # Also extract inline #tags from desc
    desc = note.get("desc", "")
    inline_tags = re.findall(r'#(\S+?)(?:\s|$|#|\[)', desc)
    for t in inline_tags:
        t = t.strip()
        if t and t not in tags:
            tags.append(t)

    # Clean desc: remove [话题] markers
    clean_desc = re.sub(r'\[话题\]', '', desc).strip()
    # Remove trailing #tags block
    clean_desc = re.sub(r'(?:\s*#\S+)+\s*$', '', clean_desc).strip()

    # Images
    images = []
    for img in note.get("imageList", []):
        url = img.get("urlDefault") or img.get("url") or ""
        if url.startswith("http"):
            images.append({
                "url": url,
                "width": img.get("width", 0),
                "height": img.get("height", 0),
            })

    # Video
    video = None
    if note.get("video") and note.get("type") == "video":
        stream = note["video"].get("media", {}).get("stream", {})
        h264_urls = [v.get("masterUrl", "") for v in stream.get("h264", []) if v.get("masterUrl")]
        h265_urls = [v.get("masterUrl", "") for v in stream.get("h265", []) if v.get("masterUrl")]
        video = {
            "h264": h264_urls,
            "h265": h265_urls,
        }

    # Interact info
    interact = note.get("interactInfo", {})

    # Comments (may or may not be present)
    comments = []
    comment_data = state.get("comment", {}) or {}
    comment_list = comment_data.get("comments", []) or []
    if not comment_list:
        # Try alternative paths
        for key in note_map:
            c = note_map[key].get("comments", [])
            if c:
                comment_list = c
                break

    for c in comment_list:
        comments.append({
            "user": c.get("userInfo", {}).get("nickname", "") or c.get("user", {}).get("nickname", ""),
            "content": c.get("content", ""),
            "likes": int(c.get("likeCount", 0) or c.get("likes", 0) or 0),
        })

    # Sort by likes descending, take top 10
    comments.sort(key=lambda x: x["likes"], reverse=True)
    comments = comments[:10]

    return {
        "noteId": note_id,
        "title": note.get("title", ""),
        "desc": clean_desc,
        "type": note.get("type", "normal"),
        "tags": tags,
        "images": images,
        "video": video,
        "author": note.get("user", {}).get("nickname", ""),
        "userId": note.get("user", {}).get("userId", ""),
        "likes": str(interact.get("likedCount", "0")),
        "collects": str(interact.get("collectedCount", "0")),
        "commentCount": str(interact.get("commentCount", "0")),
        "comments": comments,
    }


def extract_note(url: str) -> Dict[str, Any]:
    """Main extraction: fetch page and parse note data."""
    normalized = normalize_url(url)
    html = fetch_page_html(normalized)
    state = extract_initial_state(html)
    if not state:
        raise ValueError(
            "Failed to extract __INITIAL_STATE__ from page. "
            "Anti-scraping may be active. Try Chrome fallback."
        )
    result = parse_note_from_state(state)
    result["url"] = normalized
    return result


# ---------------------------------------------------------------------------
# ASR transcription
# ---------------------------------------------------------------------------

def seconds_to_hms(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def resolve_model_arg(model_name: str) -> Tuple[str, str, Path, Path]:
    """Resolve the model argument for faster-whisper."""
    model_root = DEFAULT_MODEL_ROOT
    cache_dir = model_root / model_name
    if cache_dir.exists() and any(cache_dir.iterdir()):
        return str(cache_dir), "local", model_root, cache_dir
    return model_name, "download", model_root, cache_dir


def download_media(url: str, dest: Path) -> None:
    """Download media file from URL."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Referer": "https://www.xiaohongshu.com",
    })
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f, length=1 << 20)


def extract_audio(video_path: Path, audio_path: Path) -> None:
    """Extract audio from video using ffmpeg."""
    subprocess.run(
        ["ffmpeg", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le",
         "-ar", "16000", "-ac", "1", str(audio_path), "-y"],
        capture_output=True, timeout=120, check=True
    )


def run_local_asr(audio_path: Path, asr_model: str) -> Tuple[List[str], Dict[str, Any]]:
    """Run faster-whisper ASR on audio file."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError(
            "ASR requires faster-whisper. Install: pip install faster-whisper"
        ) from e

    model_arg, model_source, model_root, cache_dir = resolve_model_arg(asr_model)

    # Auto-detect best device: CUDA > MPS (Apple Silicon) > CPU
    import torch
    if torch.cuda.is_available():
        asr_device, asr_compute = "cuda", "float16"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        asr_device, asr_compute = "auto", "int8"
    else:
        asr_device, asr_compute = "cpu", "int8"

    model = WhisperModel(
        model_arg,
        device=asr_device,
        compute_type=asr_compute,
        download_root=str(model_root),
    )
    segments_gen, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=True,
    )

    # Collect segments with timestamps
    raw_segments = []
    for seg in segments_gen:
        text = getattr(seg, "text", "").strip()
        if not text:
            continue
        raw_segments.append({
            "start": float(getattr(seg, "start", 0.0) or 0.0),
            "end": float(getattr(seg, "end", 0.0) or 0.0),
            "text": text,
        })

    if not raw_segments:
        raise RuntimeError("ASR returned empty transcript")

    lines: List[str] = []
    for seg in raw_segments:
        ts = seconds_to_hms(seg["start"])
        lines.append(f"[{ts}] {seg['text']}")

    asr_meta = {
        "model": asr_model,
        "model_source": model_source,
        "language": str(getattr(info, "language", "")),
        "duration_sec": float(getattr(info, "duration", 0.0) or 0.0),
        "line_count": len(lines),
    }
    return lines, asr_meta


def transcribe_video(video_url: str, asr_model: str = "small") -> Dict[str, Any]:
    """Download video, extract audio, run ASR, return transcript.

    video_url can be:
    - A remote URL (http/https) → download, extract audio, transcribe
    - A local .wav file path → transcribe directly
    - A local video file path → extract audio, transcribe
    """
    local_path = Path(video_url)

    # Case 1: local .wav file → transcribe directly
    if local_path.exists() and local_path.suffix == ".wav":
        lines, meta = run_local_asr(local_path, asr_model)
        return {"transcript": "\n".join(lines), "meta": meta}

    # Case 2: local video file → extract audio, then transcribe
    if local_path.exists():
        with tempfile.TemporaryDirectory(prefix="xhs_asr_") as td:
            audio_path = Path(td) / "audio.wav"
            try:
                extract_audio(local_path, audio_path)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                raise RuntimeError(f"ffmpeg failed: {e}. Install: brew install ffmpeg") from e
            lines, meta = run_local_asr(audio_path, asr_model)
        return {"transcript": "\n".join(lines), "meta": meta}

    # Case 3: remote URL → download, extract audio, transcribe
    with tempfile.TemporaryDirectory(prefix="xhs_asr_") as td:
        td_path = Path(td)
        ext = Path(urllib.parse.urlparse(video_url).path).suffix or ".mp4"
        video_path = td_path / f"video{ext}"
        download_media(video_url, video_path)

        audio_path = td_path / "audio.wav"
        try:
            extract_audio(video_path, audio_path)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(
                f"ffmpeg failed: {e}. Install: brew install ffmpeg"
            ) from e

        lines, meta = run_local_asr(audio_path, asr_model)

    return {
        "transcript": "\n".join(lines),
        "meta": meta,
    }


# ---------------------------------------------------------------------------
# Doctor check
# ---------------------------------------------------------------------------

def doctor() -> int:
    """Check dependencies."""
    ok = True

    # Python version
    print(f"Python: {sys.version}")
    if sys.version_info < (3, 9):
        print("  WARN: Python 3.9+ recommended")

    # curl
    if shutil.which("curl"):
        print("curl: OK")
    else:
        print("curl: MISSING")
        ok = False

    # ffmpeg
    if shutil.which("ffmpeg"):
        print("ffmpeg: OK")
    else:
        print("ffmpeg: MISSING (brew install ffmpeg)")
        ok = False

    # faster-whisper
    try:
        import faster_whisper
        print(f"faster-whisper: OK ({faster_whisper.__version__})")
    except ImportError:
        print("faster-whisper: MISSING (pip install faster-whisper)")
        ok = False

    # Model cache
    for model_name in SUPPORTED_ASR_MODELS:
        cache = DEFAULT_MODEL_ROOT / model_name
        if cache.exists() and any(cache.iterdir()):
            print(f"ASR model '{model_name}': cached at {cache}")
        else:
            print(f"ASR model '{model_name}': not cached (will download on first use)")

    return 0 if ok else 1


# ---------------------------------------------------------------------------
# VTT subtitle parsing
# ---------------------------------------------------------------------------

def parse_vtt(vtt_path: Path) -> List[Dict]:
    """Parse a WebVTT file into timestamped segments."""
    segments = []
    text = vtt_path.read_text(encoding="utf-8")
    # Remove WEBVTT header and metadata
    blocks = re.split(r"\n\n+", text.strip())
    for block in blocks:
        lines = block.strip().split("\n")
        # Find timestamp line (contains -->)
        ts_line = None
        for i, line in enumerate(lines):
            if "-->" in line:
                ts_line = i
                break
        if ts_line is None:
            continue
        # Parse timestamps
        ts_match = re.match(r"([\d:.,]+)\s*-->\s*([\d:.,]+)", lines[ts_line])
        if not ts_match:
            continue
        start_str, end_str = ts_match.group(1), ts_match.group(2)
        start = _vtt_ts_to_seconds(start_str)
        end = _vtt_ts_to_seconds(end_str)
        # Collect text lines after timestamp, extract text from VTT tags
        text_lines = lines[ts_line + 1:]
        raw_text = " ".join(text_lines)
        # Handle Twitter X-word-ms tags: extract text content between > and </
        xword_match = re.search(r"<X-word-ms[^>]*>(.+?)</X-word-ms>", raw_text)
        if xword_match:
            clean_text = xword_match.group(1).strip()
        else:
            # Standard VTT: strip HTML-like tags
            clean_text = re.sub(r"<[^>]+>", "", raw_text).strip()
        if clean_text:
            segments.append({"start": start, "end": end, "text": clean_text})
    return segments


def _vtt_ts_to_seconds(ts: str) -> float:
    """Convert VTT timestamp (HH:MM:SS.mmm or MM:SS.mmm) to seconds."""
    ts = ts.replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(ts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Xiaohongshu note extractor & video ASR")
    parser.add_argument("--url", help="Xiaohongshu note URL or share text")
    parser.add_argument(
        "--action",
        choices=("extract", "transcribe", "resolve"),
        default="extract",
        help="Action: extract note data, transcribe video, or resolve URL"
    )
    parser.add_argument(
        "--asr-model",
        default=DEFAULT_ASR_MODEL,
        choices=SUPPORTED_ASR_MODELS,
        help=f"ASR model (default: {DEFAULT_ASR_MODEL})"
    )
    parser.add_argument("--doctor", action="store_true", help="Check dependencies")
    args = parser.parse_args()

    if args.doctor:
        return doctor()

    if not args.url:
        parser.error("--url is required")

    try:
        if args.action == "resolve":
            result = normalize_url(args.url)
            print(result)
        elif args.action == "extract":
            result = extract_note(args.url)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.action == "transcribe":
            result = transcribe_video(args.url, args.asr_model)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
