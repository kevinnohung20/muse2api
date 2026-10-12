# -*- coding: utf-8 -*-
with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Normalize CRLF to LF temporarily for matching, then write back cleanly
lines = text.splitlines(True)
out = []

for line in lines:
    l = line
    # 448-460
    if '"""OpenAI Chat Completions 请求' in l:
        l = '    """OpenAI Chat Completions request model."""\n'
    elif 'prompt: str | None = None       # 兼容把 prompt 直接放顶层的客户端' in l:
        l = '    prompt: str | None = None       # Compatibility for clients placing prompt at top level\n'
    elif '# 下面这些声明出来只是为了「能读到」' in l:
        l = '    # Declared for compatibility only\n'
    elif '"""OpenAI Responses API（新版 Codex 默认走这个）。"""' in l:
        l = '    """OpenAI Responses API request model."""\n'
    elif 'batch: str | None = None          # 多行文本，每行一个账号' in l:
        l = '    batch: str | None = None          # Multiline text, one account per line\n'
    elif 'expires: dict[str, int] = Field(default_factory=dict)   # cookie 名 -> 过期时间戳' in l:
        l = '    expires: dict[str, int] = Field(default_factory=dict)   # Cookie name -> expiration timestamp\n'
    elif '# ------------------------- 提示词构造 -------------------------' in l:
        l = '# ------------------------- Prompt Construction -------------------------\n'
    elif '基于我本次上传附带的参考图片进行生图/编辑：' in l:
        l = l.replace('基于我本次上传附带的参考图片进行生图/编辑：', 'Generate/edit image based on attached reference image: ')
    elif '全新文生图创作（当前未提供任何参考图，请勿查找历史相册或向用户索要原图，直接根据文字描述从零绘制生成一张全新图片）：' in l:
        l = l.replace('全新文生图创作（当前未提供任何参考图，请勿查找历史相册或向用户索要原图，直接根据文字描述从零绘制生成一张全新图片）：',
                      'Text-to-image creation from scratch (do not reference historical images): ')
    elif '"竖屏"' in l:
        l = l.replace('"竖屏"', '"vertical"')
    elif '【画面构图与比例要求】：严格 9:16 竖屏满屏画幅' in l:
        l = '        parts.append("[Composition & Aspect Ratio]: Strictly 9:16 vertical full screen portrait (720x1280), do not generate horizontal")\n'
    elif '【画面构图与比例要求】：16:9 宽屏横屏画幅' in l:
        l = '        parts.append("[Composition & Aspect Ratio]: 16:9 widescreen landscape aspect ratio (1280x720)")\n'
    elif '"正方形"' in l:
        l = l.replace('"正方形"', '"square"')
    elif '【画面构图与比例要求】：1:1 正方形画幅' in l:
        l = '        parts.append("[Composition & Aspect Ratio]: 1:1 square aspect ratio")\n'
    elif '【画面构图与比例要求】：4:3 比例画幅' in l:
        l = '        parts.append("[Composition & Aspect Ratio]: 4:3 aspect ratio")\n'
    elif '【画面构图与比例要求】：3:4 竖向画幅' in l:
        l = '        parts.append("[Composition & Aspect Ratio]: 3:4 vertical aspect ratio")\n'
    elif '【画面构图与比例要求】：' in l:
        l = l.replace('【画面构图与比例要求】：', '[Composition & Aspect Ratio]: ').replace(' 画面比例', ' aspect ratio')
    elif '尺寸/比例：' in l:
        l = l.replace('尺寸/比例：', 'Size/Ratio: ')
    elif '【纯净画面要求】：彻底清除并去除参考图中的所有文字、水印、签名、角标及Logo标记' in l:
        l = '    parts.append("[Clean Image Requirement]: Completely remove all watermarks, text, signatures, and logos (clean image without watermarks)")\n'
    elif '"""把 OpenAI 的 content 归一成纯文本（兼容多模态 list 形式）。"""' in l:
        l = '    """Normalize OpenAI content into plain text (supports multimodal lists)."""\n'
    elif 'parts.append("[图片]")' in l:
        l = '                parts.append("[Image]")\n'
    elif '"""把 messages 拼成发给 muse.ai 的一段提示词。' in l:
        l = '    """Assemble messages into a prompt for muse.ai."""\n'
    elif '# 工具执行结果 → 当成"用户提供的信息"发过去' in l:
        l = '        # Tool execution result -> treated as user-provided info\n'
    elif '【工具执行结果】' in l:
        l = l.replace('【工具执行结果】', '[Tool Execution Result]')
    elif '# 部分客户端的 assistant 消息只带 tool_calls、没有正文' in l:
        l = '        # Some assistant messages only contain tool_calls\n'
    elif '【请求调用工具】' in l:
        l = l.replace('【请求调用工具】', '[Request Tool Call]')
    elif '# 单轮且无系统指令 → 直接发原文，最贴近自然对话' in l:
        l = '    # Single turn without system prompt -> send raw text\n'
    elif '背景与任务设定：' in l:
        l = l.replace('背景与任务设定：', 'Background & Task Configuration:\n')
    elif 'label = "助手" if role == "assistant" else "用户"' in l:
        l = '        label = "Assistant" if role == "assistant" else "User"\n'
    elif '# ------------------------- 工具调用（function calling）适配 -------------------------' in l:
        l = '# ------------------------- Function Calling Adaptation -------------------------\n'
    elif '# muse.ai 的网页模型**不会**返回结构化的 tool_calls' in l:
        l = '# muse.ai web model does not natively return structured tool_calls.\n'
    elif '基于我本次上传的参考图片附件作为第一帧参考图' in l:
        l = l.replace('基于我本次上传的参考图片附件作为第一帧参考图（严禁使用历史图片或任何其他图像，必须严格以我当前刚刚上传并附带在此处的这张图片为起始帧）：生成一个严格9:16竖屏手机满屏的图生视频（9:16 vertical portrait video，720x1280，时长严格为',
                      'Based on attached reference image as first frame (do not use history images): generate 9:16 vertical portrait video (720x1280, duration strictly')
        l = l.replace('基于我本次上传的参考图片附件作为第一帧参考图（严禁使用历史图片或任何其他图像，必须严格以我当前刚刚上传并附带在此处的这张图片为起始帧）：生成一个16:9宽屏横屏图生视频（16:9 widescreen landscape video，1280x720，时长严格为',
                      'Based on attached reference image as first frame: generate 16:9 widescreen video (1280x720, duration strictly')
        l = l.replace('基于我本次上传的参考图片附件作为第一帧参考图（严禁使用历史图片或任何其他图像，必须严格以我当前刚刚上传并附带在此处的这张图片为起始帧）：生成动态图生视频（严格以附带的参考图为第一帧，时长严格为',
                      'Based on attached reference image as first frame: generate dynamic video (duration strictly')
    elif '全新文生视频创作（纯文本全新生成，严禁参考任何历史图片或上下文）：生成一个严格9:16竖屏手机满屏视频' in l:
        l = l.replace('全新文生视频创作（纯文本全新生成，严禁参考任何历史图片或上下文）：生成一个严格9:16竖屏手机满屏视频（9:16 vertical portrait video，720x1280，时长严格为',
                      'Text-to-video generation (pure text, do not reference history images): generate 9:16 vertical video (720x1280, duration strictly')
    elif '"""生成完从浏览器读回 cookie 并写回账号池。' in l:
        l = '    """Read renewed cookies back from browser and update account pool."""\n'
    elif '未产出媒体附件，仅返回了文本回复' in l:
        l = l.replace('未产出媒体附件，仅返回了文本回复', 'no media attachment produced, text response only')
    elif '"""下游（LangChain、部分 SDK / 智能体框架）会带' in l:
        l = '    """Send usage chunk before [DONE] for LangChain and framework compatibility."""\n'
    elif '"""把大块文本平滑切分为仿原生 LLM 打字机的微流式 Token。' in l:
        l = '    """Smoothly slice text into streaming typewriter tokens."""\n'
    elif '"""OpenAI 兼容的对话接口 —— 各类智能体客户端都能接。' in l:
        l = '    """OpenAI-compatible chat completions endpoint."""\n'
    elif '# 工具调用协议默认不注入 —— 实测 muse.ai 的助手会明确拒绝输出"伪工具调用"' in l:
        l = '    # Tool protocol not injected by default\n'
    elif '# 放在末尾：开头是 agent 自己的 system 提示' in l:
        l = '    # Append instructions near end of prompt for better adherence\n'
    elif '"""按 OpenAI 习惯分两片发：先 id/name，再 arguments 全文。"""' in l:
        l = '    """Send tool_calls chunks in OpenAI standard format."""\n'
    elif '# 握手建立瞬间立即发送 role: assistant 首包，让下游客户端秒级捕获光标' in l:
        l = '        # Send initial assistant role packet for immediate responsiveness\n'
    elif '"""把 Responses API 的 instructions / input 归一成 messages。"""' in l:
        l = '    """Normalize Responses API instructions/input into messages."""\n'
    elif 'if item.get("role"):                      # message 形态' in l:
        l = '        if item.get("role"):                      # message format\n'
    elif '# 只要有一个账号把核心 cookie 凑齐就算通过（批量时按整体判断）' in l:
        l = '    # Check completeness of essential cookies across imported accounts\n'
    elif 'try:  # 顺带刷新额度；读不到不影响测试结论' in l:
        l = '        try:  # Refresh quota if available\n'
    elif '# 补入的是「全新会话」的 cookie，有效期估算锚点必须重置到当下' in l:
        l = '    # Reset anchor timestamp for newly updated session cookies\n'
    elif '返回例：{"plan":"Free plan","weekly_reset":"Sep 30"' in l:
        l = '    Returns example: {"plan":"Free plan","weekly_reset":"Sep 30"}\n'
    elif '"""把浏览器扩展打包成 zip 返回（推荐方式，零命令行）。' in l:
        l = '    """Package browser extension into zip for 1-click import."""\n'

    out.append(l)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(out)

print("Cleaned app.py")
