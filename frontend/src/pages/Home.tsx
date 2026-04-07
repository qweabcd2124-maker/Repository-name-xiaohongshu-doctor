import { useState } from "react";
import { useNavigate } from "react-router-dom";
import UploadZone from "../components/UploadZone";
import CategorySelector from "../components/CategorySelector";

/**
 * 首页 - 笔记上传入口
 */
export default function Home() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("");
  const [category, setCategory] = useState("food");
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [activeTab, setActiveTab] = useState<"text" | "image">("text");

  const canSubmit = title.trim().length > 0;

  const handleSubmit = () => {
    const params = { title, content, tags, category, coverFile };
    navigate("/diagnosing", { state: params });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50">
      {/* Header */}
      <header className="pt-8 pb-4 text-center">
        <div className="inline-flex items-center gap-2 mb-2">
          <span className="text-4xl">💊</span>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-600 to-teal-500 bg-clip-text text-transparent">
            薯医 NoteRx
          </h1>
        </div>
        <p className="text-gray-500 text-lg">你的笔记，值得被看见。</p>
      </header>

      {/* Main Form */}
      <main className="max-w-2xl mx-auto px-4 pb-12">
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          {/* Tab Selector */}
          <div className="flex border-b border-gray-100">
            <button
              onClick={() => setActiveTab("text")}
              className={`flex-1 py-3.5 text-sm font-medium transition-colors ${
                activeTab === "text"
                  ? "text-emerald-600 border-b-2 border-emerald-500 bg-emerald-50/50"
                  : "text-gray-400 hover:text-gray-600"
              }`}
            >
              📝 粘贴文字
            </button>
            <button
              onClick={() => setActiveTab("image")}
              className={`flex-1 py-3.5 text-sm font-medium transition-colors ${
                activeTab === "image"
                  ? "text-emerald-600 border-b-2 border-emerald-500 bg-emerald-50/50"
                  : "text-gray-400 hover:text-gray-600"
              }`}
            >
              📸 上传截图/封面
            </button>
          </div>

          <div className="p-6 space-y-5">
            {/* Category Selector */}
            <CategorySelector value={category} onChange={setCategory} />

            {activeTab === "text" ? (
              <>
                {/* Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    笔记标题 <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="输入你的笔记标题"
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 outline-none transition-all text-gray-800"
                    maxLength={100}
                  />
                  <p className="text-xs text-gray-400 mt-1 text-right">
                    {title.length}/100
                  </p>
                </div>

                {/* Content */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    笔记正文
                  </label>
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="粘贴你的笔记正文（可选）"
                    rows={6}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 outline-none transition-all resize-none text-gray-800"
                  />
                </div>

                {/* Tags */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    标签
                  </label>
                  <input
                    type="text"
                    value={tags}
                    onChange={(e) => setTags(e.target.value)}
                    placeholder="用逗号分隔，如：美食分享,减脂餐,食谱"
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 outline-none transition-all text-gray-800"
                  />
                </div>
              </>
            ) : (
              <>
                {/* Image Upload */}
                <UploadZone onFileSelect={setCoverFile} />
                {/* Still need title for image mode */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    笔记标题 <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="输入你的笔记标题"
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100 outline-none transition-all text-gray-800"
                  />
                </div>
              </>
            )}

            {/* Submit Button */}
            <button
              onClick={handleSubmit}
              disabled={!canSubmit}
              className={`w-full py-3.5 rounded-xl font-semibold text-white text-lg transition-all ${
                canSubmit
                  ? "bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 shadow-md hover:shadow-lg active:scale-[0.98]"
                  : "bg-gray-300 cursor-not-allowed"
              }`}
            >
              🔍 开始诊断
            </button>
          </div>
        </div>

        {/* Feature Highlights */}
        <div className="grid grid-cols-3 gap-3 mt-8">
          {[
            { icon: "🤖", label: "多Agent\n智能诊断" },
            { icon: "📊", label: "真实数据\n量化对比" },
            { icon: "💬", label: "AI模拟\n评论区" },
          ].map((f) => (
            <div
              key={f.label}
              className="bg-white/80 backdrop-blur rounded-xl p-4 text-center border border-gray-100"
            >
              <span className="text-2xl">{f.icon}</span>
              <p className="text-xs text-gray-500 mt-1.5 whitespace-pre-line">
                {f.label}
              </p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
