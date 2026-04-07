import { useLocation, useNavigate } from "react-router-dom";
import type { DiagnoseResult } from "../utils/api";
import ScoreCard from "../components/ScoreCard";
import RadarChart from "../components/RadarChart";
import AgentDebate from "../components/AgentDebate";
import SimulatedComments from "../components/SimulatedComments";
import SuggestionList from "../components/SuggestionList";
import DiagnoseCard from "../components/DiagnoseCard";

/**
 * 诊断报告页 - 展示完整诊断结果
 */
export default function Report() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as {
    report: DiagnoseResult;
    params: { title: string; category: string };
    isFallback?: boolean;
  } | null;

  if (!state) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500">暂无诊断数据</p>
          <button
            onClick={() => navigate("/")}
            className="mt-4 text-emerald-600 underline"
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  const { report, params, isFallback } = state;

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50 pb-20">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-gray-100">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => navigate("/")}
            className="text-gray-500 hover:text-gray-700 text-sm"
          >
            ← 重新诊断
          </button>
          <div className="flex items-center gap-1.5">
            <span className="text-lg">💊</span>
            <span className="font-semibold text-emerald-600">诊断报告</span>
          </div>
          <div className="w-16" />
        </div>
      </header>

      {isFallback && (
        <div className="max-w-3xl mx-auto px-4 mt-3">
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-amber-700 text-sm">
            ⚠️ 当前展示的是演示数据（后端不可用）
          </div>
        </div>
      )}

      <main className="max-w-3xl mx-auto px-4 mt-6 space-y-6">
        {/* Score Card */}
        <ScoreCard
          score={report.overall_score}
          grade={report.grade}
          title={params.title}
        />

        {/* Radar Chart */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 className="font-semibold text-gray-800 mb-4">📊 五维诊断雷达图</h2>
          <RadarChart data={report.radar_data} />
        </div>

        {/* Suggestions */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 className="font-semibold text-gray-800 mb-4">💡 优化建议</h2>
          <SuggestionList suggestions={report.suggestions} />
          {report.optimized_title && (
            <div className="mt-4 p-4 bg-emerald-50 rounded-xl">
              <p className="text-sm text-emerald-700 font-medium">AI建议标题：</p>
              <p className="text-emerald-800 mt-1">
                「{report.optimized_title}」
              </p>
            </div>
          )}
        </div>

        {/* Agent Debate */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 className="font-semibold text-gray-800 mb-4">
            🤖 多Agent诊断详情
          </h2>
          <AgentDebate
            opinions={report.agent_opinions}
            summary={report.debate_summary}
          />
        </div>

        {/* Simulated Comments */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 className="font-semibold text-gray-800 mb-4">
            💬 AI模拟评论区
          </h2>
          <SimulatedComments comments={report.simulated_comments} />
        </div>

        {/* Export Card */}
        <DiagnoseCard report={report} title={params.title} />
      </main>
    </div>
  );
}
