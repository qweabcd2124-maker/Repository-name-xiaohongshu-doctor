import { useRef, useState } from "react";
import html2canvas from "html2canvas";
import type { DiagnoseResult } from "../utils/api";

interface Props {
  report: DiagnoseResult;
  title: string;
}

/**
 * 可导出的诊断卡片 - 使用 html2canvas 生成分享图
 */
export default function DiagnoseCard({ report, title }: Props) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    if (!cardRef.current) return;
    setExporting(true);
    try {
      const canvas = await html2canvas(cardRef.current, {
        scale: 2,
        backgroundColor: "#ffffff",
        useCORS: true,
      });
      const link = document.createElement("a");
      link.download = `薯医诊断-${title.slice(0, 10)}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    } catch (err) {
      console.error("导出失败", err);
    } finally {
      setExporting(false);
    }
  };

  const gradeColor =
    report.grade === "S" || report.grade === "A"
      ? "text-emerald-600"
      : report.grade === "B"
      ? "text-blue-600"
      : "text-red-500";

  return (
    <div>
      <button
        onClick={handleExport}
        disabled={exporting}
        className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-semibold hover:from-emerald-600 hover:to-teal-600 transition-all shadow-md disabled:opacity-50"
      >
        {exporting ? "导出中..." : "📤 导出诊断卡片"}
      </button>

      {/* Exportable card content */}
      <div
        ref={cardRef}
        className="mt-4 bg-white rounded-2xl border border-gray-100 overflow-hidden"
        style={{ width: 375 }}
      >
        {/* Card Header */}
        <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-5 py-4 text-white">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">💊</span>
            <span className="font-bold">薯医 NoteRx 诊断报告</span>
          </div>
          <p className="text-white/90 text-sm line-clamp-1">「{title}」</p>
        </div>

        {/* Score */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div>
            <p className="text-sm text-gray-500">综合评分</p>
            <p className="text-3xl font-bold text-gray-800">
              {Math.round(report.overall_score)}
            </p>
          </div>
          <span className={`text-4xl font-bold ${gradeColor}`}>
            {report.grade}
          </span>
        </div>

        {/* Dimensions */}
        <div className="px-5 py-3 space-y-2">
          {Object.entries(report.radar_data).map(([key, val]) => {
            const labels: Record<string, string> = {
              content: "内容质量",
              visual: "视觉表现",
              growth: "增长策略",
              user_reaction: "用户反应",
              overall: "综合",
            };
            return (
              <div key={key} className="flex items-center gap-2">
                <span className="text-xs text-gray-500 w-16">
                  {labels[key] || key}
                </span>
                <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-emerald-400 rounded-full"
                    style={{ width: `${val}%` }}
                  />
                </div>
                <span className="text-xs font-medium text-gray-600 w-8 text-right">
                  {Math.round(val)}
                </span>
              </div>
            );
          })}
        </div>

        {/* Top Issues */}
        <div className="px-5 py-3 border-t border-gray-100">
          <p className="text-xs font-medium text-gray-500 mb-2">
            主要问题
          </p>
          {report.issues.slice(0, 3).map((issue, i) => (
            <p key={i} className="text-xs text-gray-600 mb-1">
              {i + 1}. {typeof issue === "string" ? issue : issue.description}
            </p>
          ))}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 bg-gray-50 text-center">
          <p className="text-xs text-gray-400">
            薯医 NoteRx — 你的笔记，值得被看见。
          </p>
        </div>
      </div>
    </div>
  );
}
