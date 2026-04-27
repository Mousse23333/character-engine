# 动态二次元角色管线架构规格 v0.2

**项目代号**：AI 驱动二次元角色生产管线
**文档定位**：架构规格 v0.2 — 在 v0.1 基础上，吸收 PGX 两轮调研结果 + 业界标准联网调研后的根本性重写
**状态**：架构定型（基于业界已成熟模式），细节待 PGX 验证
**日期**：2026-04-27
**取代**：`PIPELINE_ARCHITECTURE_SPEC.md` (v0.1)

---

## 0. 给读者的提示

本文档是 v0.2 — 它**根本性重写**了 v0.1 的架构。

### 与 v0.1 的核心差异
| 维度 | v0.1 | v0.2 |
|------|------|------|
| 范式 | 7 条独立产线 | **4 层 Tier**（按约束强度分层）|
| AI 边界 | AI 端到端生成整个角色 | **AI 只在槽位内填充，槽位是写死的"客观规律"** |
| 业界传统 | 隐含、未明确借鉴 | **显式吸收**（VRM 1.0 / DAZ Genesis / Modular Avatar / Mixamo / Hunyuan3D Studio）|
| 一致性问题 | 全图 CLIP-I（与人眼对不上）| **分层评判**（契约自动 + 局部 CLIP + LLM-Judge + 人）|
| 装备 | 在线 prompt swap（实测漂走）| **离线槽位资产 + 共享骨骼，在线只组合**|
| Animation | open problem | **Mixamo 库 + VRM 1.0 = 已解决**（仅状态微动用 I2V）|
| 基础假设 | "AI 重新发明一切" | **"传统 = 骨架不动，AI = 血肉按槽位填"** |

### 触发本次重写的关键认知
1. **第二轮 PGX 调研** 测出"装备 prompt swap CLIP-I 0.95 → 0.61-0.75"，证明 AI 端到端会漂
2. **架构师人眼复审** 发现 I2V 实际效果 > Animate-14B、Hunyuan3D mesh "还行" → 旧的"动起来才好"假设错了
3. **"尊重客观规律前提下使用 AI"** 这一原则 → AI 不能自由发明结构，必须在传统拓扑里填充
4. **业界联网调研** 发现 VRM 1.0 / DAZ Genesis / Modular Avatar / Hunyuan3D Studio 已经把这套范式做到成熟

---

## 1. 项目目标（不变）

构建一套**以 AI 为主力生产引擎、以传统渲染为主力消费引擎**的动态二次元 3D 角色管线，
最终支持类似**绝区零 / 原神**视觉品质、**沙盒式可扩展**、**装备 × 状态空间爆炸**、
**实时合成**的角色系统，下游消费者为现有 PIXI 2D 游戏。

---

## 2. 范式（升级版）

### 旧范式（v0.1）
> 架构师 + AI 工人

### 新范式（v0.2）
> **传统 = 骨架（不动） + AI = 血肉（按槽位填） + 架构师 = 定边界与契约**

更精确的表述：
- **传统业界经过几十年沉淀的拓扑结构（骨骼 / 槽位 / UV / 动画语义）是"客观规律"，AI 不应该被允许去重新发明它**
- AI 应该**被严格约束在客观规律的"插槽"里**，只贡献它擅长的（生成多样性 + 美学 + 速度）
- AI 不被允许触犯它做不到的（结构性一致性 + 拓扑稳定性 + 物理正确性）

**结果**：AI 任务从"无界（注定漂）"变成"有界（可成功）"。

---

## 3. 架构铁律（v0.2，整合后）

