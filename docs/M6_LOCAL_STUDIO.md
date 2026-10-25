# 星夜绘图室：本地工作台

## 启动与停止

1. 用户手动打开 ComfyUI Desktop，等待 8188 可连接。
2. 双击项目根目录 `启动画图台.bat`，或执行：

```powershell
cd E:\AI\Deepseek\comfyui-demo
.\.venv\Scripts\comfy-demo.exe studio
```

3. 打开 `http://127.0.0.1:8199`。

网页只监听本机。关闭网页进程可按 Ctrl+C；这不会关闭 ComfyUI，也不会删除图片。ComfyUI 中已提交任务继续执行，下次启动工作台会从 manifest 恢复状态查询，不重复提交。

## 用法

- 选择 Anima、Animagine、2× 精修、拉琪 img2img 或 in-context。超分需要显式选择 HQ 工作流。
- 输入 prompt，调整尺寸、张数；精细调整中可修改 seed、steps、CFG、denoise 与负面词。
- seed 0 有效，-1 随机；浏览器精确整数最大 9007199254740991，更大 uint64 seed 请使用 CLI。
- img2img/in-context 必须上传参考图。PNG/JPEG/WebP 校验实际内容，不只看扩展名；上限 25MB 和 4000 万像素。
- 参考图由 ComfyUI HTTP 接口写入 Shared input，网页不修改目录权限。multipart 临时文件放在 E 盘 runs/web-temp。
- SSE 显示已提交、排队、运行、完成、失败或取消。当前不显示逐采样步的数字百分比，避免以估计值冒充实际进度。
- 画廊包含 CLI、DSH、Codex 和网页记录，可按角色类型、客户端、失败记录筛选。点击卡片查看原图、绝对路径、错误与 manifest。
- 取消只针对该任务；已终止任务再次取消会返回当前状态。观察超时只标记记录，不擅自中断服务。

## 图片与记录

```text
原图：E:\Comfy-Desktop\ComfyUI-Shared\output\comfyui-demo
记录：E:\AI\Deepseek\comfyui-demo\runs\YYYY\MM\<job-id>.json
截图：E:\AI\Deepseek\comfyui-demo\runs\browser-check
```

历史 DSH 图位于 Shared output 根目录，工作台也能读取其 manifest 引用。没有删除图片的 Web API；失败和未采用图都保留。网页不复制图库，也不下载外部模型或调用付费 API。

## 验收（2026-10-25）

- pytest：30 passed。覆盖配置/注册/manifest/热文件夹/DSH 包，以及 Web schema、Host/请求令牌、图片内容、上传限制（含 chunked）、参考路径边界、SSE、原图路径、离线错误、取消幂等、重启恢复、超时和部分结果保留。
- Ruff：维护代码与测试通过。
- Playwright 使用本机 Chrome headless；1440px 桌面与 390px 手机均通过。工作流选择、筛选、原图弹窗、真实参考图上传、CSRF 拒绝、无横向溢出、reduced motion 和零 JS 错误已验证。
- 真实网页双图任务：`b8a55d3c-7528-4eab-a7c3-74d7e3db99c2`，Anima 标准，512×768、16 步、count=2；实际 seed 为 0 和 1，两张输出分别存在，client=studio，SSE 收到完成状态。
- 最终界面复核截图：`runs/browser-check/28143f5cb297/desktop.png` 和 `mobile.png`。
- 测试框架提示 Starlette 的 httpx TestClient 接口将废弃；当前兼容、全部测试通过，尚未更换测试客户端。

复测：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src tests scripts
.\.venv\Scripts\python.exe scripts/check_studio_browser.py
# 显式运行真实双图测试（会生成并保留两张新图）：
.\.venv\Scripts\python.exe scripts/check_studio_browser.py --generate
```

## 当前边界

M6 已完成本地功能与视觉验收。用户选择先完成本地工作台、公开图片稍后选，因此 M7 个人网站和公开导出本轮不实施。`benchmarks/public-selection.json` 继续为空，`showcase export` 保持锁定。

DSH v0.1.2 已包含 output_prefix 参数并验证官方参数处理路径；UI 重导入仍需下次使用 DSH 时执行。角色生成质量与工程功能分别记录：in-context 有技术成功但视觉不合格的样例，网页明确保留其评分。

## 回滚

停止网页进程即可解除 8199 监听，ComfyUI 与图库不受影响。源码改动按 M6 独立 Git 提交管理；需要回退时使用可审阅的 revert。不要对工作区执行 hard reset，不要删除 runs、Shared output 或旧图目录。
