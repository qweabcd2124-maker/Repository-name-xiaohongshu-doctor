"""Note diagnose API routes."""
from __future__ import annotations

import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import DiagnoseResponse

router = APIRouter()
logger = logging.getLogger("noterx.diagnose")

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 200 * 1024 * 1024  # 200 MB
MAX_IMAGE_COUNT = 9
ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_MIME = {"video/mp4", "video/quicktime", "video/webm", "video/x-matroska"}


def _extract_first_video_frame(video_bytes: bytes) -> Optional[bytes]:
    """Extract the first frame from video bytes as JPEG bytes."""
    try:
        import cv2
    except Exception:
        logger.warning("OpenCV unavailable; skip extracting video frame")
        return None

    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(video_bytes)
            temp_path = temp_file.name

        capture = cv2.VideoCapture(temp_path)
        ok, frame = capture.read()
        capture.release()
        if not ok:
            return None

        encode_ok, encoded = cv2.imencode(".jpg", frame)
        if not encode_ok:
            return None
        return encoded.tobytes()
    except Exception as exc:
        logger.warning("Extract video frame failed: %s", exc)
        return None
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                logger.warning("Failed to remove temp file: %s", temp_path)


async def _read_and_validate_image(file: UploadFile, field_name: str) -> bytes:
    if file.content_type and file.content_type not in ALLOWED_IMAGE_MIME:
        raise HTTPException(400, f"不支持的图片格式（{field_name}）：{file.content_type}")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(400, f"{field_name} 超过 {MAX_IMAGE_SIZE // (1024 * 1024)}MB 限制")
    return image_bytes


async def _read_and_validate_video(file: UploadFile) -> bytes:
    if file.content_type and file.content_type not in ALLOWED_VIDEO_MIME:
        raise HTTPException(400, f"不支持的视频格式：{file.content_type}")

    video_bytes = await file.read()
    if len(video_bytes) > MAX_VIDEO_SIZE:
        raise HTTPException(400, f"video_file 超过 {MAX_VIDEO_SIZE // (1024 * 1024)}MB 限制")
    return video_bytes


@router.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose_note(
    title: str = Form(""),
    content: str = Form(""),
    category: str = Form(...),
    tags: str = Form(""),
    cover_image: Optional[UploadFile] = File(None),
    cover_images: Optional[list[UploadFile]] = File(None),
    video_file: Optional[UploadFile] = File(None),
):
    """Receive note content and run multi-agent diagnosis."""
    from app.agents.orchestrator import Orchestrator

    image_files: list[UploadFile] = []
    if cover_image is not None:
        image_files.append(cover_image)
    if cover_images:
        image_files.extend(cover_images)

    if len(image_files) > MAX_IMAGE_COUNT:
        raise HTTPException(400, f"最多只允许上传 {MAX_IMAGE_COUNT} 张图片")

    parsed_images: list[bytes] = []
    for index, image in enumerate(image_files):
        parsed_images.append(await _read_and_validate_image(image, f"cover_images[{index}]") )

    video_bytes: Optional[bytes] = None
    if video_file is not None:
        video_bytes = await _read_and_validate_video(video_file)

    image_bytes = parsed_images[0] if parsed_images else None
    if len(parsed_images) > 1:
        logger.info("Received %d images; use first image as cover for current pipeline", len(parsed_images))

    if image_bytes is None and video_bytes is not None:
        extracted = _extract_first_video_frame(video_bytes)
        if extracted is not None:
            image_bytes = extracted
            logger.info("Using first frame from video for visual analysis")
        else:
            logger.info("Video uploaded but no frame extracted; continue without visual image")

    tag_list = [token.strip() for token in tags.split(",") if token.strip()] if tags else []

    if image_bytes and not title.strip():
        logger.info("Title is empty; trying OCR")
        from app.agents.base_agent import _get_client
        from app.analysis.ocr_processor import OCRProcessor

        ocr = OCRProcessor()
        ocr_result = await ocr.extract_text(image_bytes, client=_get_client())
        if ocr_result.get("title"):
            title = ocr_result["title"]
        if not content.strip() and ocr_result.get("content"):
            content = ocr_result["content"]
        if not tag_list and ocr_result.get("tags"):
            tag_list = ocr_result["tags"]
        logger.info("OCR output: title=%s, tags=%s", title[:30] if title else "", tag_list)

    if not title.strip():
        raise HTTPException(400, "请输入标题，或上传可识别标题的图片/视频")

    orchestrator = Orchestrator()
    report = await orchestrator.run(
        title=title,
        content=content,
        category=category,
        tags=tag_list,
        cover_image=image_bytes,
    )
    return report


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload one image and return visual analysis result."""
    from app.analysis.image_analyzer import ImageAnalyzer

    image_bytes = await _read_and_validate_image(file, "file")
    analyzer = ImageAnalyzer()
    return analyzer.analyze(image_bytes)