| ID | 约束 | 含义 |
|----|------|------|
| **AC-0** | **传统骨架 + AI 填血肉**（v0.2 升级为最高原则）| 所有 AI 资产生产必须在 Tier 0 标准约束下进行 |
| **AC-1** | **3D 优先，2D 视频作为可选上层效果** | 主体是 3D（mesh + 骨骼 + 贴图）；I2V 等 2D 视频在最终输出层做微动/风格化（可选） |
| **AC-2** | 沙盒式管线 | 用户/玩家可扩展资产库；管线本身要可被运行时调用 |
| **AC-3** | 装备 × 状态空间爆炸 → **实时组合，不实时生成** | 离线生产槽位资产，在线确定性合成 + 缓存 |
| **AC-4** | 画风与角色解耦 | Style 与 Identity 是两个独立 LoRA 维度 |
| **AC-5** | ~~Animation 是 open problem~~ → **降级**：动作复用 Mixamo 库 + VRM 标准骨骼，仅微动场景用 I2V | open 问题缩小到 NPR shader / Cage Deformer 工程实现 |
| **AC-6** | 全程开源、可控、可改、可替换 | 每个组件必须有开源 fallback；不被任何闭源 SaaS 绑定 |
| **AC-7** | 离线生产 / 在线合成 严格分离 | 两侧只通过 Asset Contract 通讯；离线产物不可变、版本化 |
| **AC-8** ⭐ | **业界标准只采纳，不发明** | Tier 0 直接采用 VRM 1.0 / Mixamo / Modular Avatar 等业界标准，**禁止自创** |

---

## 4. 四层 Tier 架构（核心）

按"**约束强度从硬到软**"分层。下层为上层提供契约，上层不能违反下层。

