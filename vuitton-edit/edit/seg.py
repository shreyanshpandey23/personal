"""Person matte with MODNet (ONNX, from Xenova/modnet on Hugging Face)."""
import numpy as np, onnxruntime as ort
from PIL import Image
_S = None
def matte(rgb: np.ndarray, ref: int = 512) -> np.ndarray:
    """rgb uint8 HxWx3 -> float alpha HxW in 0..1"""
    global _S
    if _S is None:
        _S = ort.InferenceSession("/root/models/modnet/onnx/model.onnx", providers=["CPUExecutionProvider"])
    h, w = rgb.shape[:2]
    s = ref / min(h, w)
    nh, nw = max(32, int(round(h * s / 32)) * 32), max(32, int(round(w * s / 32)) * 32)
    x = np.asarray(Image.fromarray(rgb).resize((nw, nh), Image.BILINEAR), np.float32) / 127.5 - 1
    a = _S.run(None, {"input": x.transpose(2, 0, 1)[None]})[0][0, 0]
    return np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32) / 255
