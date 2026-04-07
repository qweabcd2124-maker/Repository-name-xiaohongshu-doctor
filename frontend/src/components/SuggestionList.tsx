interface Suggestion {
  priority: number;
  description: string;
  expected_impact: string;
}

interface Props {
  suggestions: Suggestion[];
}

const PRIORITY_BADGES = [
  { bg: "bg-red-100 text-red-700", label: "最优先" },
  { bg: "bg-amber-100 text-amber-700", label: "重要" },
  { bg: "bg-blue-100 text-blue-700", label: "建议" },
];

/**
 * 优化建议列表（按优先级排序）
 */
export default function SuggestionList({ suggestions }: Props) {
  if (!suggestions.length) {
    return <p className="text-sm text-gray-400">暂无优化建议</p>;
  }

  const sorted = [...suggestions].sort((a, b) => a.priority - b.priority);

  return (
    <div className="space-y-3">
      {sorted.map((s, i) => {
        const badge = PRIORITY_BADGES[Math.min(i, PRIORITY_BADGES.length - 1)];
        return (
          <div
            key={i}
            className="flex items-start gap-3 p-4 bg-gray-50 rounded-xl"
          >
            <span
              className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${badge.bg}`}
            >
              {badge.label}
            </span>
            <div className="min-w-0">
              <p className="text-sm text-gray-800">{s.description}</p>
              {s.expected_impact && (
                <p className="text-xs text-emerald-600 mt-1">
                  📈 {s.expected_impact}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
