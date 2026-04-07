interface Props {
  value: string;
  onChange: (v: string) => void;
}

const CATEGORIES = [
  { id: "food", label: "美食", icon: "🍜" },
  { id: "fashion", label: "穿搭", icon: "👗" },
  { id: "tech", label: "科技", icon: "📱" },
];

/**
 * 垂类选择器
 */
export default function CategorySelector({ value, onChange }: Props) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        选择垂类
      </label>
      <div className="grid grid-cols-3 gap-3">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => onChange(cat.id)}
            className={`py-3 px-4 rounded-xl border-2 text-center transition-all ${
              value === cat.id
                ? "border-emerald-500 bg-emerald-50 text-emerald-700 shadow-sm"
                : "border-gray-100 bg-gray-50 text-gray-500 hover:border-gray-200"
            }`}
          >
            <span className="text-2xl block">{cat.icon}</span>
            <span className="text-sm font-medium mt-1 block">{cat.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
