import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Stack,
  Chip,
  CircularProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import DeleteIcon from "@mui/icons-material/Delete";
import HistoryIcon from "@mui/icons-material/History";
import {
  getHistoryList,
  getHistoryDetail,
  deleteHistory,
} from "../utils/api";
import type { HistoryListItem } from "../utils/api";

const CATEGORY_LABEL: Record<string, string> = {
  food: "美食",
  fashion: "时尚",
  tech: "科技",
  travel: "旅行",
  beauty: "美妆",
  fitness: "健身",
  life: "生活",
};

const GRADE_COLOR: Record<string, string> = {
  S: "#10b981",
  A: "#14b8a6",
  B: "#3b82f6",
  C: "#f59e0b",
  D: "#ef4444",
};

/**
 * 历史记录页
 */
export default function History() {
  const navigate = useNavigate();
  const [items, setItems] = useState<HistoryListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [navigating, setNavigating] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<HistoryListItem | null>(null);

  const fetchList = async () => {
    setLoading(true);
    try {
      const list = await getHistoryList(50);
      setItems(list);
    } catch (e) {
      console.error("获取历史记录失败", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchList();
  }, []);

  /** 点击卡片：加载完整报告后跳转 Report 页 */
  const handleOpen = async (item: HistoryListItem) => {
    setNavigating(item.id);
    try {
      const detail = await getHistoryDetail(item.id);
      navigate("/report", {
        state: {
          report: detail.report,
          params: { title: detail.title, category: detail.category },
          isFallback: false,
        },
      });
    } catch (e) {
      console.error("获取报告详情失败", e);
      setNavigating(null);
    }
  };

  /** 确认删除 */
  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteHistory(deleteTarget.id);
      setItems((prev) => prev.filter((i) => i.id !== deleteTarget.id));
    } catch (e) {
      console.error("删除失败", e);
    }
    setDeleteTarget(null);
  };

  const formatTime = (ts: string) => {
    if (!ts) return "";
    const d = new Date(ts.includes("T") ? ts : ts.replace(" ", "T"));
    return d.toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background:
          "linear-gradient(160deg, #ecfdf5 0%, #ffffff 50%, #f0fdfa 100%)",
        pb: 10,
      }}
    >
      {/* 顶栏 */}
      <Box
        sx={{
          position: "sticky",
          top: 0,
          zIndex: 10,
          bgcolor: "rgba(255,255,255,0.85)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid",
          borderColor: "divider",
        }}
      >
        <Box
          sx={{
            maxWidth: 720,
            mx: "auto",
            px: 2,
            py: 1.5,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate("/")}
            size="small"
            color="inherit"
          >
            首页
          </Button>
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <HistoryIcon color="primary" />
            <Typography sx={{ fontWeight: 700 }} color="primary">
              诊断历史
            </Typography>
          </Box>
          <Box sx={{ width: 64 }} />
        </Box>
      </Box>

      <Box sx={{ maxWidth: 720, mx: "auto", px: 2, mt: 3 }}>
        {loading ? (
          <Box sx={{ textAlign: "center", py: 10 }}>
            <CircularProgress color="primary" />
            <Typography color="text.secondary" sx={{ mt: 2 }}>
              加载中...
            </Typography>
          </Box>
        ) : items.length === 0 ? (
          <Box sx={{ textAlign: "center", py: 10 }}>
            <Typography fontSize={48}>📋</Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              暂无诊断记录
            </Typography>
            <Button
              variant="contained"
              sx={{ mt: 3 }}
              onClick={() => navigate("/")}
            >
              去诊断一篇笔记
            </Button>
          </Box>
        ) : (
          <Stack spacing={2}>
            {items.map((item) => (
              <Card key={item.id} sx={{ position: "relative" }}>
                <CardActionArea
                  onClick={() => handleOpen(item)}
                  disabled={navigating === item.id}
                >
                  <CardContent
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 2,
                      pr: 7,
                    }}
                  >
                    {/* 评分圆 */}
                    <Box
                      sx={{
                        width: 56,
                        height: 56,
                        borderRadius: "50%",
                        flexShrink: 0,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        background: `linear-gradient(135deg, ${GRADE_COLOR[item.grade] || "#999"}22, ${GRADE_COLOR[item.grade] || "#999"}11)`,
                        border: `2px solid ${GRADE_COLOR[item.grade] || "#ccc"}`,
                      }}
                    >
                      <Typography
                        sx={{
                          fontWeight: 800,
                          fontSize: 18,
                          color: GRADE_COLOR[item.grade] || "#666",
                          lineHeight: 1,
                        }}
                      >
                        {Math.round(item.overall_score)}
                      </Typography>
                      <Typography
                        sx={{
                          fontSize: 11,
                          fontWeight: 700,
                          color: GRADE_COLOR[item.grade] || "#666",
                          lineHeight: 1,
                          mt: 0.2,
                        }}
                      >
                        {item.grade}
                      </Typography>
                    </Box>

                    {/* 文本区 */}
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography
                        variant="subtitle1"
                        fontWeight={600}
                        sx={{
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {item.title}
                      </Typography>
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 1,
                          mt: 0.5,
                        }}
                      >
                        <Chip
                          label={
                            CATEGORY_LABEL[item.category] || item.category
                          }
                          size="small"
                          variant="outlined"
                          sx={{ height: 22, fontSize: 12 }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {formatTime(item.created_at)}
                        </Typography>
                      </Box>
                    </Box>

                    {navigating === item.id && (
                      <CircularProgress size={20} sx={{ ml: 1 }} />
                    )}
                  </CardContent>
                </CardActionArea>

                {/* 删除按钮 */}
                <IconButton
                  size="small"
                  sx={{
                    position: "absolute",
                    right: 8,
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "text.disabled",
                    "&:hover": { color: "error.main" },
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteTarget(item);
                  }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Card>
            ))}
          </Stack>
        )}
      </Box>

      {/* 删除确认对话框 */}
      <Dialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
      >
        <DialogTitle>删除记录</DialogTitle>
        <DialogContent>
          <DialogContentText>
            确定删除「{deleteTarget?.title}」的诊断记录吗？此操作不可恢复。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>取消</Button>
          <Button onClick={handleDelete} color="error">
            删除
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
