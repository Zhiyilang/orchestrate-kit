"""智能体层 — 模型提议，离线启发式兜底。

LLM 模式调用 OpenAI 兼容接口（读 OPENAI_API_KEY / OPENAI_BASE_URL 环境变量）。
无 key 或调用失败时自动退回问题自带的 heuristic()，保证 24 小时内一定能跑出 output.csv。
"""
import json
import os
import urllib.request

import orchestrate_kit.log_utils as log_utils


def _call_llm(system, prompt, api_key, base_url):
    if not api_key:
        return None
    url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    body = {
        "model": os.environ.get("ORC_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    # 首选带 json_object 约束；非 OpenAI 兼容提供商（如 MiMo/部分国产端点）
    # 可能不支持 response_format 而整体 400 —— 那就退一格重试，别直接掉兜底。
    variants = [dict(body, response_format={"type": "json_object"}), body]
    last_err = None
    for payload in variants:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:  # noqa: BLE001
            last_err = e
            # JSON 解析失败（模型没给纯 JSON）也尝试从文本里抠
            try:
                text = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
            except Exception:  # noqa: BLE001
                text = ""
            if text:
                salvaged = _salvage_json(text)
                if salvaged is not None:
                    return salvaged
    return {"_error": str(last_err)}


def _salvage_json(text):
    """从错误响应或混排文本里抢救 JSON 对象（有些端点把内容包在 error 里返回）。"""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        obj = json.loads(text[start:end + 1])
    except Exception:  # noqa: BLE001
        return None
    return obj if isinstance(obj, dict) and "action" in obj else None


def propose(problem, msg, ctx, mode, log):
    if mode == "llm":
        system = problem.system_prompt()
        prompt = problem.build_prompt(msg, ctx)
        log.info("LLM_PROMPT", prompt[:200])
        resp = _call_llm(system, prompt, os.environ.get("OPENAI_API_KEY"),
                         os.environ.get("OPENAI_BASE_URL"))
        if resp and "action" in resp:
            log.info("LLM_RESP", str(resp)[:200])
            return _merge(problem, msg, ctx, resp)
        log.info("LLM_FALLBACK", "LLM failed/unavailable -> heuristic")

    pred = problem.heuristic(msg, ctx)
    pred["evidence_message_ids"] = problem.extract_evidence(msg, ctx)
    log.info("HEURISTIC", "%s -> %s/%s" % (
        msg.get("message_id"), pred.get("action"), pred.get("message_type")))
    return pred


def _merge(problem, msg, ctx, resp):
    ev = resp.get("evidence_message_ids")
    if not ev:
        ev = problem.extract_evidence(msg, ctx)
    return {
        "action": resp.get("action"),
        "message_type": resp.get("message_type"),
        "reason": resp.get("reason"),
        "confidence": resp.get("confidence", 0.6),
        "evidence_message_ids": ev,
    }
