import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { diagnoseNote } from "../utils/api";
import { FALLBACK_REPORT } from "../utils/fallback";
import DiagnoseAnimation from "../components/DiagnoseAnimation";

/** 诊断阶段的步骤 */
const STEPS = [
  { label: "解析笔记内容", icon: "📄", duration: 2000 },
  { label: "分析封面视觉", icon: "🎨", duration: 2500 },
  { label: "对比垂类数据", icon: "📊", duration: 2000 },
  { label: "内容Agent诊断中", icon: "📝", duration: 3000 },
  { label: "视觉Agent诊断中", icon: "👁️", duration: 3000 },
  { label: "增长Agent诊断中", icon: "📈", duration: 3000 },
  { label: "用户模拟Agent运行中", icon: "💬", duration: 3000 },
  { label: "Agent辩论交锋", icon: "⚔️", duration: 4000 },
  { label: "综合裁判评定", icon: "⚖️", duration: 3000 },
  { label: "生成诊断报告", icon: "📋", duration: 2000 },
];

/**
 * 诊断过程页 - 展示动画并等待后端返回结果
 */
export default function Diagnosing() {
  const location = useLocation();
  const navigate = useNavigate();
  const params = location.state as {
    title: string;
    content: string;
    tags: string;
    category: string;
    coverFile: File | null;
  } | null;

  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!params) {
      navigate("/");
      return;
    }

    let cancelled = false;

    const runDiagnosis = async () => {
      try {
        const result = await diagnoseNote({
          title: params.title,
          content: params.content,
          category: params.category,
          tags: params.tags,
          coverImage: params.coverFile ?? undefined,
        });
        if (!cancelled) {
          navigate("/report", { state: { report: result, params } });
        }
      } catch (err) {
        console.warn("API 不可用，使用 fallback 数据", err);
        if (!cancelled) {
          navigate("/report", {
            state: { report: FALLBACK_REPORT, params, isFallback: true },
          });
        }
      }
    };

    runDiagnosis();

    // Advance animation steps independently
    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= STEPS.length - 1) {
          clearInterval(timer);
          return prev;
        }
        return prev + 1;
      });
    }, 2800);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  if (!params) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50 flex items-center justify-center">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
          <DiagnoseAnimation currentStep={currentStep} steps={STEPS} />

          <div className="mt-6">
            <p className="text-sm text-gray-400">正在诊断</p>
            <p className="font-semibold text-gray-700 mt-1 truncate px-4">
              「{params.title}」
            </p>
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-50 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
