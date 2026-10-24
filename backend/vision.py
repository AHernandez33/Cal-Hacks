from __future__ import annotations
import base64
from typing import Any
import cv2
import numpy as np 

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_DIMENSION = 768
MIN_LEAF_FRACTION = 0.001

class VisionAnalysisError(ValueError):
    """Raised when an image cannot be decoded or analyzed in a reliable manner."""

def resize(image: np.ndarray) -> np.ndarray:
    """Preserve aspect ration while limiting the longest side."""
    height, width = image.shape[:2]
    scale = min(1.0, MAX_IMAGE_DIMENSION / max(height, width))
    if scale == 1.0:
        return image 
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return cv2.resize(image, size, interpolation=cv2.INTER_AREA)

def leaf_mask(hsv: np.ndarray) -> np.ndarray:
    """Find the largest connected green/yellow/brown image region

    HSV rules are intentionally simple: they are NOT a trained segmentation model
    and can mistake background objects for leaves.
    """
    green = cv2.inRange(hsv, (30, 35, 25), (95, 255, 255))
    yellow = cv2.inRange(hsv, (15, 40, 85), (40, 255, 255))
    brown = cv2.inRange(hsv, (5, 35, 25), (25, 255, 200))

    candidates = cv2.bitwise_or(green, cv2.bitwise_or(yellow, brown))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    candidates = cv2.morphologyEx(candidates, cv2.MORPH_OPEN, kernel)
    candidates = cv2.morphologyEx(candidates, cv2.MORPH_CLOSE, kernel, iterations=2)

    count, labels, stats, _ = cv2.connectedComponentsWithStats(candidates, 8)
    if count <= 1:
        raise VisionAnalysisError(
            "No likely leaf found. Use one well-lit leaf against a contrasting background."
        )

    biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    component = np.uint8(labels == biggest) * 255

    # Fill gaps in the outline so discolored regions stay part of the leaf.
    contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(component)
    cv2.drawContours(mask, contours, -1, 255, thickness=cv2.FILLED)

    fraction = float(np.count_nonzero(mask) / mask.size)
    if fraction < MIN_LEAF_FRACTION:
        raise VisionAnalysisError("Detected leaf is too small; move the camera closer.")
    return mask


def analyze_image(image_bytes: bytes) -> dict[str, Any]:
    """Return five leaf features and a PNG heatmap overlay computed locally.

    `mean_hue`: OpenCV hue scale 0–179.
    `texture_variance`: grayscale variance after dividing pixel values by 255.
    `heatmap_data_url`: includes original image pixels; treat as private data.

    Raises VisionAnalysisError for unsupported or uninformative images.
    """
    if not image_bytes:
        raise VisionAnalysisError("The uploaded image is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise VisionAnalysisError("Image exceeds the 8 MiB upload limit.")

    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise VisionAnalysisError("Unable to decode image; use JPEG, PNG, or WebP.")
    image = resize(image)

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mask = leaf_mask(hsv)
    inside = mask > 0
    pixel_count = int(np.count_nonzero(inside))

    # Brown pixels take precedence over yellow, preventing double counting.
    brown_pixels = (cv2.inRange(hsv, (5, 35, 25), (25, 255, 200)) > 0) & inside
    yellow_pixels = (
        (cv2.inRange(hsv, (15, 40, 85), (40, 255, 255)) > 0)
        & inside & ~brown_pixels
    )
    yellow_fraction = float(np.count_nonzero(yellow_pixels) / pixel_count)
    brown_fraction = float(np.count_nonzero(brown_pixels) / pixel_count)
    mean_hue = float(np.mean(hsv[:, :, 0][inside]))
    texture_variance = float(np.var(gray[inside].astype(np.float32) / 255.0))

    # Count edges inside the leaf, excluding its outer border.
    interior = cv2.erode(mask, np.ones((3, 3), np.uint8), iterations=1) > 0
    edges = cv2.Canny(gray, 80, 160) > 0
    edge_density = float(np.count_nonzero(edges & interior) / max(1, np.count_nonzero(interior)))

    # A descriptive, hand-designed discoloration index, NOT disease probability.
    anomaly_score = float(np.clip(0.7 * yellow_fraction + brown_fraction, 0.0, 1.0))

    # Overlay color only around detected yellow/brown regions.
    signal = np.zeros(mask.shape, dtype=np.float32)
    signal[yellow_pixels] = 0.65
    signal[brown_pixels] = 1.0
    smooth_signal = cv2.GaussianBlur(signal, (0, 0), sigmaX=7)
    smooth_signal[~inside] = 0.0
    color_map = cv2.applyColorMap(np.uint8(np.clip(smooth_signal * 255, 0, 255)), cv2.COLORMAP_JET)
    alpha = np.minimum(smooth_signal * 0.8, 0.65)[:, :, None]
    overlay = np.uint8(np.clip(image * (1.0 - alpha) + color_map * alpha, 0, 255))
    success, encoded = cv2.imencode(".png", overlay)
    if not success:
        raise VisionAnalysisError("Unable to encode the visualization.")

    coverage = float(pixel_count / mask.size)
    warnings: list[str] = []
    if coverage > 0.85:
        warnings.append("Most of the frame was classified as leaf; verify the background.")
    if coverage < 0.08:
        warnings.append("Leaf covers little of the frame; a closer photo may help.")

    return {
        "image": {"width": int(image.shape[1]), "height": int(image.shape[0])},
        "features": {
            "yellow_fraction": round(yellow_fraction, 6),
            "brown_fraction": round(brown_fraction, 6),
            "mean_hue": round(mean_hue, 3),
            "texture_variance": round(texture_variance, 6),
            "edge_density": round(edge_density, 6),
        },
        "leaf_coverage_fraction": round(coverage, 6),
        "anomaly_score": round(anomaly_score, 6),
        "heatmap_data_url": "data:image/png;base64," + base64.b64encode(encoded.tobytes()).decode("ascii"),
        "warnings": warnings,
        "disclaimer": (
            "Rule-based visible discoloration only. The heatmap and anomaly "
            "score are not validated plant disease predictions or probabilities."
        ),
    }