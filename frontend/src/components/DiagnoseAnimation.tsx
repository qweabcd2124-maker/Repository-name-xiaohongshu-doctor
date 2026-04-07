interface Step {
  label: string;
  icon: string;
  duration: number;
}

interface Props {
  currentStep: number;
  steps: Step[];
}

/**
 * 诊断过程动画 - 模拟"体检"的逐步检查流程
 */
export default function DiagnoseAnimation({ currentStep, steps }: Props) {
  const progress = Math.min(((currentStep + 1) / steps.length) * 100, 100);

  return (
    <div className="space-y-6">
      {/* Pulsing Icon */}
      <div className="flex justify-center">
        <div className="relative">
          <div className="w-20 h-20 rounded-full bg-emerald-100 flex items-center justify-center animate-pulse">
            <span className="text-3xl">
              {steps[currentStep]?.icon ?? "🔍"}
            </span>
          </div>
          <div className="absolute -bottom-1 -right-1 w-7 h-7 bg-emerald-500 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-md">
            {currentStep + 1}
          </div>
        </div>
      </div>

      {/* Current Step Label */}
      <div>
        <p className="text-emerald-700 font-semibold text-lg">
          {steps[currentStep]?.label ?? "处理中..."}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-emerald-400 to-teal-400 rounded-full transition-all duration-700 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Step List */}
      <div className="text-left space-y-1.5 max-h-48 overflow-y-auto">
        {steps.map((step, i) => (
          <div
            key={i}
            className={`flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg transition-all ${
              i < currentStep
                ? "text-emerald-600 bg-emerald-50"
                : i === currentStep
                ? "text-emerald-700 bg-emerald-100 font-medium"
                : "text-gray-300"
            }`}
          >
            <span className="w-5 text-center">
              {i < currentStep ? "✓" : i === currentStep ? step.icon : "○"}
            </span>
            <span>{step.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
