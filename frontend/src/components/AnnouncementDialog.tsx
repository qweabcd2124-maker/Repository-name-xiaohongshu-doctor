import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  Box,
  Typography,
  Button,
  IconButton,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import FavoriteIcon from "@mui/icons-material/Favorite";
import EmailOutlinedIcon from "@mui/icons-material/EmailOutlined";
import WhatshotIcon from "@mui/icons-material/Whatshot";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import CodeIcon from "@mui/icons-material/Code";

const STORAGE_KEY = "xiaohongshu-doctor_announcement_seen_v1";

const WaveSvg = () => (
  <svg
    viewBox="0 0 600 80"
    preserveAspectRatio="none"
    style={{ position: "absolute", bottom: -1, left: 0, width: "100%", height: 48 }}
  >
    <path d="M0 40 C150 80 350 0 600 40 L600 80 L0 80Z" fill="#fff" />
  </svg>
);

const STATS = [
  {
    icon: <WhatshotIcon sx={{ fontSize: 20, color: "#ff2442" }} />,
    val: "100万+",
    label: "全网曝光",
  },
  {
    icon: <TrendingUpIcon sx={{ fontSize: 20, color: "#ff5c72" }} />,
    val: "10万+",
    label: "日均流量",
  },
  {
    icon: <CodeIcon sx={{ fontSize: 20, color: "#ff8fa3" }} />,
    val: "全开源",
    label: "MIT License",
  },
];

export default function AnnouncementDialog() {
  const [open, setOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  useEffect(() => {
    try {
      if (!localStorage.getItem(STORAGE_KEY)) {
        const timer = setTimeout(() => setOpen(true), 800);
        return () => clearTimeout(timer);
      }
    } catch {
      /* localStorage unavailable */
    }
  }, []);

  const handleClose = () => {
    setOpen(false);
    try {
      localStorage.setItem(STORAGE_KEY, Date.now().toString());
    } catch {
      /* ignore */
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      fullScreen={isMobile}
      slotProps={{
        paper: {
          sx: {
            borderRadius: isMobile ? 0 : "24px",
            overflow: "hidden",
            maxHeight: isMobile ? "100%" : "92vh",
            boxShadow: "0 24px 80px rgba(0,0,0,0.12)",
          },
        },
      }}
    >
      {/* ───── Hero ───── */}
      <Box
        sx={{
          background: "linear-gradient(145deg, #ff2442 0%, #ff5c72 40%, #ff8fa3 100%)",
          px: { xs: 3, sm: 4 },
          pt: { xs: 4, sm: 5 },
          pb: { xs: 5, sm: 6 },
          position: "relative",
          textAlign: "center",
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            position: "absolute", width: 260, height: 260, borderRadius: "50%",
            background: "rgba(255,255,255,0.07)", top: -100, right: -60,
          }}
        />
        <Box
          sx={{
            position: "absolute", width: 160, height: 160, borderRadius: "50%",
            background: "rgba(255,255,255,0.05)", bottom: 10, left: -50,
          }}
        />
        <Box
          sx={{
            position: "absolute", width: 80, height: 80, borderRadius: "50%",
            background: "rgba(255,255,255,0.06)", top: "30%", left: "20%",
          }}
        />
        <WaveSvg />

        <IconButton
          onClick={handleClose}
          size="small"
          sx={{
            position: "absolute", top: 12, right: 12,
            color: "rgba(255,255,255,0.7)",
            backdropFilter: "blur(8px)",
            background: "rgba(255,255,255,0.1)",
            "&:hover": { color: "#fff", background: "rgba(255,255,255,0.2)" },
          }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>

        <Box sx={{ position: "relative", zIndex: 1 }}>
          <Box
            sx={{
              width: 56, height: 56, borderRadius: "16px",
              background: "rgba(255,255,255,0.2)",
              backdropFilter: "blur(12px)",
              display: "flex", alignItems: "center", justifyContent: "center",
              mx: "auto", mb: 2,
            }}
          >
            <FavoriteIcon sx={{ color: "#fff", fontSize: 28 }} />
          </Box>
          <Typography
            sx={{
              color: "#fff", fontWeight: 800,
              fontSize: { xs: "1.35rem", sm: "1.5rem" },
              letterSpacing: "-0.5px", mb: 1,
            }}
          >
            小红薯医生 是公益项目
          </Typography>
          <Typography
            sx={{
              color: "rgba(255,255,255,0.88)",
              fontSize: { xs: "0.85rem", sm: "0.9rem" },
              lineHeight: 1.7, maxWidth: 380, mx: "auto",
            }}
          >
            完全免费 · 完全开源 · 由团队自费运营
          </Typography>
        </Box>
      </Box>

      {/* ───── Content ───── */}
      <DialogContent
        sx={{
          px: { xs: 2.5, sm: 3.5 },
          py: { xs: 2.5, sm: 3 },
          "&::-webkit-scrollbar": { width: 4 },
          "&::-webkit-scrollbar-thumb": { background: "rgba(0,0,0,0.1)", borderRadius: 2 },
        }}
      >
        {/* Stats row */}
        <Box sx={{ display: "flex", gap: { xs: 1, sm: 1.5 }, mb: 2.5 }}>
          {STATS.map((s) => (
            <Box
              key={s.label}
              sx={{
                flex: 1, textAlign: "center",
                py: { xs: 1.2, sm: 1.5 }, px: 0.5,
                borderRadius: "14px", background: "#fff",
                border: "1px solid rgba(0,0,0,0.05)",
                boxShadow: "0 2px 8px rgba(0,0,0,0.03)",
              }}
            >
              <Box sx={{ display: "flex", justifyContent: "center", mb: 0.5 }}>
                {s.icon}
              </Box>
              <Typography
                sx={{
                  fontWeight: 800,
                  fontSize: { xs: "0.95rem", sm: "1.1rem" },
                  color: "#ff2442", lineHeight: 1.3,
                }}
              >
                {s.val}
              </Typography>
              <Typography
                sx={{
                  fontSize: "0.65rem", color: "#aaa", mt: 0.2,
                  fontWeight: 600, letterSpacing: "0.3px",
                }}
              >
                {s.label}
              </Typography>
            </Box>
          ))}
        </Box>
        {/* Contact email */}
        <Box
          sx={{
            display: "flex", alignItems: "center", justifyContent: "center",
            gap: 1, py: 1.2, borderRadius: "12px",
            background: "rgba(255,36,66,0.03)",
            border: "1px solid rgba(255,36,66,0.08)", mb: 3,
          }}
        >
          <EmailOutlinedIcon sx={{ fontSize: 16, color: "#ff6b81" }} />
          <Typography sx={{ fontSize: "0.82rem", color: "#666" }}>
            微信：<strong>kevin88855</strong>　邮箱：<a href="mailto:928766904@qq.com" style={{ color: "#ff2442", fontWeight: 700, textDecoration: "none" }}>928766904@qq.com</a></Typography>
        </Box>

        {/* CTA */}
        <Button
          variant="contained"
          color="primary"
          fullWidth
          size="large"
          onClick={handleClose}
          sx={{
            py: 1.6, fontSize: "0.95rem", fontWeight: 700,
            borderRadius: "14px", textTransform: "none",
          }}
        >
          好的，开始使用 小红薯医生
        </Button>

        <Typography
          sx={{
            textAlign: "center", fontSize: "0.68rem",
            color: "#ccc", mt: 1.5, letterSpacing: "0.3px",
          }}
        >
          此弹窗仅在首次访问时展示
        </Typography>
      </DialogContent>
    </Dialog>
  );
}
