import { useState, useEffect, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Box, Typography, TextField, Button, Stack, Chip,
  CircularProgress, Alert,
} from "@mui/material";
import HistoryOutlined from "@mui/icons-material/HistoryOutlined";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import CategoryPicker from "../components/CategoryPicker";
import UploadZone from "../components/UploadZone";
import { quickRecognize } from "../utils/api";
import type { QuickRecognizeResult } from "../utils/api";

/** @returns A stable key for a File object */
function fkey(f: File) {
  return `${f.name}_${f.size}_${f.lastModified}`;
}

/** 中文垂类 → 英文 key 映射 */
const CAT_MAP: Record<string, string> = {
  "美食": "food", "穿搭": "fashion", "科技": "tech", "数码": "tech",
  "旅行": "travel", "旅游": "travel", "美妆": "beauty",
  "健身": "fitness", "运动": "fitness",
};

export default function Home() {
  const navigate = useNavigate();

  const [files, setFiles] = useState<File[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("food");

  /** Per-file recognition results and loading state */
  const [aiRecogs, setAiRecogs] = useState<Record<string, QuickRecognizeResult>>({});
  const [aiLoading, setAiLoading] = useState<Record<string, boolean>>({});
  const [aiSuggestion, setAiSuggestion] = useState("");

  /** Track whether user has manually edited each field (suppresses auto-fill & warnings) */
  const [userEdited, setUserEdited] = useState({ title: false, content: false, category: false });

  useEffect(() => { document.title = "薯医 NoteRx"; }, []);

  /** Ctrl+V paste images */
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      const pasted: File[] = [];
      for (const item of items) {
        if (item.type.startsWith("image/") || item.type.startsWith("video/")) {
          const file = item.getAsFile();
          if (file) pasted.push(file);
        }
      }
      if (pasted.length > 0) setFiles((prev) => [...prev, ...pasted].slice(0, 9));
    };
    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, []);

  // ---- Aggregated recognition state (derived) ----

  const anyLoading = useMemo(() => Object.values(aiLoading).some(Boolean), [aiLoading]);
  const allResults = useMemo(() => Object.values(aiRecogs), [aiRecogs]);
  const successResults = useMemo(() => allResults.filter((r) => r.success), [allResults]);

  /** 聚合所有识别结果，从中取最佳 title / content / category */
  const aggregated = useMemo(() => {
    let bestTitle = "";
    let bestContent = "";
    let bestCategory = "";
    let bestSummary = "";

    for (const r of successResults) {
      if (!bestTitle && r.title?.trim()) bestTitle = r.title.trim();
      if (!bestContent && r.content_text?.trim()) bestContent = r.content_text.trim();
      if (!bestCategory && r.category?.trim()) bestCategory = r.category.trim();
      if (!bestSummary && r.summary?.trim()) bestSummary = r.summary.trim();
    }

    return { bestTitle, bestContent, bestCategory, bestSummary };
  }, [successResults]);

  /** 当前文件中需要识别的图片 key 集合 */
  const imageFileKeys = useMemo(
    () => new Set(files.filter((f) => f.type.startsWith("image/")).map(fkey)),
    [files],
  );

  /** 所有图片是否都已完成识别（成功或失败）*/
  const allRecognitionDone = useMemo(() => {
    if (imageFileKeys.size === 0) return false;
    for (const k of imageFileKeys) {
      if (!aiRecogs[k] && !aiLoading[k]) return false;
      if (aiLoading[k]) return false;
    }
    return true;
  }, [imageFileKeys, aiRecogs, aiLoading]);

  // ---- Auto-fill effect: watch aggregated results & fill if user hasn't edited ----

  useEffect(() => {
    const { bestTitle, bestContent, bestCategory, bestSummary } = aggregated;

    if (!userEdited.title) {
      const fillTitle = bestTitle || bestSummary;
      if (fillTitle) setTitle(fillTitle.slice(0, 100));
    }
    if (!userEdited.content && bestContent) {
      setContent(bestContent);
    }
    if (!userEdited.category && bestCategory) {
      const mapped = CAT_MAP[bestCategory];
      if (mapped) setCategory(mapped);
    }
  }, [aggregated, userEdited]);

  /** Did ALL recognitions fail (likely API key issue)? */
  const allFailed = allRecognitionDone && successResults.length === 0 && allResults.length > 0;

  /** Warnings: only for specific fields, only when some recognitions succeeded but a field is missing */
  const showWarnings = allRecognitionDone && files.length > 0 && !allFailed;
  const warnings = useMemo(() => {
    if (!showWarnings) return { title: false, content: false, category: false };
    const { bestTitle, bestContent, bestCategory, bestSummary } = aggregated;
    return {
      title: !bestTitle && !bestSummary,
      content: !bestContent,
      category: !bestCategory,
    };
  }, [showWarnings, aggregated]);

  const autoFilled = useMemo(() => {
    const { bestTitle, bestContent, bestCategory, bestSummary } = aggregated;
    return {
      title: !userEdited.title && !!(bestTitle || bestSummary),
      content: !userEdited.content && !!bestContent,
      category: !userEdited.category && !!bestCategory && !!CAT_MAP[bestCategory],
    };
  }, [aggregated, userEdited]);

  // ---- Recognition trigger ----

  const runRecognition = useCallback(async (file: File) => {
    const key = fkey(file);
    setAiLoading((p) => {
      if (p[key]) return p;
      return { ...p, [key]: true };
    });
    try {
      const res = await quickRecognize(file);
      setAiRecogs((p) => ({ ...p, [key]: res }));
    } catch {
      setAiRecogs((p) => ({ ...p, [key]: { success: false, slot_type: "unknown", category: "", summary: "", error: "识别失败" } }));
    } finally {
      setAiLoading((p) => ({ ...p, [key]: false }));
    }
  }, []);

  /** Update AI suggestion based on current upload state */
  useEffect(() => {
    const imgCount = files.filter((f) => f.type.startsWith("image/")).length;
    const hasVideo = files.some((f) => f.type.startsWith("video/"));
    if (files.length === 0) setAiSuggestion("");
    else if (imgCount === 1 && !hasVideo) setAiSuggestion("建议再上传正文截图或评论区截图，让诊断更全面");
    else if (imgCount === 2) setAiSuggestion("不错！可以继续补充主页截图和评论区截图");
    else if (imgCount >= 3) setAiSuggestion("图片充足，可以直接开始诊断了");
    else if (hasVideo && imgCount === 0) setAiSuggestion("建议再补一张封面截图，提升视觉维度分析效果");
    else setAiSuggestion("");
  }, [files]);

  /** Reset state when all files removed */
  useEffect(() => {
    if (files.length === 0) {
      setAiRecogs({});
      setAiLoading({});
      setUserEdited({ title: false, content: false, category: false });
      setTitle("");
      setContent("");
      setCategory("food");
    }
  }, [files.length]);

  /** Trigger recognition for newly added images (skip already-recognized) */
  const handleFilesChange = useCallback(
    (newFiles: File[]) => {
      setFiles(newFiles);
      for (const f of newFiles) {
        const key = fkey(f);
        if (f.type.startsWith("image/") && !aiRecogs[key]) {
          runRecognition(f);
        }
      }
    },
    [runRecognition, aiRecogs],
  );

  const canSubmit = files.length > 0 && title.trim().length > 0;

  const handleSubmit = () => {
    if (!canSubmit) return;
    navigate("/diagnosing", {
      state: {
        title, content, tags: "", category,
        coverFile: files.find((f) => f.type.startsWith("image/")) ?? null,
        coverImages: files.filter((f) => f.type.startsWith("image/")),
        videoFile: files.find((f) => f.type.startsWith("video/")) ?? null,
      },
    });
  };

  const imageCount = files.filter((f) => f.type.startsWith("image/")).length;
  const guideSteps = ["上传封面", "补充正文", "补充主页", "补充评论区"];
  const currentGuideIndex = Math.min(imageCount, guideSteps.length - 1);

  return (
    <Box
      component={motion.div}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      sx={{ minHeight: "100vh", bgcolor: "#fafafa", display: "flex", flexDirection: "column", alignItems: "center", px: 2, py: { xs: 5, md: 8 } }}
    >
      {/* Header */}
      <Box sx={{ width: "100%", maxWidth: 520, display: "flex", justifyContent: "flex-end", mb: 1 }}>
        <Button
          startIcon={<HistoryOutlined sx={{ fontSize: 16 }} />}
          onClick={() => navigate("/history")}
          sx={{ color: "#999", fontSize: 13, fontWeight: 500, "&:hover": { color: "#262626" } }}
        >
          历史记录
        </Button>
      </Box>

      {/* Brand */}
      <Box sx={{ textAlign: "center", mb: { xs: 3, md: 4 } }}>
        <Box sx={{ display: "inline-flex", alignItems: "center", gap: 1, mb: 0.5 }}>
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect width="28" height="28" rx="7" fill="#ff2442" />
            <text x="14" y="19" textAnchor="middle" fill="#fff" fontSize="13" fontWeight="700" fontFamily="Inter, system-ui, sans-serif">Rx</text>
          </svg>
          <Typography sx={{ fontSize: "1.4rem", fontWeight: 700, color: "#262626" }}>薯医 NoteRx</Typography>
        </Box>
        <Typography sx={{ fontSize: "0.85rem", color: "#999", mt: 0.25 }}>AI 诊断你的小红书笔记</Typography>
      </Box>

      {/* Main card */}
      <Box sx={{ width: "100%", maxWidth: 520, bgcolor: "#fff", border: "1px solid #f0f0f0", borderRadius: "16px", boxShadow: "0 1px 8px rgba(0,0,0,0.04)", overflow: "hidden", p: { xs: 2.5, md: 3 } }}>
        <Stack spacing={2.5}>
          {/* Process guide */}
          <Box sx={{ p: 1.5, borderRadius: "12px", bgcolor: "#fff5f6", border: "1px solid #ffe3e8" }}>
            <Typography sx={{ fontSize: 12, color: "#ff2442", fontWeight: 600, mb: 1 }}>引导流程</Typography>
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75 }}>
              {guideSteps.map((step, idx) => (
                <Chip
                  key={step}
                  size="small"
                  label={step}
                  sx={{
                    bgcolor: idx <= currentGuideIndex ? "#ff2442" : "#fff",
                    color: idx <= currentGuideIndex ? "#fff" : "#999",
                    border: idx <= currentGuideIndex ? "none" : "1px solid #eee",
                    fontSize: 11,
                    fontWeight: idx === currentGuideIndex ? 700 : 500,
                  }}
                />
              ))}
            </Box>
            <Typography sx={{ mt: 1, fontSize: 12, color: "#666" }}>
              当前建议：{guideSteps[currentGuideIndex]}
            </Typography>
          </Box>

          {/* Multi-file upload */}
          <UploadZone files={files} onFilesChange={handleFilesChange} maxFiles={9} />

          {/* AI real-time feedback panel */}
          {(anyLoading || successResults.length > 0 || allFailed || aiSuggestion) && (
            <Box sx={{ p: 2, borderRadius: "12px", bgcolor: allFailed ? "#fffbeb" : "#fafbfc", border: `1px solid ${allFailed ? "#fde68a" : "#f0f0f0"}` }}>
              {anyLoading && (
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: successResults.length > 0 ? 1 : 0 }}>
                  <CircularProgress size={14} sx={{ color: "#ff2442" }} />
                  <Typography sx={{ fontSize: 12, color: "#999" }}>AI 正在识别标题、正文、垂类...</Typography>
                </Box>
              )}
              {allFailed && (
                <Box>
                  <Typography sx={{ fontSize: 12, fontWeight: 600, color: "#92400e", mb: 0.5 }}>
                    AI 识别服务暂时不可用
                  </Typography>
                  <Typography sx={{ fontSize: 12, color: "#a16207", lineHeight: 1.6 }}>
                    可能是 API Key 过期或网络问题。请手动填写标题、正文和垂类后即可正常诊断。
                  </Typography>
                </Box>
              )}
              {successResults.length > 0 && (
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75, mb: aiSuggestion ? 1 : 0 }}>
                  {successResults.map((r, i) => (
                    <Chip
                      key={i}
                      icon={<CheckCircleIcon sx={{ fontSize: 14 }} />}
                      label={r.category ? `${r.category}${r.summary ? ` · ${r.summary.slice(0, 20)}` : ""}` : r.summary?.slice(0, 30)}
                      size="small"
                      sx={{ bgcolor: "#f0fdf4", color: "#16a34a", fontWeight: 500, fontSize: 11, "& .MuiChip-icon": { color: "#16a34a" } }}
                    />
                  ))}
                </Box>
              )}
              {aiSuggestion && !allFailed && (
                <Typography sx={{ fontSize: 12, color: "#666", lineHeight: 1.5 }}>
                  💡 {aiSuggestion}
                </Typography>
              )}
            </Box>
          )}

          {/* Title */}
          <Box>
            <TextField
              label="笔记标题"
              required
              fullWidth
              value={title}
              onChange={(e) => { setTitle(e.target.value); setUserEdited((p) => ({ ...p, title: true })); }}
              placeholder="上传图片后 AI 自动识别，也可手动输入"
              slotProps={{ htmlInput: { maxLength: 100 } }}
              helperText={autoFilled.title ? "✅ AI 已自动识别填充，可自行修改" : `${title.length}/100`}
            />
            {showWarnings && warnings.title && !title.trim() && !userEdited.title && (
              <Alert severity="warning" icon={<WarningAmberIcon fontSize="small" />} sx={{ mt: 0.75, py: 0, fontSize: 12 }}>
                AI 未从图片中识别到笔记标题，请手动输入
              </Alert>
            )}
          </Box>

          {/* Content */}
          <Box>
            <TextField
              label="笔记正文"
              fullWidth
              multiline
              rows={4}
              value={content}
              onChange={(e) => { setContent(e.target.value); setUserEdited((p) => ({ ...p, content: true })); }}
              placeholder="上传图片后 AI 自动提取正文，也可手动输入"
              helperText={autoFilled.content ? "✅ AI 已自动提取正文，可自行修改" : undefined}
            />
            {showWarnings && warnings.content && !content.trim() && !userEdited.content && (
              <Alert severity="warning" icon={<WarningAmberIcon fontSize="small" />} sx={{ mt: 0.75, py: 0, fontSize: 12 }}>
                AI 未从图片中提取到正文内容，建议上传正文截图或手动输入
              </Alert>
            )}
          </Box>

          {/* Category */}
          <Box>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
              <Typography sx={{ fontSize: 13, fontWeight: 500, color: "#999" }}>选择垂类</Typography>
              {autoFilled.category && (
                <Chip label="AI 已自动识别" size="small" sx={{ bgcolor: "#f0fdf4", color: "#16a34a", fontSize: 10, height: 20 }} />
              )}
            </Box>
            <CategoryPicker value={category} onChange={(v) => { setCategory(v); setUserEdited((p) => ({ ...p, category: true })); }} />
            {showWarnings && warnings.category && !userEdited.category && (
              <Alert severity="warning" icon={<WarningAmberIcon fontSize="small" />} sx={{ mt: 0.75, py: 0, fontSize: 12 }}>
                AI 未识别到内容垂类，请手动选择
              </Alert>
            )}
          </Box>

          {/* Submit */}
          <Button
            variant="contained"
            fullWidth
            disabled={!canSubmit}
            onClick={handleSubmit}
            sx={{
              py: 1.4, fontSize: "0.95rem", fontWeight: 600, borderRadius: "12px", height: 48,
              bgcolor: "#ff2442", "&:hover": { bgcolor: "#d91a36" },
              "&.Mui-disabled": { bgcolor: "#f0f0f0", color: "#bbb" },
            }}
          >
            开始诊断
          </Button>
        </Stack>
      </Box>

      <Typography sx={{ mt: 5, fontSize: "0.72rem", color: "#ccc" }}>薯医 NoteRx · AI 诊断仅供参考</Typography>
    </Box>
  );
}
