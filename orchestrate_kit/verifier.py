"""确定性裁决层 — 绝不信任原始模型输出。

任何模型给出的 action / message_type / confidence / evidence 都必须经过这里
校验与降级。不过关就丢回安全默认值，保证提交的 output.csv 永远合法。
"""


def verify(pred, allowed_actions, allowed_types, valid_evidence):
    out = dict(pred) if pred else {}

    a = (out.get("action") or "").strip().lower()
    out["action"] = a if a in allowed_actions else "digest"

    t = (out.get("message_type") or "").strip().lower()
    out["message_type"] = t if t in allowed_types else "unknown"

    try:
        c = float(out.get("confidence", 0.5))
    except (TypeError, ValueError):
        c = 0.5
    out["confidence"] = round(max(0.0, min(1.0, c)), 2)

    reason = (out.get("reason") or "").strip()
    out["reason"] = reason or "No strong signal; deferred to digest."

    ev = out.get("evidence_message_ids") or "none"
    if isinstance(ev, list):
        ev = ";".join([e for e in ev if e in valid_evidence]) or "none"
    else:
        parts = [e.strip() for e in str(ev).replace(";", ",").split(",") if e.strip()]
        ev = ";".join([e for e in parts if e in valid_evidence]) or "none"
    out["evidence_message_ids"] = ev

    return out
