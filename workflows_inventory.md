# 12 个工作流拆解清单

数据来自 `ComfyUI\user\default\workflows\*.json` 的实际节点，不是猜的。

## 一、每个工作流是干什么的

| 文件 | 定位 | 底模 / 关键件 | 采样 | 尺寸 | 备注 |
|---|---|---|---|---|---|
| **主Anima.json** | 通用文生图主力 | anima-base-v1.0 + 3 LoRA | er_sde / beta57 / 30 步 / cfg5 | 1024×1536 或 1536×1024 | 带 UltimateSDUpscale 2×；Raffle 抽标签；39 节点 |
| 主Anima (选择器).json | 同上 + 画师选择 | 同上 + AnimaArtistTagSelectorPlus | 同上 | 同上 | 多一个画师标签选择器 |
| 主Anima_Profile_阳光辣妹校园_v1.json | 固定人设版 | 同上 | 同上 | 同上 | 提示词里写死了角色设定 |
| **图生图.json** | 参考图重绘 | 主Anima 全套 + LoadImage | er_sde / beta57 / 30 步 / **denoise 0.42** | 同上 | 改图、垫图最常用 |
| 图生图尝试.json | 角色/参考条件生成 | anima-incontext-character LoRA + AnimaRefEncode ×2 | er_sde / simple / 30 步 / cfg4 | 1024×1024 | in-context 玩法，无超分 |
| 随机抽奖.json | 快速抽卡 | **anima-turbo-v1.0** + 3 LoRA | er_sde / beta57 / 30 步（randomize） | 1024×1536 | turbo 底模，出图快 |
| **Anima+AIO+生图+超分.json** | 最快 + 细节修复 + 4× | anima_baseV10 + turbo LoRA + aesthetic LoRA | euler_ancestral / simple / **10 步 / cfg1** | 由 ResolutionMaster 决定 | Impact detailer + 4x-AnimeSharp 放大 + WD14 反推 |
| 画师.json | 反向模仿画师风格 | anima-base-v1.0 + context_detailer | dpmpp_3m_sde / beta / **40 步 / cfg4.5** | 1024×1536 / 1536×1024 | 先调 Gemini 反推画师名再抽签 |
| Anima+ToriiGate-0.5无审查反推图生图.json | 本地 VLM 读图 → 图生图 | anima-base-v1.0 + **ToriiGate-0.5 Q5_K_M.gguf** | dpmpp_2m_sde_gpu / beta57 / 40 步 / cfg4.5 | 1200×1800 | 全程本地，不联网 |
| anima_official_base_v1.json | 提示词工厂 | Danbooru 标签检索 + WD14 打标 | 无采样器 | — | 只产标签文本，不出图 |
| sunny_gyaru_baseline_v01.json | SDXL + 参考图风格 | v6.safetensors + **IPAdapter Plus** | euler_ancestral / normal / 28 步 / cfg5.5 | 832×1216 | 唯一非 Anima 的一条 |
| wd14_reference_analysis.json | 单纯打标工具 | WD14 Tagger | — | — | 2 个节点 |

**内容倾向**：`主Anima` 系列和 `随机抽奖` 的 Raffle 节点里挂的是含成人向标签的抽签池，属于 NSFW 版；其余（图生图、AIO、画师、ToriiGate、SDXL）默认提示词是正常向。建议按这个分成两个文件夹，别混在一个列表里翻。

## 二、你实际拥有的「零件库」

### 底模 / 编码器（Anima 一套）

| 角色 | 文件 | 谁在用 |
|---|---|---|
| 主 UNET | `anima-base-v1.0.safetensors` | 主Anima、图生图、画师、ToriiGate |
| 备 UNET | `anima_baseV10.safetensors` | AIO |
| 加速 UNET | `anima-turbo-v1.0.safetensors` | 随机抽奖 |
| 备 UNET | `anima-aesthetic-v1.1.safetensors` | official_base |
| 文本编码 | `qwen_3_06b_base` / `anima_qwen_3_06b_base` | 全部 Anima 流程（type=stable_diffusion） |
| VAE | `qwen_image_vae.safetensors` | 全部 Anima 流程 |

### LoRA 组合（这是你最有价值的部分）

| 组合 | 内容 | 效果 |
|---|---|---|
| **质感三件套** | `anima-base-1-masterpiece-v51` 1.0 → `anima_context_detailer_base10` 0.75 → `anima-highres-aesthetic-boost` 0.5 | 主Anima 的默认味道：干净线条 + 细节 + 高分辨率观感 |
| 快速组合 | `anima-turbo-lora-v0.2` + `anima-highres-aesthetic-boost` | 配 10 步用 |
| 角色参考 | `anima-incontext-character`（0.52 GB） | in-context 图生图 |
| 风格向 | `mixed_styles_anima-base1_v5`、`Chocopizza_Anima`、`MIO-anima-b1_v5`、`Asura_epoch_20` | 换画风 |

