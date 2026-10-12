# -*- coding: utf-8 -*-
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    l = line
    # 62-67
    if '# Cookie 助手脚本' in l:
        l = '# Allow CORS origins: allow import from muse.ai and chrome-extension://\n'
    elif '# 浏览器扩展从 chrome-extension://' in l or '# 这里直接放行所有来源' in l or '# 放行来源不会带来越权风险' in l or '# （Open WebUI / LobeChat' in l:
        continue
    # 83-86
    elif '"""多账号并发调度锁。' in l:
        l = '    """Multi-account concurrency scheduling lock."""\n'
    elif '由 CFG.max_concurrency 限制最大并发槽位；' in l or '同时提供与标准 Lock 兼容的' in l or '确保向下兼容历史单锁断言' in l:
        continue
    # 124
    elif '"""账号并发冲突管理器' in l:
        l = '    """Account concurrency manager: prevents multiple concurrent tasks on the same account."""\n'
    # 138
    elif 'raise MuseGenerationError("等待空闲账号超时' in l:
        l = '                    raise MuseGenerationError("Timed out waiting for idle account, all accounts are busy")\n'
    # 143
    elif 'raise MuseAuthError(f"指定账号' in l:
        l = '                        raise MuseAuthError(f"Specified account {account_id} does not exist or is disabled")\n'
    # 161
    elif 'raise MuseAuthError("没有可用账号' in l:
        l = '                    raise MuseAuthError("No available accounts, please import cookies in admin dashboard")\n'
    # 179-182
    elif '# ------------------------- OpenAI 风格的错误响应 -------------------------' in l:
        l = '# ------------------------- OpenAI Format Error Response -------------------------\n'
    elif '# 各类智能体基本都按 OpenAI 的' in l or '# FastAPI 默认返回的是' in l or '# 所以 /v1/* 统一转成 OpenAI 格式' in l:
        continue
    # 211
    elif '"message": "请求参数校验失败："' in l:
        l = '            "message": "Request validation failed: " + str(exc.errors())[:400],\n'
    # 217-221
    elif '"Muse Spark —— 文本 / 代码对话' in l:
        l = '     "description": "Muse Spark -- Text / code chat (web quota, supports stream)"},\n'
    elif '"Muse Image —— 文生图 / 图像编辑' in l:
        l = '     "description": "Muse Image -- Text-to-image / image editing (web quota)"},\n'
    elif '"Muse Video —— 文生视频 / 图生视频' in l:
        l = '     "description": "Muse Video -- Text-to-video / image-to-video (web quota)"},\n'
    # 224-250
    elif '# 下游（Codex / Cline / 各种客户端）' in l:
        l = '# Map client model names to Muse capabilities:\n'
    elif '# 这里统一映射到 muse' in l or '# 说明：muse.ai 网页是自动路由' in l or '# 能稳定调用的就是三条' in l or '# Muse Image（生图）' in l:
        continue
    elif '# ---- 文本 / 代码 → muse-spark ----' in l:
        l = '    # ---- Text / Code -> muse-spark ----\n'
    elif '# ---- 生图 → muse-image ----' in l:
        l = '    # ---- Image -> muse-image ----\n'
    elif '# ---- 生视频 → muse-video ----' in l:
        l = '    # ---- Video -> muse-video ----\n'
    # 262-271
    elif '# ------------------------- 鉴权 -------------------------' in l:
        l = '# ------------------------- Authentication -------------------------\n'
    elif 'raise HTTPException(401, "缺少 Authorization: Bearer <key>")' in l:
        l = '        raise HTTPException(401, "Missing Authorization: Bearer <key>")\n'
    elif 'raise HTTPException(401, "API key 无效")' in l:
        l = '        raise HTTPException(401, "Invalid API key")\n'
    # 275-344
    elif '# ------------------------- 请求模型 -------------------------' in l:
        l = '# ------------------------- Request Models -------------------------\n'
    elif '"""调用 /api/session 续签账号 cookie' in l:
        l = '    """Call /api/session to renew cookies and return latest account dict."""\n'
    elif '近期（10分钟内）已续签且状态正常' in l:
        continue
    elif 'store.touch_keepalive(acc_id, True, f"会话正常' in l:
        l = '            store.touch_keepalive(acc_id, True, f"Session healthy (VM: {res.get(\'vm_state\') or \'RUNNING\'})")\n'
    elif 'log.warning("HTTP 预续签账号' in l:
        l = '        log.warning("HTTP pre-renewal for account %s failed: %s", acc_id, exc)\n'
    elif '"""在独立线程中执行 chat_stream 并持有 GEN_LOCK' in l:
        l = '    """Execute chat_stream in background thread with queue output."""\n'
    elif '无论下游客户端何时断连' in l or '若首字前遇到单账号 VM 卡死' in l:
        continue
    elif 'log.info("【对话自动切号】切换到备用账号' in l:
        l = '                    log.info("[Chat Auto Switch] Switching to alternate account %s (%s)...", alt.get("label"), cur_id)\n'
    # 450-451
    elif '对第三方客户端要尽量宽松' in l or '只挑我们真正用得上的读' in l:
        continue
    # 549-551
    elif 'muse.ai 网页本身是个带上下文的会话' in l or '不同账号/页面），所以把历史拼进' in l or '「每轮都带全量历史」的客户端' in l:
        continue
    # 591-596
    elif '#   1) 请求带 tools 时' in l or '#   2) 模型按协议输出' in l or '#   3) 我们把这段解析回' in l or '# 注意：这是"尽力适配"而非保证' in l or '# function calling 做微调' in l:
        continue
    # 725-735
    elif 'parts.append(f"基于我本次上传的参考图片附件作为第一帧参考图' in l:
        l = '            parts.append(f"Based on attached reference image: generate video (duration strictly {dur}s): {user_prompt}")\n'
    elif 'parts.append(f"全新文生视频创作（纯文本全新生成' in l:
        l = '            parts.append(f"Text-to-video generation (duration strictly {dur}s): {user_prompt}")\n'
    # 803-820
    elif '实测结论：**核心 cookie 的 expires 不会被使用行为续期**' in l or '约 2 天就到期），这里同步回来的主要是那些每次访问都会重新下发的非核心' in l or 'cookie（_fbp / wd / dpr 等）' in l or '注意：这个函数**绝不能把生成结果搞失败**' in l or '同步只是锦上添花，出任何问题都只记一条日志。' in l or '# 有效期要「合并」而不是「覆盖」' in l or '# 若整体覆盖会把原有有效期记录清空' in l:
        continue
    # 1234-1235
    elif '`stream_options.include_usage=true`，要求在 [DONE]' in l or '`choices: []` + `usage` 的分片' in l:
        continue
    # 1243-1244
    elif '若传入文本本身微小' in l or '若传入文本是大块' in l:
        continue
    # 1268-1275
    elif '说明：muse.ai 网页是**自动路由**的 agent' in l or '都会落到同一个网页助手' in l or '`model` 字段只用于兼容下游' in l or '请求带 `tools` 时，会注入' in l or '`tool_calls`（muse.ai 没有原生' in l or '对话与生图/生视频共用同一个浏览器实例' in l:
        continue
    # 1282, 1286
    elif '# 注入反而污染正常回答；详见' in l or '# 紧贴用户消息之前，模型对末尾指令' in l:
        continue
    # 1668
    elif '# 否则会沿用旧会话的锚点' in l:
        continue
    # 1799
    elif '用户下载后解压 → chrome://extensions' in l:
        continue

    new_lines.append(l)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Exact replace done")
