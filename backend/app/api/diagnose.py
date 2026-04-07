"""
笔记诊断 API
"""
from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

from app.models.schemas import DiagnoseRequest, DiagnoseResponse

router = APIRouter()


@router.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose_note(
    title: str = Form(...),
    content: str = Form(""),
    category: str = Form(...),
    tags: str = Form(""),
    cover_image: Optional[UploadFile] = File(None),
):
    """
    接收笔记内容，执行多Agent诊断，返回诊断报告。

    @param title - 笔记标题
    @param content - 笔记正文
    @param category - 垂类 (food / fashion / tech)
    @param tags - 标签，逗号分隔
    @param cover_image - 封面图片（可选）
    """
    from app.agents.orchestrator import Orchestrator

    image_bytes = None
    if cover_image:
        image_bytes = await cover_image.read()

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

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
    """上传封面图片，返回图像分析结果"""
    from app.analysis.image_analyzer import ImageAnalyzer

    image_bytes = await file.read()
    analyzer = ImageAnalyzer()
    result = analyzer.analyze(image_bytes)
    return result
