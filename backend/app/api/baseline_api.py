"""
Baseline 数据查询 API
"""
from fastapi import APIRouter

from app.baseline.comparator import BaselineComparator

router = APIRouter()


@router.get("/baseline/{category}")
async def get_baseline(category: str):
    """
    获取指定垂类的 baseline 统计概览。

    @param category - 垂类标识 (food / fashion / tech)
    """
    comparator = BaselineComparator()
    stats = comparator.get_category_stats(category)
    return stats