```
┌─────────────────────────────────────────────────────────┐
│  TIER 0: 业界标准层（只采纳，不发明）                    │
│  约束强度：硬（不可违反）                                │
│  AI 参与：零                                             │
└─────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────┐
│  TIER 1: Base Avatar 层（一次性产出，全项目复用）        │
│  约束强度：硬（一旦产出永远固定）                        │
│  AI 参与：辅助生成（人类最终把关）                       │
└─────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────┐
│  TIER 2: AI 槽位填充层（每件资产一次，AI 主力）          │
│  约束强度：中（必须 conformance check）                  │
│  AI 参与：主力执行                                       │
└─────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────┐
│  TIER 3: 在线合成层（确定性，无 AI）                     │
│  约束强度：软（运行时灵活组合）                          │
│  AI 参与：零（仅在最外层可选 I2V 微动）                  │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Tier 0：业界标准层（具体清单）

这一层**直接采纳业界已有标准**，我们的工作只是查规范、写 schema。

### 5.1 骨骼标准 — VRM 1.0
- **来源**：[vrm-c/vrm-specification](https://github.com/vrm-c/vrm-specification)
- **必需骨骼**（11）：hips, spine, chest, upperChest, neck, head + 上下肢链
- **可选骨骼**（~44）：肩、脚趾、眼、颌、手指（21 段）
- **总骨数**：~55
- **轴向**：Z+ forward
- **初始姿态**：T-pose（强制）
- **优势**：开源标准 / 有 Unity SDK / 有 Three.js loader / VRoid 直接导出 / VRChat 兼容

### 5.2 装备槽位约定（v0.2 草案）
**借鉴**：Modular Avatar (VRChat) + DAZ Genesis 槽位划分

| 槽位 ID | 接合 bone | 互斥规则 | 可叠加层数 |
|---------|-----------|---------|---------|
| `slot.skin` | 全骨骼 | 始终在最底层 | 1 |
| `slot.underwear_top` | chest | — | 1 |
| `slot.underwear_bottom` | hips | — | 1 |
| `slot.top` | chest, upperChest | 覆盖时隐藏 underwear_top | 1 |
| `slot.bottom` | hips, upperLeg | 覆盖时隐藏 underwear_bottom | 1 |
| `slot.dress_full` | chest, hips, legs | 与 top + bottom 互斥 | 1 |
| `slot.outerwear` | chest | 叠加在 top/dress 上 | 1 |
| `slot.gloves` | leftHand, rightHand | — | 1 |
| `slot.shoes` | leftFoot, rightFoot | — | 1 |
| `slot.socks` | leftLowerLeg, rightLowerLeg | shoes 覆盖时部分隐藏 | 1 |
| `slot.hair` | head | — | 1 |
| `slot.headwear` | head | hair 部分隐藏 | 1 |
| `slot.face_accessory` | head | — | 多 |
| `slot.cape` | upperChest | 物理布料 | 1 |
| `slot.weapon_main` | rightHand | — | 1 |
| `slot.weapon_sub` | leftHand | — | 1 |
| `slot.tail` | hips | — | 1 |
| `slot.wings` | upperChest | — | 1 |

**这是项目的"客观规律"清单。AI 必须按这个填，不能创造新槽位。**

### 5.3 UV 布局约定
- 参考 VRoid 标准：多张 1024² PNG，每张对应特定槽位
- 标准 UV map：`body.png`, `face.png`, `hair.png`, `outfit_top.png`, `outfit_bottom.png`, `accessory.png` 等

### 5.4 标准动画库
- **来源**：Mixamo 离线 FBX 库（开源协议允许重分发本地副本）
- 因为所有角色用同一 VRM 1.0 骨骼 → **所有 Mixamo 动画自动适用**
- 复用率：100%

### 5.5 表情参数标准
- ARKit 52 blendshape（业界事实标准）
- 每个 base avatar 必须实现这 52 个 blendshape

### 5.6 渲染管线标准
- PBR 基础材质（roughness / metalness / normal）
- NPR 二次元 shader（参考 HoyoToon / Genshin shader 开源复刻）
- 标准 outline 方法：inverted hull

---

## 6. Tier 1：Base Avatar 层

### 6.1 内容
**1 个标准 base body**（全项目复用）：
- VRM 1.0 标准骨骼绑定（55 骨）
- ~30k 三角面，干净拓扑
- 标准 UV 区域划分（哪个 UV 属于哪个槽位）
- 槽位锚点定义（每个槽位的 attach bone + bbox + 接合圈顶点 ID）
- 默认皮肤纹理 + 默认 ARKit 52 blendshape
- 默认 T-pose

### 6.2 来源选项

**推荐：路线 a — VRoid Studio 改造**
- VRoid Studio 输出**已经是 VRM 1.0**
- 已有标准 blendshape（表情）+ 标准 UV
- 几小时上手 vs 自建 1-2 周
- 完全免费、商用 OK

备选：
- 路线 b：[ToxSam/open-source-avatars](https://github.com/ToxSam/open-source-avatars) 选一个 + 改造
- 路线 c：Hunyuan3D 2.5 生成 base 后做 retop（可控性最高，但工程量大）

### 6.3 改造工作量
1. VRoid 出标准默认 base
2. 标注每个槽位的 anchor 点（bone + bbox + 接合圈顶点 ID）
3. 写成 `base_avatar.json` schema
4. 一次性 1-2 周

---

## 7. Tier 2：AI 槽位填充层（项目核心创新）

### 7.1 核心契约
对每个槽位，AI 生成符合该槽位契约的资产：

```yaml
SlotAssetGenerationRequest:
  slot_spec:
    slot_id: enum<SlotID>          # 来自 Tier 0 槽位清单
    attach_bone: list<BoneName>    # VRM 1.0 骨骼名
    bbox: AABB                     # 包围盒约束
    attach_ring: list<VertexID>    # 与 base 接合的顶点圈
    uv_region: Rect                # 贴图必须落在的 UV 区域
  style_anchor:
    style_lora: <LoRA path>        # 画风 LoRA
    identity_lora: <LoRA path>     # 角色身份 LoRA
  prompt: str                      # 装备描述
  
SlotAssetGenerationResult:
  mesh: <glb path>                 # 槽位 mesh
  texture: <png path>              # 贴图
  bone_weights: <skin weights>     # 绑定到 base 骨骼
  collision_proxy: <simplified>    # 防穿模代理
  conformance_score: float[]       # 各项契约符合度
```

### 7.2 子流程流水线

```
① AI 生成槽位 mesh + 贴图
   工具：Hunyuan3D 2.5（推荐）/ TRELLIS（备选）
   输入约束：prompt + 槽位 bbox（用作 ControlNet hint）
   产出：自由拓扑的 mesh + 贴图
       ↓
