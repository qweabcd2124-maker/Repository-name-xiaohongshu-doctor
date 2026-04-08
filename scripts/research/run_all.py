"""
一键运行完整研究 Pipeline。
根据数据可用性自动跳过缺数据的步骤。

Usage:
    python scripts/research/run_all.py [--skip-llm] [--skip-download]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PYTHON = sys.executable

STEPS = [
    ("01_normalize",           "01_import_data.py",           "数据导入与清洗",       False),
    ("02_download",            "02_download_covers.py",       "下载封面图片",         True),
    ("03_traditional",         "03_traditional_analysis.py",  "传统统计分析",         False),
    ("04_cover_vision",        "04_llm_analysis.py --covers", "封面视觉分析 (omni)", True),
    ("05_content_llm",         "04_llm_analysis.py --content","内容模式分析 (pro)",   True),
    ("06_tag_llm",             "04_llm_analysis.py --tags",   "标签策略分析 (pro)",   True),
    ("07_persona",             "06_user_persona.py",          "用户画像",             True),
    ("08_scoring_model",       "08_build_scoring_model.py",   "构建评分模型",         False),
    ("09_prompts",             "09_generate_prompts.py",      "生成增强提示词",       True),
    ("10_validate",            "10_validate_model.py",        "模型验证",             False),
    ("11_report",              "11_final_report.py",          "最终报告",             True),
]


def run_step(script: str, desc: str, skip_llm: bool, is_llm: bool) -> bool:
    if skip_llm and is_llm:
        print(f"  ⊘ 跳过 (--skip-llm): {desc}")
        return True

    parts = script.split()
    cmd = [PYTHON, str(SCRIPT_DIR / parts[0])] + parts[1:]

    print(f"\n{'='*60}")
    print(f"  ▶ {desc}")
    print(f"    {' '.join(cmd)}")
    print(f"{'='*60}")

    t0 = time.time()
    result = subprocess.run(cmd, cwd=str(SCRIPT_DIR.parent.parent))
    elapsed = time.time() - t0

    if result.returncode == 0:
        print(f"  ✓ 完成 ({elapsed:.1f}s)")
        return True
    else:
        print(f"  ✗ 失败 (exit={result.returncode}, {elapsed:.1f}s)")
        return False


def main():
    parser = argparse.ArgumentParser(description="运行完整研究 Pipeline")
    parser.add_argument("--skip-llm", action="store_true", help="跳过所有 LLM 调用步骤")
    parser.add_argument("--skip-download", action="store_true", help="跳过图片下载")
    parser.add_argument("--from-step", type=int, default=1, help="从第 N 步开始")
    args = parser.parse_args()

    print("=" * 60)
    print("NoteRx 研究 Pipeline — 全流程")
    print("=" * 60)

    t_start = time.time()
    results = []

    for i, (name, script, desc, is_llm) in enumerate(STEPS, 1):
        if i < args.from_step:
            continue
        if args.skip_download and "download" in name:
            print(f"  ⊘ 跳过 (--skip-download): {desc}")
            results.append((desc, True))
            continue

        ok = run_step(script, desc, args.skip_llm, is_llm)
        results.append((desc, ok))

        if not ok and not is_llm:
            print(f"\n关键步骤失败，停止 Pipeline")
            break

    # 总结
    total = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"Pipeline 完成 ({total:.0f}s)")
    print(f"{'='*60}")
    for desc, ok in results:
        status = "✓" if ok else "✗"
        print(f"  {status} {desc}")


if __name__ == "__main__":
    main()
