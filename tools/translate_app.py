# -*- coding: utf-8 -*-
"""
Script to translate Chinese in app.py to English.
"""
import re

def translate_app():
    with open('app.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # 1. Module docstring
    module_doc_old = '''"""muse2api — 把 Muse(muse.ai) 网页免费账号的对话/生图/生视频额度反代成 API。

OpenAI 兼容:
  POST /v1/chat/completions          （文本 / 代码对话，支持 stream，可接 Codex）
  POST /v1/images/generations
  POST /v1/videos  +  GET /v1/videos/{task_id}
  GET  /v1/models
  GET  /v1/media/{name}

管理（前端账号池管理页面在 GET /）:
  GET    /admin/status
  GET    /admin/accounts
  POST   /admin/accounts            （单条 / 批量文本 / 批量数组）
  PATCH  /admin/accounts/{id}       （改标签、启用/禁用）
  DELETE /admin/accounts/{id}
  POST   /admin/accounts/{id}/test  （真实打开 muse.ai 验证会话是否有效）
  POST   /admin/accounts/{id}/relogin
  GET    /admin/tasks               （任务记录）
  DELETE /admin/tasks/{id}  |  POST /admin/tasks/clear
  GET    /admin/media  |  POST /admin/media/delete  |  DELETE /admin/media/{name}
  GET    /admin/extension           （浏览器扩展 zip，用来取 cookie）
  GET    /admin/cookie-helper       （命令行取 cookie 脚本，进阶）
"""'''

    module_doc_new = '''"""muse2api — Reverse proxy Muse (muse.ai) free web chat/image/video quotas into OpenAI-compatible APIs.

OpenAI Compatible:
  POST /v1/chat/completions          (Text / code chat, supports stream, Codex compatible)
  POST /v1/images/generations
  POST /v1/videos  +  GET /v1/videos/{task_id}
  GET  /v1/models
  GET  /v1/media/{name}

Management (Dashboard at GET /):
  GET    /admin/status
  GET    /admin/accounts
  POST   /admin/accounts            (Single / batch text / batch array)
  PATCH  /admin/accounts/{id}       (Update label, enable/disable)
  DELETE /admin/accounts/{id}
  POST   /admin/accounts/{id}/test  (Verify session validity against muse.ai)
  POST   /admin/accounts/{id}/relogin
  GET    /admin/tasks               (Task history)
  DELETE /admin/tasks/{id}  |  POST /admin/tasks/clear
  GET    /admin/media  |  POST /admin/media/delete  |  DELETE /admin/media/{name}
  GET    /admin/extension           (Browser extension zip for importing cookies)
  GET    /admin/cookie-helper       (CLI cookie extraction script, advanced)
"""'''

    c = c.replace(module_doc_old, module_doc_new)

    subs = [
        ("# 允许跨域调用：方便从 chrome-extension:// 导入、以及跨域反代接入",
         "# CORS: allow import from chrome-extension:// and cross-origin clients"),
        ("Field(default=None, description=\"请求唯一标识，留空则由服务端自动生成\")",
         "Field(default=None, description=\"Unique request ID, generated if omitted\")"),
        ("Field(default=None, description=\"关联的业务会话 ID，留空由服务端生成\")",
         "Field(default=None, description=\"Associated conversation ID, generated if omitted\")"),
        ("Field(description=\"提示词内容，描述希望生成的视频画面\")",
         "Field(description=\"Prompt describing the desired video\")"),
        ("Field(default=\"16:9\", description=\"视频宽高比，支持 '16:9'、'9:16'、'1:1'\")",
         "Field(default=\"16:9\", description=\"Aspect ratio, supports '16:9', '9:16', '1:1'\")"),
        ("Field(default=5, ge=1, le=30, description=\"视频时长（秒），支持 1–30 秒\")",
         "Field(default=5, ge=1, le=30, description=\"Video duration in seconds, 1-30\")"),
        ("Field(default=None, description=\"参考图片（支持 http/https URL、或 data:image/...;base64,... 字符串），用于图生视频\")",
         "Field(default=None, description=\"Reference image (http/https URL or base64 data URI) for image-to-video\")"),
        ("Field(default=None, description=\"画质规格，可选 '720p'、'1080p'、'original' 等\")",
         "Field(default=None, description=\"Resolution, e.g. '720p', '1080p', 'original'\")"),
        ("Field(default=None, description=\"指定要使用的账号 ID，留空则由账号池自动调度\")",
         "Field(default=None, description=\"Designated account ID, auto-scheduled if omitted\")"),
        ("Field(default=None, description=\"任务整体超时秒数，默认 600\")",
         "Field(default=None, description=\"Overall task timeout in seconds, default 600\")"),

        # Tool protocol
        ('''_TOOL_PROTOCOL_HEAD = """你可以根据需要调用以下工具来协助用户完成任务。
若需调用工具，请直接输出如下格式的 JSON 代码块（不要包含其他多余解释）：
```json
{"name": "<工具名>", "arguments": {<参数>}}
```
如果需要调用多个工具，请输出包含多个对象的 JSON 数组。
如果无需调用工具，请直接用自然语言回答。

可用工具列表：
"""''',
         '''_TOOL_PROTOCOL_HEAD = """You can call the following tools as needed to assist the user.
If you need to call a tool, output a JSON code block in the following format (without extra explanations):
```json
{"name": "<tool_name>", "arguments": {<arguments>}}
```
If multiple tools are needed, output a JSON array of objects.
If no tool call is needed, reply directly in natural language.

Available tools:
"""'''),
        ('"""把 JSON Schema 的参数描述成易读的多行文本。"""',
         '"""Format JSON Schema parameters into readable multiline text."""'),
        ('return "      （无参数）"', 'return "      (No parameters)"'),
        ('"必填" if name in required else "可选"', '"required" if name in required else "optional"'),
        ('"""把 tools 定义翻译成提示词片段（没有工具时返回空串）。\n\n    同时兼容 Chat Completions 的 `{"type":"function","function":{...}}`\n    和 Responses API 的 `{"type":"function","name":...,"parameters":...}`。\n    """',
         '"""Convert tools definitions into prompt snippet (returns empty string if none).\n    Compatible with Chat Completions and Responses API formats.\n    """'),
        ('items.append("%d. %s%s\\n   参数：\\n%s" % (', 'items.append("%d. %s%s\\n   Parameters:\\n%s" % ('),
        ('"""把解析出的 JSON 转成 OpenAI tool_calls；不像工具调用就返回 None。"""',
         '"""Convert parsed JSON into OpenAI tool_calls; returns None if not a tool call."""'),
        ('"""从模型输出里抽出工具调用。\n\n    返回 (tool_calls, 剩余文本)；抽不到就返回 (None, 原文)。\n    支持多种形态：\n    1) ```json ... ``` 代码块；\n    2) 裸 JSON（或带有前导 json/JSON 关键字）；\n    3) 文本中内嵌的完整 JSON 对象或数组。\n    """',
         '"""Extract tool calls from model output.\n    Returns (tool_calls, remaining_text); or (None, original_text) if none found.\n    """'),

        # Prompt formatting for video
        ('is_vertical = any(k in ar or k in sz for k in ("9:16", "9/16", "portrait", "竖屏", "720x1280", "1080x1920"))',
         'is_vertical = any(k in ar or k in sz for k in ("9:16", "9/16", "portrait", "vertical", "720x1280", "1080x1920"))'),
        ('parts.append(f"基于我本次上传的参考图片附件作为第一帧参考图（严禁使用历史图片或任何其他图像，必须严格以我当前刚刚上传并附带在此处的这张图片为起始帧）：生成一个严格9:16竖屏手机满屏的图生视频（9:16 vertical portrait video，720x1280，时长严格为 {dur} 秒）：{user_prompt}")',
         'parts.append(f"Based on my newly uploaded reference image attachment as the starting first frame (strictly do not use historical images): generate a 9:16 vertical portrait video (720x1280, duration strictly {dur}s): {user_prompt}")'),
        ('parts.append(f"全新文生视频创作（纯文本全新生成，严禁参考任何历史图片或上下文）：生成一个严格9:16竖屏手机满屏视频（9:16 vertical portrait video，720x1280，时长严格为 {dur} 秒）：{user_prompt}")',
         'parts.append(f"Text-to-video generation (pure text, do not reference historical images): generate a 9:16 vertical portrait video (720x1280, duration strictly {dur}s): {user_prompt}")'),
        ('elif any(k in ar or k in sz for k in ("16:9", "16/9", "landscape", "横屏", "1280x720", "1920x1080")):',
         'elif any(k in ar or k in sz for k in ("16:9", "16/9", "landscape", "horizontal", "1280x720", "1920x1080")):'),
        ('parts.append(f"基于我本次上传的参考图片附件作为第一帧参考图（严禁使用历史图片或任何其他图像，必须严格以我当前刚刚上传并附带在此处的这张图片为起始帧）：生成一个16:9宽屏横屏图生视频（16:9 widescreen landscape video，1280x720，时长严格为 {dur} 秒）：{user_prompt}")',
         'parts.append(f"Based on my newly uploaded reference image attachment as the starting first frame (strictly do not use historical images): generate a 16:9 widescreen landscape video (1280x720, duration strictly {dur}s): {user_prompt}")'),
        ('parts.append(f"全新文生视频创作（纯文本全新生成，严禁参考任何历史图片或上下文）：生成一个16:9横屏宽屏视频（16:9 widescreen landscape video，时长严格为 {dur} 秒）：{user_prompt}")',
         'parts.append(f"Text-to-video generation (pure text, do not reference historical images): generate a 16:9 widescreen landscape video (duration strictly {dur}s): {user_prompt}")'),
        ('parts.append(f"基于我本次上传的参考图片附件作为第一帧参考图（严禁使用历史图片或任何其他图像，必须严格以我当前刚刚上传并附带在此处的这张图片为起始帧）：生成动态图生视频（严格以附带的参考图为第一帧，时长严格为 {dur} 秒）：{user_prompt}")',
         'parts.append(f"Based on my newly uploaded reference image attachment as the starting first frame: generate a dynamic video (duration strictly {dur}s): {user_prompt}")'),
        ('parts.append(f"全新文生视频创作（纯文本全新生成，严禁参考任何历史图片或上下文）：生成一个视频（时长严格为 {dur} 秒）：{user_prompt}")',
         'parts.append(f"Text-to-video generation (duration strictly {dur}s): {user_prompt}")'),
        ('parts.append(f"画质规格：{r.resolution}")', 'parts.append(f"Resolution: {r.resolution}")'),

        # Media url docstring
        ('"""媒体地址。\n\n    配了 public_base 就返回**绝对 URL** —— OpenAI 兼容客户端（以及各类智能体\n    平台）拿到 data[].url 后一般会直接渲染或下载，相对路径会被解析到客户端\n    自己的域名上，导致 404。public_base 为空时退回相对路径。\n    """',
         '"""Media URL.\n    Returns absolute URL if public_base is configured, otherwise relative path.\n    """'),
        ('# ------------------------- cookie 解析 -------------------------', '# ------------------------- Cookie Parsing -------------------------'),
        ('"""把 `a=1; b=2` / JSON / Set-Cookie 行解析成 dict。"""', '"""Parse `a=1; b=2` / JSON / Set-Cookie lines into a dict."""'),
        ('"""批量导入：每行 `标签 | cookie串`，标签可省略。"""', '"""Batch import: each line formatted as `label | cookie_string` (label optional)."""'),
        ('# `|` 出现在 cookie 里时不算分隔符', '# `|` inside cookie value is not a delimiter'),
        ('# ------------------------- 核心生成 -------------------------', '# ------------------------- Core Generation Pipeline -------------------------'),
        ('# 有效期要「合并」而不是「覆盖」：会话 cookie 读回的 expires 是 -1，\n    # 若整体覆盖会把原有有效期记录清空（实测踩过这个坑）。',
         '# Merge expires instead of overwriting: session cookie expires is -1.'),
        ('log.warning("cookie 同步失败（不影响本次生成）: %s", exc)', 'log.warning("Cookie sync failed (does not affect current generation): %s", exc)'),
        ('raise MuseGenerationError("等待浏览器队列超时，请稍后重试")', 'raise MuseGenerationError("Timed out waiting in browser queue, please retry later")'),
        ('raise MuseGenerationError("任务总等待时限已到，停止重试")', 'raise MuseGenerationError("Total task timeout exceeded, stopping retries")'),
        ('log.info("【生图/视频自动切号】切换到备用账号 %s (%s) 重试...", cur_acc.get("label"), cur_acc["id"])',
         'log.info("[Auto Account Switch] Switching to alternate account %s (%s) to retry...", cur_acc.get("label"), cur_acc["id"])'),
        ('store.mark(cur_acc["id"], True, f"任务异常: {str(exc)[:60]}")',
         'store.mark(cur_acc["id"], True, f"Task exception: {str(exc)[:60]}")'),
        ('last_exc = MuseGenerationError(f"生成失败: {exc}")', 'last_exc = MuseGenerationError(f"Generation failed: {exc}")'),

        # Basic endpoints & images
        ('# ------------------------- 基础接口 -------------------------', '# ------------------------- Basic Endpoints -------------------------'),
        ('# ------------------------- 生图 -------------------------', '# ------------------------- Image Generation -------------------------'),
        ('raise HTTPException(404, "image task 不存在")', 'raise HTTPException(404, "Image task not found")'),
        ('"""OpenAI 兼容的图生图/图像编辑接口，兼容 multipart/form-data 与 application/json。"""',
         '"""OpenAI-compatible image editing / variation endpoint (supports multipart/form-data & application/json)."""'),
        ('prompt = "参考此图片并进行生图创作"', 'prompt = "Reference this image and create artwork"'),
        ('# ------------------------- 生视频（异步任务） -------------------------', '# ------------------------- Video Generation (Async) -------------------------'),
        ('raise HTTPException(404, "task 不存在")', 'raise HTTPException(404, "Task not found")'),
        ('# ------------------------- 对话（OpenAI 兼容） -------------------------', '# ------------------------- Chat Completions (OpenAI Compatible) -------------------------'),
        ('raise HTTPException(400, "messages 为空")', 'raise HTTPException(400, "messages cannot be empty")'),
        ('raise HTTPException(400, "没有可用账号，请先在管理页面导入 cookie")', 'raise HTTPException(400, "No available account, please import cookies in admin dashboard")'),
        ('store.mark(acc_id, True, f"助手超时: {str(exc)[:60]}")', 'store.mark(acc_id, True, f"Assistant timeout: {str(exc)[:60]}")'),
        ('yield _sse({"error": {"message": f"内部错误: {exc}", "type": "server_error", "code": 500}})',
         'yield _sse({"error": {"message": f"Internal error: {exc}", "type": "server_error", "code": 500}})'),
        ('msgs.append(ChatMessage(role="user", content="【工具执行结果】\\n"',
         'msgs.append(ChatMessage(role="user", content="[Tool Execution Result]\\n"'),
        ('msgs.append(ChatMessage(role="assistant", content="【请求调用工具】"',
         'msgs.append(ChatMessage(role="assistant", content="[Request Tool Call]"'),
        ('"""OpenAI Responses API —— 新版 Codex 默认走这个端点。\n\n    只实现 Codex 实际用到的子集：文本进 → 文本出（含流式事件）。\n    muse.ai 不会返回结构化的 tool_calls，关于工具调用的边界见 README。\n    """',
         '"""OpenAI Responses API -- used by new Codex.\n    Implements text in -> text out subset with streaming events.\n    """'),
        ('raise HTTPException(400, "input 为空")', 'raise HTTPException(400, "input cannot be empty")'),
        ('log.warning("responses 流式失败: %s", exc)', 'log.warning("Responses stream failed: %s", exc)'),
        ('raise HTTPException(400, "非法文件名")', 'raise HTTPException(400, "Invalid file name")'),
        ('raise HTTPException(404, "文件不存在")', 'raise HTTPException(404, "File not found")'),

        # Admin Endpoints
        ('# ------------------------- 管理：总览 -------------------------', '# ------------------------- Admin: Overview -------------------------'),
        ('# ------------------------- 管理：账号池 -------------------------', '# ------------------------- Admin: Account Pool -------------------------'),
        ('seen: list[dict] = []          # 本次导入的所有 cookie，用来检查核心项是否齐全',
         'seen: list[dict] = []          # Cookies imported in this batch, checked for completeness'),
        ('raise HTTPException(400, "未解析到任何 cookie，请检查格式")',
         'raise HTTPException(400, "No cookies parsed, please check format")'),
        ('"warning": (f"缺少核心 cookie：{\', \'.join(missing)}，该账号可能无法生成"',
         '"warning": (f"Missing essential cookies: {\', \'.join(missing)}, account may not be able to generate"'),
        ('raise HTTPException(404, "账号不存在")', 'raise HTTPException(404, "Account not found")'),
        ('"""真实打开 muse.ai 验证该账号 cookie 是否仍可登录。"""',
         '"""Open muse.ai to verify whether account cookies are valid."""'),
        ('raise HTTPException(400, "该账号没有 cookie")', 'raise HTTPException(400, "Account has no cookies")'),
        ('store.mark(aid, True, "会话有效")', 'store.mark(aid, True, "Session valid")'),
        ('return {"ok": True, "message": "会话有效，可正常生成",', 'return {"ok": True, "message": "Session valid, ready to generate",'),
        ('store.touch_keepalive(aid, None, f"测试未确认（保留账号状态）: {str(exc)[:200]}")',
         'store.touch_keepalive(aid, None, f"Test unconfirmed (retaining status): {str(exc)[:200]}")'),
        ('"""更新某个账号的 cookie（用于会话过期后补新 cookie）。"""',
         '"""Update cookies for an account (used when session expires)."""'),
        ('raise HTTPException(400, "未解析到 cookie")', 'raise HTTPException(400, "No cookies parsed")'),
        ('note="已更新 cookie",', 'note="Cookies updated",'),
        ('raise HTTPException(400, "没有可用账号")', 'raise HTTPException(400, "No available accounts")'),
        ('# ------------------------- 管理：额度 -------------------------', '# ------------------------- Admin: Quota -------------------------'),
        ('"""打开 muse.ai 的 Settings 面板读该账号的额度（实时），并缓存到账号记录。',
         '"""Open muse.ai Settings panel to read quota (real-time) and cache in account record.'),
        ('raise HTTPException(502, f"额度查询失败: {exc}") from exc',
         'raise HTTPException(502, f"Quota query failed: {exc}") from exc'),
        ('"""用当前最久未用的可用账号查一次额度（同池账号共享同一 muse.ai 计划的\n    通常只有一人使用时够用；多账号时建议按账号查）。"""',
         '"""Query quota using the least recently used account in pool."""'),
        ('# ------------------------- 管理：接入信息 / API Key -------------------------',
         '# ------------------------- Admin: Access Info / API Key -------------------------'),
        ('"""生成新的 API Key，写入 .env 并立即生效（不用重启）。"""',
         '"""Generate a new API Key, write to .env, and apply immediately without restart."""'),
        ('"message": "已生成新 Key 并立即生效；旧 Key 已失效，请更新下游项目"',
         '"message": "New Key generated and active; old Key is invalidated, please update clients"'),
        ('"""把配置写回 .env（保留其它行，原子替换）。"""',
         '"""Write config back to .env with atomic replacement."""'),
        ('# ------------------------- 管理：Cookie 获取 -------------------------',
         '# ------------------------- Admin: Cookie Extraction -------------------------'),
        ('"""返回本机取 cookie 的助手脚本（进阶方式，需要装 Python）。"""',
         '"""Return local cookie extraction helper script (advanced, requires Python)."""'),
        ('raise HTTPException(404, "助手脚本缺失")', 'raise HTTPException(404, "Helper script missing")'),
        ('"""把浏览器扩展打包成 zip 返回（推荐方式，零命令行）。\n    用户下载后解压 → chrome://extensions 开发者模式加载 → 点一下就导入 cookie。\n    """',
         '"""Package browser extension as zip (recommended, zero command-line).\n    Unzip and load unpacked in chrome://extensions -> 1-click import.\n    """'),
        ('raise HTTPException(404, "扩展目录缺失")', 'raise HTTPException(404, "Extension directory missing")'),
        ('"""列出扩展目录内容（前端展示用）。"""', '"""List extension directory files (for frontend display)."""'),
        ('# ------------------------- 管理：任务 / 媒体 -------------------------',
         '# ------------------------- Admin: Tasks / Media -------------------------'),
        ('raise HTTPException(404, "任务不存在")', 'raise HTTPException(404, "Task not found")'),
        ('raise HTTPException(400, "names 必须是文件名数组")', 'raise HTTPException(400, "names must be an array of file names")'),
        ('errors.append(f"非法文件名: {name}")', 'errors.append(f"Invalid file name: {name}")'),
        ('raise HTTPException(500, f"删除失败: {e}")', 'raise HTTPException(500, f"Delete failed: {e}")'),
        ('# ------------------------- 前端页面 -------------------------', '# ------------------------- Frontend Admin UI -------------------------'),
        ('"<h2>muse2api</h2><p>管理页面文件 admin.html 缺失。</p>"',
         '"<h2>muse2api</h2><p>Admin dashboard file admin.html missing.</p>"'),
        ('"<p>接口可用：<code>/v1/images/generations</code>、"',
         '"<p>Available endpoints: <code>/v1/images/generations</code>, "'),
        ('# ------------------------- 账号自动保活与静默续期 -------------------------',
         '# ------------------------- Account Auto-Keepalive & Silent Renewal -------------------------'),
        ('"""通过 muse.ai/api/session 触发 Meta 网关签发新 hatch_vml (+48h) / hatch_sess (+30d) 并唤醒云端 VM。"""',
         '"""Trigger session renewal via muse.ai/api/session and wake cloud workspace VM."""'),
        ('return {"ok": False, "id": aid, "label": (acc or {}).get("label", aid), "error": "账号无有效 cookie"}',
         'return {"ok": False, "id": aid, "label": (acc or {}).get("label", aid), "error": "Account has no valid cookies"}'),
        ('store.touch_keepalive(aid, True, f"会话有效 · 自动保活 (VM: {vm_state})")',
         'store.touch_keepalive(aid, True, f"Session valid - auto keepalive (VM: {vm_state})")'),
        ('log.warning("读取账号 %s 额度失败: %s", aid, qe)', 'log.warning("Failed to read quota for account %s: %s", aid, qe)'),
        ('store.touch_keepalive(aid, False, f"保活认证失败: {str(exc)[:200]}")',
         'store.touch_keepalive(aid, False, f"Keepalive auth failed: {str(exc)[:200]}")'),
        ('store.touch_keepalive(aid, None, f"保活未确认（保留账号状态）: {str(exc)[:200]}")',
         'store.touch_keepalive(aid, None, f"Keepalive unconfirmed (retaining status): {str(exc)[:200]}")'),
        ('"""执行账号保活：force=True 时强制刷新所有启用账号，否则刷新临期/未检账号并保持 VM 热备。"""',
         '"""Perform account keepalive: force=True refreshes all enabled accounts, otherwise refreshes expiring/untested accounts."""'),
        ('skipped.append({"id": aid, "label": label, "reason": "会话充足且近期已保活"})',
         'skipped.append({"id": aid, "label": label, "reason": "Session valid and recently refreshed"})'),
        ('log.info("【自动保活】正在为账号 %s (%s) 执行静默续期与 VM 唤醒...", label, aid)',
         'log.info("[Auto Keepalive] Performing silent renewal and VM wake for account %s (%s)...", label, aid)'),
        ('log.info("【自动保活】账号 %s 执行结果: ok=%s expires_at=%s", label, res.get("ok"), res.get("expires_at"))',
         'log.info("[Auto Keepalive] Account %s result: ok=%s expires_at=%s", label, res.get("ok"), res.get("expires_at"))'),
        ('"""后台静默预热浏览器与首个可用账号的 WebSocket 隧道，使重启后首条请求也秒回。"""',
         '"""Pre-warm browser and WebSocket connection in background."""'),
        ('log.info("【浏览器预热】正在后台预热账号 %s (%s) 的热备标签页...", acc.get("label"), acc["id"])',
         'log.info("[Browser Warmup] Pre-warming standby tab for account %s (%s)...", acc.get("label"), acc["id"])'),
        ('log.info("【浏览器预热】账号 %s (%s) 热备标签页与 WebSocket 已就绪", acc.get("label"), acc["id"])',
         'log.info("[Browser Warmup] Standby tab and WebSocket ready for account %s (%s)", acc.get("label"), acc["id"])'),
        ('log.warning("【浏览器预热】预热异常: %s", exc)', 'log.warning("[Browser Warmup] Warmup exception: %s", exc)'),
        ('"""后台常驻守护任务：每 15 分钟轮询一次账号健康状态并保持 VM 热备。"""',
         '"""Background daemon: checks account health every 15 minutes."""'),
        ('log.info("【自动保活守护进程】已启动，检测周期: 15 分钟")',
         'log.info("[Keepalive Daemon] Started, check interval: 15 minutes")'),
        ('log.warning("【浏览器预热】异常: %s", e)', 'log.warning("[Browser Warmup] Exception: %s", e)'),
        ('log.error("【自动保活守护进程】轮询异常: %s", e)', 'log.error("[Keepalive Daemon] Polling exception: %s", e)'),
        ('"""管理员手动触发一次全账号保活续期。"""', '"""Admin manually triggers keepalive for all accounts."""'),
        ('return {"status": "busy", "message": "保活任务正在执行中，请稍候"}',
         'return {"status": "busy", "message": "Keepalive task in progress, please wait"}'),
        ('"""手动针对单个账号执行保活续期。"""', '"""Manually trigger keepalive for a single account."""'),
        ('"""获取保活守护协程状态。"""', '"""Get keepalive daemon status."""'),
        ('# ------------------------- 仓库实时更新检测、通知与一键在线升级 -------------------------',
         '# ------------------------- Real-time Repo Update Check, Notifications & Upgrade -------------------------'),
        ('"""确保 BASE_DIR 已初始化为绑定 czg86389-hub/muse2api 的 Git 仓库。"""',
         '"""Ensure BASE_DIR is initialized as a Git repository tracking czg86389-hub/muse2api."""'),
        ('"""检测 GitHub 官方仓库 (czg86389-hub/muse2api) 是否有新版本或新提交。\n    默认缓存 90 秒，防止频繁刷新触发 GitHub API 速率限制。"""',
         '"""Check GitHub upstream repository for updates (cached 90s)."""'),
        ('# 若用户通过 Docker/ZIP 部署（无 .git）且首次运行版本一致，记录初始基准 SHA',
         '# Record initial baseline SHA if deployed via Docker/ZIP (no .git)'),
        ('"""从 GitHub 拉取最新代码覆盖核心文件（兼容 Git 与无 Git 的 Docker/ZIP 环境），绝不触碰 .env 与 data/。"""',
         '"""Pull latest code from GitHub to update core files (preserving .env and data/)."""'),
        ('log.warning("Git 拉取更新失败，将使用 Tarball 方式更新: %s", e)',
         'log.warning("Git pull failed, falling back to Tarball update: %s", e)'),
        ('raise HTTPException(502, f"下载 GitHub 更新包失败 (HTTP {resp.status_code})")',
         'raise HTTPException(502, f"Failed to download GitHub update archive (HTTP {resp.status_code})")'),
        ('"message": f"已成功更新至最新版本 {status.get(\'remote_version\')} ({status.get(\'remote_sha\')})"',
         '"message": f"Successfully updated to latest version {status.get(\'remote_version\')} ({status.get(\'remote_sha\')})"'),
        ('"""供所有已部署节点实时检测 GitHub 官方仓库是否有新版本更新。"""',
         '"""Endpoint to check if upstream GitHub repository has updates."""'),
        ('"""一键从 GitHub 官方仓库拉取最新更新并自动平滑重启服务。"""',
         '"""1-click pull latest updates from GitHub and restart service."""'),
        ('"""维护者专用：将当前节点核心代码推送到 GitHub 仓库（自动过滤 .env 与 data 目录）。"""',
         '"""Maintainer only: push core code to GitHub repository."""'),
        ('raise HTTPException(500, f"Git commit 失败: {c_res.stderr or c_res.stdout}")',
         'raise HTTPException(500, f"Git commit failed: {c_res.stderr or c_res.stdout}")'),
        ('raise HTTPException(500, f"Git push 失败: {err[:300]}")',
         'raise HTTPException(500, f"Git push failed: {err[:300]}")'),
        ('"message": "已成功提交并推送到 GitHub 仓库"',
         '"message": "Successfully committed and pushed to GitHub repository"'),
        ('store.update_task(task["id"], status="failed", error="服务重启中断了任务，请重新提交")',
         'store.update_task(task["id"], status="failed", error="Task interrupted by service restart, please resubmit")'),
        ('log.info("🔑 未检测到 MUSE2API_KEY，已自动生成初始密钥: %s", new_key)',
         'log.info("No MUSE2API_KEY found, automatically generated initial key: %s", new_key)'),
    ]

    for t, r in subs:
        c = c.replace(t, r)

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(c)

    print("Done translate_app")

translate_app()
