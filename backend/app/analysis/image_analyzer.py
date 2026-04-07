"""
封面图像分析模块
使用 OpenCV 分析封面构图、色彩、人脸检测等特征。
"""
import io
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from PIL import Image


class ImageAnalyzer:
    """分析封面图片的视觉特征"""

    def analyze(self, image_bytes: bytes) -> dict:
        """
        分析图片，返回各项视觉指标。

        @param image_bytes - 原始图片字节数据
        @returns dict 包含 saturation, text_ratio, has_face, brightness 等指标
        """
        img_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(img_pil)

        result = {
            "width": img_pil.width,
            "height": img_pil.height,
            "aspect_ratio": round(img_pil.width / max(img_pil.height, 1), 2),
            "saturation": self._calc_saturation(img_np),
            "brightness": self._calc_brightness(img_np),
            "has_face": self._detect_face(img_np),
            "text_ratio": self._estimate_text_ratio(img_np),
            "dominant_colors": self._get_dominant_colors(img_np),
        }
        return result

    def _calc_saturation(self, img_np: np.ndarray) -> float:
        """计算平均色彩饱和度 (0-1)"""
        if not CV2_AVAILABLE:
            r, g, b = img_np[:,:,0], img_np[:,:,1], img_np[:,:,2]
            max_c = np.maximum(np.maximum(r, g), b).astype(float)
            min_c = np.minimum(np.minimum(r, g), b).astype(float)
            diff = max_c - min_c
            sat = np.where(max_c > 0, diff / max_c, 0)
            return round(float(np.mean(sat)), 3)

        hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
        return round(float(np.mean(hsv[:, :, 1]) / 255.0), 3)

    def _calc_brightness(self, img_np: np.ndarray) -> float:
        """计算平均亮度 (0-1)"""
        gray = np.mean(img_np, axis=2)
        return round(float(np.mean(gray) / 255.0), 3)

    def _detect_face(self, img_np: np.ndarray) -> bool:
        """检测图片中是否有人脸"""
        if not CV2_AVAILABLE:
            return False
        try:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            return len(faces) > 0
        except Exception:
            return False

    def _estimate_text_ratio(self, img_np: np.ndarray) -> float:
        """
        估算封面上文字区域的占比。
        使用边缘检测 + 连通域分析来粗略估计文字区域。
        """
        if not CV2_AVAILABLE:
            return 0.15

        try:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            dilated = cv2.dilate(edges, kernel, iterations=2)
            text_pixels = np.sum(dilated > 0)
            total_pixels = dilated.shape[0] * dilated.shape[1]
            return round(text_pixels / total_pixels, 3)
        except Exception:
            return 0.15

    def _get_dominant_colors(self, img_np: np.ndarray, k: int = 3) -> list[str]:
        """提取主色调（简化实现，取平均色块）"""
        h, w = img_np.shape[:2]
        block_h, block_w = h // 3, w // 3
        colors = []
        for i in range(3):
            row = i * block_h
            col = i * block_w
            block = img_np[row:row+block_h, col:col+block_w]
            avg_color = block.mean(axis=(0, 1)).astype(int)
            hex_color = "#{:02x}{:02x}{:02x}".format(*avg_color)
            colors.append(hex_color)
        return colors
