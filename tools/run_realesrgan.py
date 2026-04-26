#!/usr/bin/env python3
"""E-00: Real-ESRGAN x4 upsample alice_ref.jpeg → 756x1068.

ai-forever/Real-ESRGAN ships a flat state_dict (no 'params' key) — load directly.
"""
import torch, os, time, sys
from PIL import Image
import numpy as np
from pathlib import Path

REPORT = Path("/workspace/character-engine/pgx_reports/2026-04-26-overnight/E-00-data-augmentation")
SAMPLES = REPORT / "samples"
LOGS = REPORT / "logs"
SAMPLES.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

src = Path("/workspace/character-engine/test_assets/test_character_alice_ref.jpeg")
img = Image.open(src).convert("RGB")
print(f"input: {src.name}  size={img.size}  mode={img.mode}")
img.save(SAMPLES / "00_original_189x267.png")

img_bicubic = img.resize((756, 1068), Image.BICUBIC)
img_bicubic.save(SAMPLES / "01_bicubic_x4.png")

# RRDBNet from ai-forever/Real-ESRGAN format (rdb1/rdb2/rdb3 lowercase)
class RRDB(torch.nn.Module):
    def __init__(self, nf=64, gc=32):
        super().__init__()
        self.rdb1 = self._dense(nf, gc)
        self.rdb2 = self._dense(nf, gc)
        self.rdb3 = self._dense(nf, gc)
    def _dense(self, nf, gc):
        m = torch.nn.Module()
        m.conv1 = torch.nn.Conv2d(nf, gc, 3, 1, 1)
        m.conv2 = torch.nn.Conv2d(nf+gc, gc, 3, 1, 1)
        m.conv3 = torch.nn.Conv2d(nf+2*gc, gc, 3, 1, 1)
        m.conv4 = torch.nn.Conv2d(nf+3*gc, gc, 3, 1, 1)
        m.conv5 = torch.nn.Conv2d(nf+4*gc, nf, 3, 1, 1)
        m.lrelu = torch.nn.LeakyReLU(0.2, inplace=True)
        def fwd(x):
            x1 = m.lrelu(m.conv1(x))
            x2 = m.lrelu(m.conv2(torch.cat([x, x1], 1)))
            x3 = m.lrelu(m.conv3(torch.cat([x, x1, x2], 1)))
            x4 = m.lrelu(m.conv4(torch.cat([x, x1, x2, x3], 1)))
            x5 = m.conv5(torch.cat([x, x1, x2, x3, x4], 1))
            return x5 * 0.2 + x
        m.forward = fwd
        return m
    def forward(self, x):
        out = self.rdb1(x)
        out = self.rdb2(out)
        out = self.rdb3(out)
        return out * 0.2 + x

class RRDBNet(torch.nn.Module):
    def __init__(self, in_ch=3, out_ch=3, nf=64, nb=23, gc=32, scale=4):
        super().__init__()
        self.scale = scale
        self.conv_first = torch.nn.Conv2d(in_ch, nf, 3, 1, 1)
        self.body = torch.nn.Sequential(*[RRDB(nf, gc) for _ in range(nb)])
        self.conv_body = torch.nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_up1 = torch.nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_up2 = torch.nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_hr = torch.nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_last = torch.nn.Conv2d(nf, out_ch, 3, 1, 1)
        self.lrelu = torch.nn.LeakyReLU(0.2, inplace=True)
    def forward(self, x):
        feat = self.conv_first(x)
        body_feat = self.conv_body(self.body(feat))
        feat = feat + body_feat
        feat = self.lrelu(self.conv_up1(torch.nn.functional.interpolate(feat, scale_factor=2, mode='nearest')))
        feat = self.lrelu(self.conv_up2(torch.nn.functional.interpolate(feat, scale_factor=2, mode='nearest')))
        out = self.conv_last(self.lrelu(self.conv_hr(feat)))
        return out

dev = torch.device("cuda")
model_path = "/home/daniel/.cache/huggingface/hub/models--ai-forever--Real-ESRGAN/snapshots/8110204ebf8d25c031b66c26c2d1098aa831157e/RealESRGAN_x4.pth"
sd = torch.load(model_path, map_location='cpu', weights_only=True)
print(f"weight file: {len(sd)} keys")

model = RRDBNet(scale=4).to(dev).eval()
missing, unexpected = model.load_state_dict(sd, strict=False)
print(f"missing keys: {len(missing)} | unexpected: {len(unexpected)}")
if len(missing) < 5: print(f"  missing: {missing}")
if len(unexpected) < 5: print(f"  unexpected: {unexpected}")

# convert
arr = np.array(img).astype(np.float32) / 255.0
inp = torch.from_numpy(arr).permute(2,0,1).unsqueeze(0).to(dev)
print(f"input tensor: {inp.shape}")

t0 = time.time()
with torch.no_grad(), torch.amp.autocast(device_type='cuda', dtype=torch.float16):
    out = model(inp)
torch.cuda.synchronize()
print(f"inference: {time.time()-t0:.2f}s  out={out.shape}  peak GPU={torch.cuda.max_memory_allocated()/1e9:.2f}GB")

out = out.clamp(0, 1).squeeze(0).permute(1,2,0).float().cpu().numpy()
out = (out * 255.0).astype(np.uint8)
Image.fromarray(out).save(SAMPLES / "02_realesrgan_x4_756x1068.png")
print(f"saved: {SAMPLES / '02_realesrgan_x4_756x1068.png'}")

# side-by-side
sxs = Image.new("RGB", (756*2 + 20, 1068), (50,50,50))
sxs.paste(img_bicubic, (0,0))
sxs.paste(Image.fromarray(out), (776,0))
sxs.save(SAMPLES / "03_compare_bicubic_vs_esrgan.png")
print("compare saved")

# basic objective metrics: gradient strength as proxy for sharpness
def grad_strength(img_np):
    g = np.array(img_np.convert('L'), dtype=np.float32)
    gx = np.diff(g, axis=1); gy = np.diff(g, axis=0)
    return float(np.sqrt(gx[:-1,:]**2 + gy[:,:-1]**2).mean())

g_orig = grad_strength(img)
g_bic  = grad_strength(img_bicubic)
g_esr  = grad_strength(Image.fromarray(out))
print(f"gradient strength | orig: {g_orig:.2f}  bicubic: {g_bic:.2f}  esrgan: {g_esr:.2f}")