### 采样预设（直接抄）

| 场景 | sampler / scheduler / steps / cfg |
|---|---|
| 标准 Anima | `er_sde` / `beta57` / 30 / 5 |
| Turbo 草稿 | `euler_ancestral` / `simple` / 10 / 1 |
| 画师风格 | `dpmpp_3m_sde` / `beta` / 40 / 4.5 |
| 本地 VLM 反推后重绘 | `dpmpp_2m_sde_gpu` / `beta57` / 40 / 4.5 |
| 图生图重绘 | 同标准，denoise 0.42 |

### 放大链

| 用途 | 节点 | 参数 |
|---|---|---|
| 2× 精修 | `UltimateSDUpscale` + `realesrganX4plusAnime_v1.pt` | 2× / 25 步 / cfg5 / er_sde / beta57 / denoise 0.33 / tile 1024 / mask_blur 16 / padding 32 / seam None |
| 纯 4× | `ImageUpscaleWithModel` + `4x-AnimeSharp.pth` | AIO 里用，快但只放大不加细节 |

### 尺寸

1024×1536（竖）、1536×1024（横）、1200×1800（ToriiGate）、832×1216（SDXL）、1024×1024（in-context）

## 三、你说的「说不出来的东西」是什么

| 节点 | 来自 | 作用 |
|---|---|---|
| `Raffle` | ComfyUI-Raffle | 从标签池随机抽一组，抽签出图 |
| `AnimaArtistTagSelectorPlus` / `AnimaMultiLoraLoader` | Comfyui-Anima-Tools | 画师标签选择、LoRA 批量加载 |
| `AnimaRefEncode` / `AnimaRefLatentBatch` / `AnimaInContextApply` | comfyui-anima-incontext | 参考图条件注入（in-context） |
| `ToriiGate_LlamaCppVisionGenerate` | comfyui_toriigate | 本地跑 gguf 视觉模型，读图出提示词 |
| `Gemini_API_S_Zho` | ComfyUI-Gemini | 调 Gemini 反推画师 |
| `DanbooruTagSearch` / `DanbooruRelated` / `SaveText` | ComfyUI-DanbooruSearcher | 搜 Danbooru 标签并存成 txt |
| `WD14Tagger|pysssss` | ComfyUI-WD14-Tagger | 图片反推标签 |
| `WildcardPromptFromString` / `StringListToString` / `DetailerForEach` / `ImpactMakeTileSEGS` | ComfyUI-Impact-Pack | 通配符、列表、分区细化 |
| `ComfySwitchNode` / `ShowText|pysssss` / `easy showAnything` | Easy-Use 类工具包 | 开关分支、显示文本 |
| `ResolutionMaster` | Comfyui-Resolution-Master | 按比例算尺寸 |
| `ConcatTextOfUtils` / `CR Prompt Text` | utils-nodes / Comfyroll | 文本拼接 |

## 四、我的复用情况（实话）

**已复用**（`anima_t2i.json` / `anima_hq.json`）：
- 底模 + 文本编码 + VAE 这套组合
- 质感三件套 LoRA 及你设的强度
- 采样参数、正负提示词模板
- `anima_hq.json` 里把你 `主Anima` 的 2× 超分链（含 tile、denoise 等全部参数）原样搬了进来

**没复用**：
- `Raffle` 抽签、`AnimaArtistTagSelectorPlus`、`ComfySwitchNode` 分支、`ShowText` —— 这些是画布交互逻辑，脚本里用「随机 seed + 自己的标签池」更直接
- Gemini 反推、ToriiGate 反推、Danbooru 搜索、WD14 打标 —— 依赖 API key 或本地 VLM，放在 ComfyUI 里跑更合适
- Impact detailer 分区重绘 —— 能搬，但节点参数多、容易翻车，暂时没做

## 五、建议怎么用

1. 日常出图：画图台「标准」流程（约 60 秒）
2. 要发出去的成图：画图台「2× 超分」流程（约 4 分钟，出 2048×3072）
3. 快速试构图：ComfyUI 里开 `随机抽奖` 或 `AIO`（10 步）
4. 改图/垫图：`图生图`（denoise 0.42）—— 这条我还没做成 API 版，需要的话可以补
5. NSFW 和正常图分两个文件夹，别共用一个列表
