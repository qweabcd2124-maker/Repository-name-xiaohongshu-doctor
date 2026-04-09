import { useState, useCallback, useEffect, useRef } from "react";
import { Box, Typography, IconButton } from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import CloseIcon from "@mui/icons-material/Close";
import AddPhotoAlternateIcon from "@mui/icons-material/AddPhotoAlternate";
import VideocamOutlinedIcon from "@mui/icons-material/VideocamOutlined";
import { motion, AnimatePresence } from "framer-motion";

interface UploadZoneProps {
  /** Controlled file list from parent */
  files?: File[];
  /** Called whenever the file list changes */
  onFilesChange: (files: File[]) => void;
  /** Max number of files allowed */
  maxFiles?: number;
  /** Desktop compact mode: denser grid and smaller empty state */
  compact?: boolean;
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
/** 与后端 MAX_VIDEO_UPLOAD_MB 默认 300 对齐；更大需在 backend/.env 调高并同步此处 */
const VIDEO_MAX_MB = 300;
const MAX_VIDEO = VIDEO_MAX_MB * 1024 * 1024;

/**
 * 从本地视频文件解码首帧（或小 seek）并生成 JPEG 的 object URL，用于上传区缩略图。
 * @param file - 用户选择的视频文件
 * @returns 指向 JPEG Blob 的 object URL（调用方需在适当时机 revoke）
 */
async function captureVideoFirstFrameAsObjectUrl(file: File): Promise<string> {
  const blobUrl = URL.createObjectURL(file);
  const video = document.createElement("video");
  video.muted = true;
  video.playsInline = true;
  video.setAttribute("playsinline", "true");
  video.preload = "auto";

  return new Promise((resolve, reject) => {
    const teardownVideo = () => {
      video.removeAttribute("src");
      video.load();
    };

    const finishFail = (err: Error) => {
      URL.revokeObjectURL(blobUrl);
      teardownVideo();
      reject(err);
    };

    const drawFrame = () => {
      try {
        const w = video.videoWidth;
        const h = video.videoHeight;
        if (!w || !h) {
          finishFail(new Error("no video dimensions"));
          return;
        }
        const canvas = document.createElement("canvas");
        const maxEdge = 1024;
        let tw = w;
        let th = h;
        if (Math.max(w, h) > maxEdge) {
          const scale = maxEdge / Math.max(w, h);
          tw = Math.round(w * scale);
          th = Math.round(h * scale);
        }
        canvas.width = tw;
        canvas.height = th;
        const ctx = canvas.getContext("2d");
        if (!ctx) {
          finishFail(new Error("no canvas context"));
          return;
        }
        ctx.drawImage(video, 0, 0, tw, th);
        canvas.toBlob(
          (jpeg) => {
            URL.revokeObjectURL(blobUrl);
            teardownVideo();
            if (!jpeg) {
              reject(new Error("toBlob failed"));
              return;
            }
            resolve(URL.createObjectURL(jpeg));
          },
          "image/jpeg",
          0.88,
        );
      } catch (e) {
        finishFail(e instanceof Error ? e : new Error(String(e)));
      }
    };

    const onSeeked = () => {
      video.removeEventListener("seeked", onSeeked);
      drawFrame();
    };

    video.addEventListener("seeked", onSeeked);

    video.onerror = () => finishFail(new Error("video decode error"));

    video.addEventListener(
      "loadeddata",
      () => {
        const d = video.duration;
        const t =
          d && !Number.isNaN(d) && Number.isFinite(d) && d > 0
            ? Math.min(0.08, Math.max(0.001, d * 0.02))
            : 0;
        try {
          video.currentTime = t;
        } catch {
          finishFail(new Error("seek failed"));
        }
      },
      { once: true },
    );

    video.src = blobUrl;
    video.load();
  });
}

/**
 * Multi-file upload zone with grid preview.
 * Supports images and one video. Shows thumbnails in a responsive grid.
 */
export default function UploadZone({
  files = [],
  onFilesChange,
  maxFiles = 9,
  compact = false,
}: UploadZoneProps) {
  const [previews, setPreviews] = useState<Record<string, string>>({});
  /** 视频首帧截取失败时记录 key，回退为摄像机图标 */
  const [videoPosterFailed, setVideoPosterFailed] = useState<Record<string, true>>({});
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  /** 为图片生成 object URL；视频异步截取首帧为 JPEG 缩略图 */
  useEffect(() => {
    const keysNow = new Set(files.map((f) => `${f.name}_${f.size}_${f.lastModified}`));
    let cancelled = false;

    setPreviews((prev) => {
      const next: Record<string, string> = {};
      const toRevoke: string[] = [];
      Object.entries(prev).forEach(([k, url]) => {
        if (!keysNow.has(k)) toRevoke.push(url);
      });
      toRevoke.forEach((u) => URL.revokeObjectURL(u));

      files.forEach((f) => {
        const key = `${f.name}_${f.size}_${f.lastModified}`;
        if (prev[key]) {
          next[key] = prev[key];
        } else if (IMAGE_TYPES.includes(f.type)) {
          next[key] = URL.createObjectURL(f);
        }
      });
      return next;
    });

    setVideoPosterFailed((prev) => {
      const next: Record<string, true> = { ...prev };
      Object.keys(prev).forEach((k) => {
        if (!keysNow.has(k)) delete next[k];
      });
      return next;
    });

    files.forEach((f) => {
      if (!VIDEO_TYPES.includes(f.type)) return;
      const key = `${f.name}_${f.size}_${f.lastModified}`;
      captureVideoFirstFrameAsObjectUrl(f)
        .then((url) => {
          if (cancelled) {
            URL.revokeObjectURL(url);
            return;
          }
          setPreviews((prev) => {
            if (prev[key]) {
              URL.revokeObjectURL(url);
              return prev;
            }
            return { ...prev, [key]: url };
          });
        })
        .catch(() => {
          if (!cancelled) {
            setVideoPosterFailed((p) => ({ ...p, [key]: true }));
          }
        });
    });

    return () => {
      cancelled = true;
    };
  }, [files]);

  const fileKey = (f: File) => `${f.name}_${f.size}_${f.lastModified}`;

  const validateAndAdd = useCallback(
    (incoming: File[]) => {
      setError("");
      const valid: File[] = [];
      for (const f of incoming) {
        const isVideo = VIDEO_TYPES.includes(f.type);
        const isImage = IMAGE_TYPES.includes(f.type);
        if (!isImage && !isVideo) {
          setError("仅支持图片（JPG/PNG/WebP）或视频（MP4/MOV/WebM）");
          continue;
        }
        if (isImage && f.size > MAX_IMAGE) {
          setError(`图片过大（${formatSize(f.size)}），最大 10MB`);
          continue;
        }
        if (isVideo && f.size > MAX_VIDEO) {
          setError(`视频过大（${formatSize(f.size)}），最大 ${VIDEO_MAX_MB}MB`);
          continue;
        }
        if (isVideo && files.some((ex) => VIDEO_TYPES.includes(ex.type))) {
          setError("仅支持上传一个视频");
          continue;
        }
        valid.push(f);
      }
      if (valid.length === 0) return;
      const merged = [...files, ...valid].slice(0, maxFiles);
      onFilesChange(merged);
    },
    [files, maxFiles, onFilesChange],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      validateAndAdd(Array.from(e.dataTransfer.files));
    },
    [validateAndAdd],
  );

