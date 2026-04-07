import { useState, useCallback } from "react";

interface Props {
  onFileSelect: (file: File) => void;
}

/**
 * 拖拽/点击上传区域，支持图片预览
 */
export default function UploadZone({ onFileSelect }: Props) {
  const [preview, setPreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.type.startsWith("image/")) return;
      onFileSelect(file);
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(file);
    },
    [onFileSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
        isDragging
          ? "border-emerald-400 bg-emerald-50"
          : "border-gray-200 hover:border-emerald-300 hover:bg-emerald-50/30"
      }`}
    >
      <input
        type="file"
        accept="image/*"
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      {preview ? (
        <div className="space-y-3">
          <img
            src={preview}
            alt="preview"
            className="max-h-48 mx-auto rounded-lg shadow-sm"
          />
          <p className="text-sm text-gray-500">点击或拖拽替换图片</p>
        </div>
      ) : (
        <div className="space-y-2">
          <span className="text-4xl">📷</span>
          <p className="text-gray-500">拖拽图片到此处，或点击上传</p>
          <p className="text-xs text-gray-400">支持 JPG、PNG 格式</p>
        </div>
      )}
    </div>
  );
}
