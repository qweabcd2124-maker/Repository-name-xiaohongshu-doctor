import type { SimulatedComment } from "../utils/api";

interface Props {
  comments: SimulatedComment[];
}

const SENTIMENT_STYLES = {
  positive: "bg-emerald-50 border-emerald-200",
  negative: "bg-red-50 border-red-200",
  neutral: "bg-gray-50 border-gray-200",
};

/**
 * AI 模拟评论区
 */
export default function SimulatedComments({ comments }: Props) {
  if (!comments.length) {
    return <p className="text-sm text-gray-400">暂无模拟评论</p>;
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-gray-400">
        以下评论由 AI 模拟生成，预测真实用户可能的反应
      </p>
      {comments.map((c, i) => (
        <div
          key={i}
          className={`flex items-start gap-3 p-3 rounded-xl border ${
            SENTIMENT_STYLES[c.sentiment] || SENTIMENT_STYLES.neutral
          }`}
        >
          <span className="text-2xl shrink-0">{c.avatar_emoji}</span>
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-700">{c.username}</p>
            <p className="text-sm text-gray-600 mt-0.5">{c.comment}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
