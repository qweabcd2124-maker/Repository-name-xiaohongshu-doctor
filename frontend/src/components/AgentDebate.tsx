import { useState } from "react";
import type { AgentOpinion } from "../utils/api";

interface Props {
  opinions: AgentOpinion[];
  summary: string;
}

const AGENT_AVATARS: Record<string, string> = {
  "内容分析师": "📝",
  "视觉诊断师": "🎨",
  "增长策略师": "📈",
  "用户模拟器": "💬",
  "综合裁判": "⚖️",
};

/**
 * Agent 诊断详情与辩论过程可视化
 */
export default function AgentDebate({ opinions, summary }: Props) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      {/* Debate Summary */}
      {summary && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <p className="text-sm font-medium text-amber-700 mb-1">
            ⚔️ 辩论总结
          </p>
          <p className="text-sm text-amber-800">{summary}</p>
        </div>
      )}

      {/* Agent Opinions */}
      {opinions.map((op, idx) => {
        const isExpanded = expandedIdx === idx;
        const avatar = AGENT_AVATARS[op.agent_name] || "🤖";
        const scoreColor =
          op.score >= 75
            ? "text-emerald-600"
            : op.score >= 50
            ? "text-amber-600"
            : "text-red-500";

        return (
          <div
            key={idx}
            className="border border-gray-100 rounded-xl overflow-hidden"
          >
            <button
              onClick={() => setExpandedIdx(isExpanded ? null : idx)}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{avatar}</span>
                <div>
                  <p className="font-medium text-gray-800">{op.agent_name}</p>
                  <p className="text-xs text-gray-400">{op.dimension}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-xl font-bold ${scoreColor}`}>
                  {Math.round(op.score)}
                </span>
                <span
                  className={`text-gray-400 transition-transform ${
                    isExpanded ? "rotate-180" : ""
                  }`}
                >
                  ▾
                </span>
              </div>
            </button>

            {isExpanded && (
              <div className="px-4 pb-4 space-y-3 border-t border-gray-50">
                {/* Issues */}
                {op.issues.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-medium text-red-500 mb-1.5">
                      发现问题
                    </p>
                    {op.issues.map((issue, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-2 text-sm text-gray-600 mb-1"
                      >
                        <span className="text-red-400 mt-0.5">•</span>
                        <span>{issue}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Suggestions */}
                {op.suggestions.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-emerald-600 mb-1.5">
                      优化建议
                    </p>
                    {op.suggestions.map((sug, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-2 text-sm text-gray-600 mb-1"
                      >
                        <span className="text-emerald-500 mt-0.5">✦</span>
                        <span>{sug}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Reasoning */}
                {op.reasoning && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs font-medium text-gray-500 mb-1">
                      分析过程
                    </p>
                    <p className="text-sm text-gray-600">{op.reasoning}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
