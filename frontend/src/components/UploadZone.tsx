import { useState, useCallback, useEffect, useRef } from "react";
import { Box, Typography, IconButton } from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import CloseIcon from "@mui/icons-material/Close";
import VideocamOutlinedIcon from "@mui/icons-material/VideocamOutlined";
import { motion, AnimatePresence } from "framer-motion";

interface UploadZoneProps {
  file?: File | null;
  onFileSelect: (file: File | null) => void;
}

function formatSize(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

const IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];
const VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/webm"];
const ALL_ACCEPT = [...IMAGE_TYPES, ...VIDEO_TYPES].join(",");
const MAX_IMAGE = 10 * 1024 * 1024;
const MAX_VIDEO = 200 * 1024 * 1024;

export default function UploadZone({ file = null, onFileSelect }: UploadZoneProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [fileInfo, setFileInfo] = useState<{ name: string; size: number; isVideo: boolean } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((f: File) => {
    setError("");
    const isVideo = VIDEO_TYPES.includes(f.type);
    const isImage = IMAGE_TYPES.includes(f.type);

    if (!isImage && !isVideo) {
      setError("支持图片（JPG/PNG/WebP）或视频（MP4/MOV/WebM）");
      return;
    }
    if (isImage && f.size > MAX_IMAGE) {
      setError(`图片过大（${formatSize(f.size)}），请控制在 10MB 以内`);
      return;
    }
    if (isVideo && f.size > MAX_VIDEO) {
      setError(`视频过大（${formatSize(f.size)}），请控制在 200MB 以内`);
      return;
    }

    onFileSelect(f);
    setFileInfo({ name: f.name, size: f.size, isVideo });

    if (isImage) {
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(f);
    } else {
      setPreview(null); // video has no inline preview
    }
  }, [onFileSelect]);

  const handleRemove = useCallback(() => {
    setPreview(null);
    setFileInfo(null);
    setError("");
    onFileSelect(null);
    if (inputRef.current) inputRef.current.value = "";
  }, [onFileSelect]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  useEffect(() => {
    if (!file) { setPreview(null); setFileInfo(null); return; }
    const isVideo = VIDEO_TYPES.includes(file.type);
    setFileInfo({ name: file.name, size: file.size, isVideo });
    if (!isVideo) {
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(file);
    } else {
      setPreview(null);
    }
  }, [file]);

  const hasFile = fileInfo !== null;

  return (
    <>
      <Box
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => !hasFile && inputRef.current?.click()}
        sx={{
          borderRadius: "12px",
          border: `2px dashed ${isDragging ? "#ff2442" : error ? "#ef4444" : "#e0e0e0"}`,
          bgcolor: isDragging ? "rgba(255,36,66,0.03)" : "#fff",
          cursor: hasFile ? "default" : "pointer",
          transition: "all 0.2s",
          overflow: "hidden",
          minHeight: 160,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          "&:hover": hasFile ? {} : { borderColor: "#ff2442", bgcolor: "#fafafa" },
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ALL_ACCEPT}
          hidden
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
        />

        <AnimatePresence mode="wait">
          {hasFile ? (
            <motion.div
              key="preview"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              style={{ width: "100%", padding: 20, display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}
            >
              <Box sx={{ position: "relative", display: "inline-block" }}>
                {preview ? (
                  <Box
                    component="img"
                    src={preview}
                    alt="preview"
                    sx={{ maxHeight: 180, maxWidth: "100%", borderRadius: "10px", display: "block" }}
                  />
                ) : (
                  <Box sx={{ width: 120, height: 80, borderRadius: "10px", bgcolor: "#f5f5f5", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <VideocamOutlinedIcon sx={{ fontSize: 32, color: "#bbb" }} />
                  </Box>
                )}
                <IconButton
                  size="small"
                  onClick={(e) => { e.stopPropagation(); handleRemove(); }}
                  sx={{
                    position: "absolute", top: -8, right: -8,
                    bgcolor: "#ff2442", color: "#fff", width: 24, height: 24,
                    "&:hover": { bgcolor: "#d91a36" },
                  }}
                >
                  <CloseIcon sx={{ fontSize: 14 }} />
                </IconButton>
              </Box>
              <Typography sx={{ fontSize: 13, color: "#262626", fontWeight: 500 }}>
                {fileInfo!.name}
                <Typography component="span" sx={{ color: "#999", ml: 1, fontSize: 12 }}>
                  {formatSize(fileInfo!.size)}
                </Typography>
              </Typography>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: 28, gap: 6 }}
            >
              <CloudUploadIcon sx={{ fontSize: 36, color: "#ccc" }} />
              <Typography sx={{ color: "#666", fontWeight: 500, fontSize: "0.85rem", mt: 0.5 }}>
                拖拽、点击或 Ctrl+V 上传
              </Typography>
              <Typography sx={{ color: "#bbb", fontSize: "0.75rem" }}>
                图片（JPG/PNG/WebP，10MB）或视频（MP4/MOV，200MB）
              </Typography>
            </motion.div>
          )}
        </AnimatePresence>
      </Box>

      {error && (
        <Typography sx={{ color: "#ef4444", mt: 0.75, fontSize: "0.8rem" }}>
          {error}
        </Typography>
      )}
    </>
  );
}
