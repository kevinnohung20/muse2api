# -*- coding: utf-8 -*-
import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacements = [
    # 62-67
    ("""# Cookie 助手脚本从 muse.ai 页面发起导入请求，需要放行该来源；
# 浏览器扩展从 chrome-extension:// 发起，也一并放行。
# 这里直接放行所有来源：本服务用 Bearer Key 鉴权、不依赖 Cookie，
# 放行来源不会带来越权风险；反之如果把来源限死，浏览器端的智能体
# （Open WebUI / LobeChat / 各种 Web 客户端）会被 CORS 拦住用不了。""",
     """# Allow CORS origins: allow import from muse.ai and chrome-extension://
# All origins are permitted; bearer key auth is used to prevent unauthorized access."""),

    # 83-86
    (""""""多账号并发调度锁。
由 CFG.max_concurrency 限制最大并发槽位；
同时提供与标准 Lock 兼容的 acquire / release / locked 接口，
确保向下兼容历史单锁断言与管理端操作。""""",
     """"""Multi-account concurrency scheduling lock.
Limits maximum concurrency slots via CFG.max_concurrency;
provides standard acquire / release / locked interface compatible with Lock.""""""),

    # 124-161
    (""""""账号并发冲突管理器：确保同一账号不会同时被两个并发任务操作，多账号则并行执行。""""",
     """"""Account concurrency conflict manager: ensures one account is not used by two concurrent tasks.""""""),

    ('raise MuseGenerationError("等待空闲账号超时，当前所有账号均处于繁忙中")',
     'raise MuseGenerationError("Timed out waiting for idle account, all accounts are currently busy")'),

    ('raise MuseAuthError(f"指定账号 {account_id} 不存在或已禁用")',
     'raise MuseAuthError(f"Specified account {account_id} does not exist or is disabled")'),

    ('raise MuseAuthError("没有可用账号，请先在管理页面导入 cookie")',
     'raise MuseAuthError("No available accounts, please import cookies in admin dashboard")'),

    # 179-182
    ("""# ------------------------- OpenAI 风格的错误响应 -------------------------
# 各类智能体基本都按 OpenAI 的 {"error": {"message": ...}} 取错误信息；
# FastAPI 默认返回的是 {"detail": ...}，客户端会读不到原因、只显示"未知错误"。
# 所以 /v1/* 统一转成 OpenAI 格式，管理接口保持原样（前端依赖 detail）。""",
     """# ------------------------- OpenAI Format Error Response -------------------------
# Translates errors into {"error": {"message": ...}} for OpenAI compatibility."""),

    ('"message": "请求参数校验失败：" + str(exc.errors())[:400],',
     '"message": "Request validation failed: " + str(exc.errors())[:400],'),

    # 217-221
    ('"description": "Muse Spark —— 文本 / 代码对话（网页免费额度，支持流式）"},',
     '"description": "Muse Spark -- Text / code chat (web quota, supports stream)"},'),

    ('"description": "Muse Image —— 文生图 / 图像编辑（网页免费额度）"},',
     '"description": "Muse Image -- Text-to-image / image editing (web quota)"},'),

    ('"description": "Muse Video —— 文生视频 / 图生视频（网页免费额度）"},',
     '"description": "Muse Video -- Text-to-video / image-to-video (web quota)"},'),

    # 224-250
    ("""# 下游（Codex / Cline / 各种客户端）习惯按 OpenAI、Anthropic 的名字传模型，
# 这里统一映射到 muse 的真实能力上。
# 说明：muse.ai 网页是自动路由的 agent，对外**没有可枚举的模型清单**，
# 能稳定调用的就是三条真实能力 —— Muse Spark（语言/代码）、
# Muse Image（生图）、Muse Video（生视频）。别名只是让下游不用改配置。
# ---- 文本 / 代码 → muse-spark ----""",
     """# Map external model names to Muse capabilities:
# muse-spark (text/code), muse-image (images), muse-video (videos).
# ---- Text / Code -> muse-spark ----"""),

    ('# ---- 生图 → muse-image ----', '# ---- Image -> muse-image ----'),
    ('# ---- 生视频 → muse-video ----', '# ---- Video -> muse-video ----'),

    # 262-271
    ('raise HTTPException(401, "缺少 Authorization: Bearer <key>")',
     'raise HTTPException(401, "Missing Authorization: Bearer <key>")'),
    ('raise HTTPException(401, "API key 无效")',
     'raise HTTPException(401, "Invalid API key")'),

    # 278-344
    (""""""调用 /api/session 续签账号 cookie 并写回 store，返回最新账号 dict。
近期（10分钟内）已续签且状态正常的账号直接复用，避免每次请求阻塞 2~3 秒 HTTP 往返。""""",
     """"""Call /api/session to renew cookies and return latest account dict.""""""),

    ('store.touch_keepalive(acc_id, True, f"会话正常 (VM: {res.get(\'vm_state\') or \'RUNNING\'})")',
     'store.touch_keepalive(acc_id, True, f"Session healthy (VM: {res.get(\'vm_state\') or \'RUNNING\'})")'),

    ('log.warning("HTTP 预续签账号 %s 异常: %s", acc_id, exc)',
     'log.warning("HTTP pre-renewal for account %s failed: %s", acc_id, exc)'),

    (""""""在独立线程中执行 chat_stream 并持有 GEN_LOCK，通过 Queue 往外吐。
无论下游客户端何时断连、异常或超时，stop_event + finally 块保证 100% 立即释放 GEN_LOCK，绝不死锁。
若首字前遇到单账号 VM 卡死或会话异常，自动切换下一个健康账号重试一次。""""",
     """"""Execute chat_stream in worker thread with queue output and auto retry on alternate account.""""""),

    ('log.info("【对话自动切号】切换到备用账号 %s (%s) 重试...", alt.get("label"), cur_id)',
     'log.info("[Chat Auto Switch] Switching to alternate account %s (%s) to retry...", alt.get("label"), cur_id)'),
]

for old, new in replacements:
    # replace with both LF and CRLF variations
    old_crlf = old.replace('\n', '\r\n')
    new_crlf = new.replace('\n', '\r\n')
    if old in text:
        text = text.replace(old, new)
    elif old_crlf in text:
        text = text.replace(old_crlf, new_crlf)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Finish app done")