② Mesh 配准到 base 骨骼（项目核心研究问题）
   候选方案：
     A) DAZ-style Transfer Utility（推荐 — 业界 14 年验证）
        - 把 base 骨骼权重自动投射到新 mesh
        - 对每个新顶点：找最近 base 顶点 → 复制权重
     C) Cage Mesh Deformer（备选 — 体型变化时用）
        - base mesh 外裹低面 cage
        - 装备绑到 cage，cage 跟随 base 变形
     B) SMPL-X 配准（学术 SOTA，二次元适配性差，暂不用）
       ↓
③ 自动 collision check / 防穿模
   - Shrinkwrap modifier with positive offset
   - Minimum-distance constraint（cloth backstop）
   - Pre-baked collision meshes（capsules / convex 简化体）
       ↓
④ 自动质量评判（多层）
   L1: 几何健康（trimesh：流形 / 自相交 / 面数）
   L2: 槽位 conformance（接合圈对齐 / bbox 不超界）
   L3: 贴图 conformance（贴图落在指定 UV 区域）
   L4: 风格一致性（CLIP-I 在贴图区域，不是整图）
   L5: 美学（Aesthetic Predictor + LLM-as-Judge）
       ↓
⑤ 通过 → 入资产库；不通过 → 重生成
```

### 7.3 关键工具栈（Tier 2）

| 子流程 | 工具 | 开源状态 | 备注 |
|--------|------|---------|------|
| ① mesh 生成 | Hunyuan3D 2.5 | Apache-2.0 | 内置贴图 |
| ① 备选 | TRELLIS | 开源 | 拓扑更细 |
| ② 配准 A | 自实现 / DAZ-style | 自研 | 业界算法成熟 |
| ② 配准 C | 自实现 Cage Deformer | 自研 | Roblox 用此 |
| ③ 防穿模 | Shrinkwrap (Blender) / 自实现 | GPL/自研 | 业界成熟 |
| ④ 评判 L1 | trimesh | MIT | Python 库 |
| ④ 评判 L4 | open_clip | MIT | CLIP-I |
| ④ 评判 L5 | improved-aesthetic-predictor + Qwen3-30B (vLLM) | MIT/Apache | 已部署 |

---

## 8. Tier 3：在线合成层

### 8.1 接口
```
Render(identity, equipment[], state, motion, view) → frame_buffer
```

### 8.2 内部流程
```
1. 加载 Tier 1 base avatar + 共享骨骼
2. 按 equipment[] 加载 slot assets（从资产库）
3. 应用槽位互斥规则（自动 hide 被遮挡 base 部位）
4. 处理 z-order / cage adapt（如果 base body 形态变化）
5. 应用 state modulator（纹理调制 / 局部 blendshape / 显隐）
6. 套用 motion clip（共享骨骼 → 任意 Mixamo 动画自动适用）
7. NPR shader 渲染
8. 视角投影 → 输出
```

### 8.3 业界已有模式
| 业界模式 | 我们怎么用 |
|---------|-----------|
| Unreal Master Pose Component | Three.js 用 SkinnedMesh + 共享 Skeleton 实现 |
| Modular Avatar Object Toggle | 自实现槽位显隐逻辑 |
| VRChat 自动 hide 被遮挡部位 | "互斥规则"按这个实现 |
| VRoid blendshape 自动同步 | state modulator 走 blendshape weights |

### 8.4 微动场景的 I2V（可选）
- 立绘类静态展示场景：3D 渲染出帧 → I2V 加微动（呼吸、表情等）
- 这是 v0.2 新加的 — 第二轮 PGX 调研中架构师人眼发现 I2V 微动效果好

### 8.5 缓存策略
- 缓存 key：`hash(identity, equipment[], state, motion, view)`
- 多级缓存：mesh 组合 / shader 渲染 / 完整帧
- AC-3（实时合成）的真正实现 = **运行时只查缓存 + 边缘合成**

---

## 9. 旧死结的解决映射

| 旧死结（v0.1）| v0.2 解决方案 |
|------------|-------------|
| 装备 prompt swap CLIP-I 漂走（实测 0.95 → 0.61）| 不再用 prompt swap，用槽位资产替换 |
| 新装备需要重新绑骨 | 共享 VRM 1.0 骨骼，绑一次永远不再绑 |
| Animation 是 open problem | Mixamo 离线 FBX 库 + VRM 1.0 标准 = 现成动画库 |
| CLIP-I 评判和人眼对不上 | 拆分为契约 conformance（自动）+ 贴图区域 CLIP-I + LLM-as-Judge |
| 7 条产线散开难管理 | 4 层 Tier，约束自上而下传递 |

---

## 10. 留下的研究问题（按优先级）

### 🔴 高优先级（影响架构可行性）
1. **Hunyuan3D 自由 mesh → 槽位 conformance** — Tier 2 子流程 ② 的核心
2. **Hunyuan3D 2.5 内置绑骨能否产 VRM 1.0 兼容骨骼** — 如果能，Tier 2 ②③ 可省
3. **NPR shader 在 Three.js 上的实现** — 业界都是 Unity / Blender，Web 端要自写或找开源

### 🟡 中优先级（影响工程效率）
4. **Cage Mesh Deformer 在 Three.js 上的实现** — Roblox 不开源
5. **批量生成 Tier 2 槽位资产** 的吞吐量上限
6. **资产库的物理形态**（Git LFS / S3 / 文件系统）

### 🟢 低优先级（细节）
7. 状态 modulator 的具体表示（参数向量 schema）
8. 缓存淘汰策略
9. 沙盒扩展机制（用户提交资产的 review 流程）

---

## 11. 工具栈总览（v0.2，全栈开源）

| Tier | 环节 | 工具 | 开源协议 |
|------|------|------|---------|
| 0 | 骨骼标准 | VRM 1.0 spec | CC0 |
| 0 | 槽位标准 | 借鉴 Modular Avatar | 自定义 schema |
| 0 | UV 标准 | 借鉴 VRoid | 自定义 schema |
| 0 | 动画标准 | Mixamo offline FBX | Adobe 允许本地使用 |
| 0 | 表情标准 | ARKit 52 | Apple 公开规范 |
| 1 | base 生成 | VRoid Studio | 商用免费 |
| 2 ① | mesh 生成 | Hunyuan3D 2.5 | Apache-2.0 |
| 2 ② | 配准 | 自实现 DAZ Transfer + Cage Deformer | 自研 |
| 2 ③ | 防穿模 | Shrinkwrap (Blender) / 自实现 | GPL / 自研 |
| 2 ④ | 评判 L1 | trimesh | MIT |
| 2 ④ | 评判 L4 | open_clip | MIT |
| 2 ④ | 评判 L5 | aesthetic-predictor + Qwen3-30B (vLLM) | MIT / Apache |
| 3 | 渲染 | Three.js + 自写 NPR shader | MIT |
| 3 | 微动可选 | Wan 2.2 I2V | Apache-2.0 |
| 3 | 状态调制 | 自实现 | 自研 |

**全栈无闭源依赖**。

---

## 12. 待 PGX 验证的关键不确定性

下次 PGX 调研最高优先级：

1. **Hunyuan3D 2.5 自带 auto-rig 出的骨骼，能否对齐 VRM 1.0 的 55 骨标准？**
   - 如果能：整个 Tier 2 ②③ 路径大幅简化
   - 如果不能：必须走"DAZ Transfer Utility 自实现"路线

2. **Hunyuan3D 2.5 在二次元角色上的骨骼绑定质量**（以 Alice 为测试角色）

3. **DAZ-style 骨骼权重自动投射** 在二次元 mesh 上的可用性
   - 测试：从 VRoid base 投射到 Hunyuan3D 出的 dress mesh

4. **Cage Mesh Deformer Three.js 实现路径**（学术开源 / 自实现）

5. **NPR shader Three.js 端的 SOTA 开源**

---

## 13. 当前未拍板事项（架构师待决）

1. ✅ 接受 4 层 Tier 架构（待架构师 confirm）
2. ✅ Tier 0 = VRM 1.0 + Modular Avatar 风格槽位 + Mixamo 动画 + ARKit 52 表情（待 confirm）
3. ✅ Tier 1 = VRoid 改造路线（待 confirm）
4. ✅ Tier 2 ② 配准 A 优先 + C 备选（待 confirm）
5. ⏸ 下一轮 PGX 任务详细 brief（等架构 confirm 后写 ADDENDUM 002）

---

## 14. 关于本文档版本管理

- v0.1 (`PIPELINE_ARCHITECTURE_SPEC.md`) — 保留作历史记录，不再更新
- v0.2 (`PIPELINE_ARCHITECTURE_SPEC_v0.2.md`) — 当前活跃文档
- 后续大版本（架构性变更）→ v0.3, v0.4 ...
- 小修改在当前版本内 commit

---

## 15. 参考来源（本次架构修订基于的调研）

### 业界标准
- [VRM 1.0 Humanoid Specification](https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_vrm-1.0/humanoid.md)
- [VRM Features](https://vrm.dev/en/vrm/vrm_features/)
- [Modular Avatar (VRChat 事实标准)](https://modular-avatar.nadena.dev/docs/intro)
- [DAZ Conforming Clothing](https://www.daz3d.com/forums/discussion/55027/workflow-tutorial-conforming-clothes-for-all-genesis-figures)
- [Mixamo Skeleton Standard](https://mocaponline.com/blogs/mocap-news/skeleton-hierarchy-animation-guide)
- [ARKit 52 Blendshapes Guide](https://pooyadeperson.com/the-ultimate-guide-to-creating-arkits-52-facial-blendshapes/)

### 工程模式
- [Unreal Modular Characters](https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-modular-characters-in-unreal-engine)
- [Unreal Master Pose Component](https://forums.unrealengine.com/t/how-to-setup-master-pose-component/318765)
- [Unity Skinned Mesh Renderer](https://docs.unity3d.com/Manual/class-SkinnedMeshRenderer.html)
- [Roblox Cage Mesh Deformer](https://devforum.roblox.com/t/cage-mesh-deformer-studio-beta/1196727)

### AI 工具栈
- [Hunyuan3D Studio Paper (arXiv 2509.12815)](https://arxiv.org/html/2509.12815v1) — 端到端 AI 管线（含绑骨）
- [Hunyuan3D 2.5 Auto-Rig 5 步](https://www.vset3d.com/hunyuan-3d-2-5-create-and-rig-a-3d-character-in-5-steps/)
- [Hunyuan3D-2 GitHub](https://github.com/Tencent-Hunyuan/Hunyuan3D-2)
- [Tripo AI Auto-Rig](https://www.tripo3d.ai/features/ai-auto-rigging)
- [TRELLIS](https://github.com/microsoft/TRELLIS)

### 学术前沿
- [SMPL-X GitHub](https://github.com/vchoutas/smplx)
- [ICON GitHub](https://github.com/YuliangXiu/ICON)
- [ECON GitHub](https://github.com/YuliangXiu/ECON)
- [PoseMaster (arXiv 2506.21076)](https://arxiv.org/pdf/2506.21076)
- [CharacterGen](https://arxiv.org/html/2402.17214v1)
- [Awesome Digital Human](https://github.com/weihaox/awesome-digital-human)

### 项目内部历史
- [v0.1 架构](./PIPELINE_ARCHITECTURE_SPEC.md)
- [PGX 第一轮调研](./pgx_reports/2026-04-26-overnight/EXECUTIVE_SUMMARY.md)
- [PGX 第二轮调研](./pgx_reports/2026-04-27-paradigm-comparison/EXECUTIVE_SUMMARY.md)
- [Task Addendum 001（旧）](./PGX_TASK_ADDENDUM_001.md)

---

**文档结束 · v0.2**

*下一步：架构师 confirm 第 13 节的 4 个待拍板事项，然后撰写 PGX_TASK_ADDENDUM_002.md*