  const removeFile = useCallback(
    (idx: number) => {
      const next = files.filter((_, i) => i !== idx);
      onFilesChange(next);
    },
    [files, onFilesChange],
  );

  const hasFiles = files.length > 0;

  return (
    <>
      <Box
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        sx={{
          borderRadius: "14px",
          border: `2px dashed ${isDragging ? "rgba(255, 36, 66, 0.65)" : error ? "#ef4444" : "rgba(0,0,0,0.1)"}`,
          bgcolor: isDragging ? "rgba(255,36,66,0.06)" : "rgba(255,255,255,0.65)",
          backdropFilter: "blur(6px)",
          boxShadow: isDragging
            ? "0 0 0 3px rgba(255,36,66,0.12), inset 0 1px 0 rgba(255,255,255,0.9)"
            : "inset 0 1px 0 rgba(255,255,255,0.85)",
          transition: "border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease",
          overflow: "hidden",
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ALL_ACCEPT}
          multiple
          hidden
          onChange={(e) => {
            if (e.target.files) validateAndAdd(Array.from(e.target.files));
            e.target.value = "";
          }}
        />

        <AnimatePresence mode="wait">
          {hasFiles ? (
            <motion.div
              key="grid"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: compact ? "repeat(4, 1fr)" : "repeat(3, 1fr)",
                  gap: compact ? 0.75 : 1,
                  p: compact ? 1 : 1.5,
                  maxHeight: compact ? 220 : "none",
                  overflowY: compact ? "auto" : "visible",
                }}
              >
                {files.map((f, idx) => {
                  const key = fileKey(f);
                  const isVideo = VIDEO_TYPES.includes(f.type);
                  return (
                    <Box
                      key={key}
                      sx={{
                        position: "relative",
                        aspectRatio: "1",
                        borderRadius: "12px",
                        overflow: "hidden",
                        bgcolor: "#f0f0f2",
                        boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
                        transition: "transform 0.2s ease, box-shadow 0.2s ease",
                        "&:hover": { transform: "scale(1.02)", boxShadow: "0 4px 14px rgba(0,0,0,0.1)" },
                      }}
                    >
                      {isVideo && videoPosterFailed[key] ? (
                        <Box sx={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                          <VideocamOutlinedIcon sx={{ fontSize: 28, color: "#999" }} />
                        </Box>
                      ) : isVideo && previews[key] ? (
                        <Box
                          component="img"
                          src={previews[key]}
                          alt=""
                          sx={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
                        />
                      ) : isVideo ? (
                        <Box sx={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                          <Typography sx={{ fontSize: 11, color: "#999" }}>加载中</Typography>
                        </Box>
                      ) : previews[key] ? (
                        <Box
                          component="img"
                          src={previews[key]}
                          alt={f.name}
                          sx={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
                        />
                      ) : (
                        <Box sx={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                          <Typography sx={{ fontSize: 11, color: "#999" }}>加载中</Typography>
                        </Box>
                      )}
                      <IconButton
                        size="small"
                        aria-label="删除文件"
                        onClick={() => removeFile(idx)}
                        sx={{
                          position: "absolute", top: 2, right: 2,
                          bgcolor: "rgba(0,0,0,0.5)", color: "#fff",
                          width: 24, height: 24, minWidth: 24,
                          padding: 0,
                          "&:hover": { bgcolor: "rgba(0,0,0,0.7)" },
                        }}
                      >
                        <CloseIcon sx={{ fontSize: 14 }} />
                      </IconButton>
                    </Box>
                  );
                })}
                {files.length < maxFiles && (
                  <Box
                    role="button"
                    tabIndex={0}
                    aria-label="添加更多文件"
                    onClick={() => inputRef.current?.click()}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") inputRef.current?.click(); }}
                    sx={{
                      aspectRatio: "1",
                      borderRadius: "12px",
                      border: "1px dashed rgba(255,36,66,0.25)",
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: "pointer",
                      bgcolor: "rgba(255,245,247,0.4)",
                      transition: "all 0.2s ease",
                      "&:hover": {
                        borderColor: "primary.main",
                        bgcolor: "rgba(255,36,66,0.08)",
                        boxShadow: "0 2px 12px rgba(255,36,66,0.12)",
                      },
                      "&:focus-visible": { outline: "2px solid #ff2442", outlineOffset: 2 },
                    }}
                  >
                    <AddPhotoAlternateIcon sx={{ fontSize: 24, color: "#ccc" }} />
                    <Typography sx={{ fontSize: 11, color: "#999", mt: 0.25 }}>
                      {files.length}/{maxFiles}
                    </Typography>
                  </Box>
                )}
              </Box>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                padding: compact ? "24px 16px" : "40px 24px",
                gap: compact ? 6 : 10,
                cursor: "pointer",
              }}
              onClick={() => inputRef.current?.click()}
            >
              <Box sx={{
                width: compact ? 52 : 64,
                height: compact ? 52 : 64,
                borderRadius: compact ? "14px" : "18px",
                background: "linear-gradient(135deg, rgba(255,36,66,0.08) 0%, rgba(255,100,120,0.04) 100%)",
                border: "1.5px solid rgba(255,36,66,0.1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}>
                <CloudUploadIcon sx={{ fontSize: compact ? 26 : 32, color: "#ff2442" }} />
              </Box>
              <Box sx={{ textAlign: "center" }}>
                <Typography sx={{
                  color: "#1a1a1a", fontWeight: 700,
                  fontSize: compact ? 14 : 16,
                  lineHeight: 1.3, mb: 0.5,
                }}>
                  拖入截图开始诊断
                </Typography>
                <Typography sx={{
                  color: "#999",
                  fontSize: compact ? 12 : 13,
                  lineHeight: 1.5,
                }}>
                  支持拖拽 · 点击 · Ctrl+V 粘贴
                </Typography>
                <Typography sx={{
                  color: "#bbb",
                  fontSize: compact ? 11 : 12,
                  mt: 0.25,
                }}>
                  图片最多 {maxFiles} 张 · 视频 1 个
                </Typography>
              </Box>
            </motion.div>
          )}
        </AnimatePresence>
      </Box>

      {error && (
        <Typography role="alert" sx={{ color: "#ef4444", mt: 0.75, fontSize: "0.8rem" }}>
          {error}
        </Typography>
      )}
    </>
  );
}
