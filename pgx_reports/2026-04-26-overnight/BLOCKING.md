# BLOCKING.md — 架构师起床第一份文件

**架构师，请先读这里再读 EXECUTIVE_SUMMARY.md。**

---

## TL;DR

**当前 GPU/内存被你的另一个项目占满（vLLM serving Qwen3-30B-A3B）**。本夜 5 个核心实验中的 4 个（E-05/E-11/E-03/E-13）所需显存（12–80 GB 不等）**严重超过 free** ≈ 6 GB。我**没有 kill vLLM**，因为：

1. 它在 cwd `/workspace/numara`，是你另一个项目的真实负载（已运行 2.5 天）。
2. 我们在任务开始前明确约定"不动 vLLM"。
3. Kill 一个不可恢复的、不归我管的服务，远远超过我的授权边界。

**这是真正的 BLOCKING 情况**，符合启动文档"硬件资源问题"触发条件。我没有停下来等——我把整夜重排成"vLLM 不让位也能做的事"。但**最贵 / 最有决策价值的实验需要你做选择**。

---

## 你的三个选项（请选一个）

### Option A：vLLM 留着不动（最保守）
**今晚我能产出**：
- ✅ E-16 完整开源工具栈审计（每个工具的 repo / commit / ARM64 状态 / 已知坑 / 安装命令）— **决策价值很高**
- ✅ E-00 数据扩充：Real-ESRGAN 上采样 +（如果 SDXL 装下） LoRA-free IP-Adapter
- ✅ E-07 retopology 纯 CPU 跑通（Instant Meshes + QuadriFlow + 调研）
- ✅ E-08 UniRig **推理**（如果显存够）和**调研报告**（理论部分先写厚）
- ✅ DWpose 姿态提取（用我自录或下载的开源舞蹈视频）作为 E-13 的"输入端"测试
- ✅ 用 **vLLM 的 Qwen3-30B 做 LLM-as-Judge 框架**——这是顺水人情，把 vLLM 变成今晚的实验资源
- ✅ 全套实验自动化脚本（你 kill vLLM 后 `bash run_p1_p4.sh` 就能继续）
- ✅ 完整的 EXECUTIVE_SUMMARY + ARCHITECT_DECISIONS（基于已有信号 + 公开调研）
- ❌ 跑不了：Hunyuan3D / Wan 2.2 / HunyuanVideo / SDXL inference

**你早上的决策密度**：能拿到 Q2（绑骨）+ Q3（数据扩充策略）的初步答案 + 完整工具栈情报；Q1/Q4/Q5 因为 GPU 实际产物缺失，只能从公开资料给"业界声称的状态 + 我的怀疑度"。

### Option B：你起床后 kill vLLM，我接力（推荐）
**步骤**：
```bash
kill -SIGTERM 11230   # 优雅停止 vLLM
# 等 30 秒让它 release 内存
nvidia-smi             # 确认 free ≈ 110 GB
cd /workspace/character-engine/pgx_reports/2026-04-26-overnight
bash run_p1_p4.sh      # 我会写好
```
我整夜会**把所有 P1-P4 的脚本、模型权重下载、数据准备全部做好**，你 kill 后我（或再开一个 Claude session）就能直接跑核心实验。**预计 6-8 小时跑完 E-05 / E-11（Wan 部分） / E-08 / E-13。**

### Option C：你睡前帮我把 vLLM 临时降配
最优的折中。让 vLLM 切到一个 8B 模型（吃 ~16GB）或临时 stop。如果你**现在还醒着**：
```bash
# 这样我今晚就能跑 Hunyuan3D + LoRA 类小尺寸实验
kill -SIGTERM 11230 && sleep 30  # 完全停
# 或者重启 vLLM 切小模型：
# vllm serve Qwen/Qwen2.5-7B-Instruct --gpu-memory-utilization 0.15 ...
```

---

## 当前内存细节（证据）

```
GB10 unified memory: 119.6 GB total
Used:                ~110 GiB
Free:                ~6 GiB

vLLM EngineCore (PID 11230, user=daniel, cwd=/workspace/numara):
  - GPU:  105,688 MiB (~103 GB)
  - 已运行: 2 天 14 小时
  - Serving: qwen3-30b-a3b (max_model_len=8192)
  - API:    http://localhost:8000/v1 active

剩余可用 ≈ 6 GiB — 仅够小工具（Real-ESRGAN small / DWpose / 纯 CPU 任务）
```

---

## 我现在采取的行动（不等你回复）

按 Option A 假设推进。如果你早上选 B/C，我所有的预备工作都直接复用。

**今晚的剩余 8 小时我会做**：

1. **E-16 / ENVIRONMENT.md 完整化**：
   - 每个工具 (Hunyuan3D 2.0, Wan 2.2, UniRig, Instant Meshes, EasyMocap, DWpose, Real-ESRGAN, IP-Adapter, PuLID, Kohya, Diffusion-pipe, Blender) 的 ARM64 兼容性 + 安装命令 + 已知坑
   - 一夜后你拿到一份"哪个工具今天真能装上"的可信清单
2. **预下载所有模型权重**到 HF cache（带宽闲着也是闲着）
3. **写好 P1-P4 的可执行脚本**：vLLM 一停就能 `bash run.sh` 推进
4. **跑能跑的**：
   - E-00 上采样 + 基础数据扩充框架（Real-ESRGAN < 2GB）
   - E-07 retopology（纯 CPU）
   - DWpose 姿态提取（< 3GB）
   - LLM-as-Judge 调用 vLLM Qwen3 做基础评判
5. **把 EXECUTIVE_SUMMARY 和 ARCHITECT_DECISIONS 写成基于"现有信号 + 调研 + 已跑实验"的实在版本**
6. **公开网络调研**：把 Hunyuan3D / Wan 2.2 / UniRig 的最新 arxiv / GitHub issues / 已知用户报告整理进每个 E-XX/details.md，作为"在你 kill vLLM 之前的预判"

---

## 这条 BLOCKING 不是放弃，是诚实

我没有"停下来等你回复"的奢侈——你睡觉。我把今晚分成两层：
- 第一层：**绝对要做的**（不烧 GPU 的所有工作）—— 即使你早上选 A，你也能拿到一份有架构决策价值的报告。
- 第二层：**预备好的**（vLLM 让位后能立刻跑的脚本 + 权重）—— 你早上选 B/C，第二个 session 接力，1 天就能完成核心实验。

**这是我对"独立调查员"角色的最佳解读**：在硬约束下最大化决策价值。

---

**早上见。**
