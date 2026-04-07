interface Props {
  score: number;
  grade: string;
  title: string;
}

const GRADE_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  S: { bg: "from-amber-400 to-orange-500", text: "text-white", label: "爆款潜力" },
  A: { bg: "from-emerald-400 to-teal-500", text: "text-white", label: "表现优秀" },
  B: { bg: "from-blue-400 to-indigo-500", text: "text-white", label: "中规中矩" },
  C: { bg: "from-orange-400 to-red-400", text: "text-white", label: "需要优化" },
  D: { bg: "from-red-500 to-rose-600", text: "text-white", label: "问题严重" },
};

/**
 * 综合评分卡片
 */
export default function ScoreCard({ score, grade, title }: Props) {
  const style = GRADE_STYLES[grade] || GRADE_STYLES.B;

  return (
    <div
      className={`bg-gradient-to-br ${style.bg} rounded-2xl p-6 ${style.text} shadow-lg`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-white/80 text-sm">诊断笔记</p>
          <p className="font-semibold text-lg mt-0.5 line-clamp-1">
            「{title}」
          </p>
        </div>
        <div className="text-right">
          <div className="text-5xl font-bold">{Math.round(score)}</div>
          <p className="text-white/80 text-sm mt-0.5">/ 100</p>
        </div>
      </div>

      <div className="mt-4 flex items-center gap-3">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-white/20 rounded-full text-sm font-medium backdrop-blur">
          <span className="text-lg">{grade}</span>
          <span>级</span>
        </span>
        <span className="text-white/90 text-sm">{style.label}</span>
      </div>
    </div>
  );
}
