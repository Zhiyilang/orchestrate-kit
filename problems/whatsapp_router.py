"""WhatsApp Message Notification Router — 2026 八月 Orchestrate 真题（练习靶场）。

本文件是 Problem 接口的一个具体实现。10-25 拿到十月场新题后，
只需在 problems/ 下新建一个同类文件改这几处：
  - ALLOWED_ACTIONS / ALLOWED_TYPES
  - extra_context() 引用哪些上下文 CSV
  - system_prompt() / build_prompt()
  - heuristic() 的判定规则
  - extract_evidence() 的证据选取逻辑
loader / verifier / agent / solve / eval 全部不动。
"""
import re

ALLOWED_ACTIONS = ["notify", "digest", "mute"]
ALLOWED_TYPES = ["personal", "urgent", "event", "payment", "business_update",
                 "promotion", "greeting", "forward", "spam", "scam", "unknown"]

# 判定正则（离线启发式用；LLM 模式下作为提示词里的硬约束）
PROMO = re.compile(r"\b(buy|offer|sale|discount|subscribe|join|win|prize|limited|book now|shop|deal|off)\b", re.I)
SCAM = re.compile(r"\b(verify|account suspended|otp|click here|claim|password|urgent payment|congrat|lottery|inherit|urgent|转账|中奖|密码|验证码)\b", re.I)
URGENT = re.compile(r"\b(urgent|asap|immediately|deadline|overdue|due|eod|tonight|now|紧急|立刻)\b", re.I)
PAYMENT = re.compile(r"\b(payment|invoice|bill|due|overdue|refund|paid|order|delivery|账单|付款|订单|物流)\b", re.I)
EVENT = re.compile(r"\b(meeting|event|invite|rsvp|session|class|appointment|会议|活动|邀请|预约)\b", re.I)
PERSONAL = re.compile(r"\b(mom|dad|family|bro|sis|call|catch up|how are you|在吗|妈妈|爸爸|家人|电话)\b", re.I)
GREET = re.compile(r"\b(good morning|good evening|hope|peace|vibes|早|晚安|好)\b", re.I)
# 时间敏感 / 管理类信号：群内出现这些词，多半是要 notify 的运营/管理通知
TIME = re.compile(r"\b(by \d{1,2}|before \d{1,2}|at \d{1,2}|today|tonight|\d{1,2}[:.]\d{2}|deadline|eod|紧急|立刻|马上|今晚|今天)\b", re.I)
ADMIN = re.compile(r"\b(admin|teacher|school|principal|manager|security|supervisor|heads[- ]?up|notice|reminder|update|pls|please|kindly)\b", re.I)


class WhatsAppRouter:
    name = "whatsapp_router"
    allowed_actions = ALLOWED_ACTIONS
    allowed_types = ALLOWED_TYPES

    def extra_context(self):
        return {
            "users": "users.csv",
            "groups": "groups.csv",
            "business": "business_accounts.csv",
            "history": "message_history.csv",
            "events": "message_events.csv",
            "business_history": "user_business_history.csv",
        }

    def system_prompt(self):
        return ("You route WhatsApp messages for a noisy user stream. "
                "Return JSON with exactly these keys: "
                "action (one of notify|digest|mute), "
                "message_type (one of %s), "
                "reason (one short sentence), confidence (0-1). "
                "Mute clear scams/spam. Personalize using sender, group, "
                "business relationship and history." % "|".join(ALLOWED_TYPES))

    def build_prompt(self, msg, ctx):
        txt = msg.get("message_text", "") or ""
        return ("User %s received a %s message%s: %s\nDecide routing. "
                "Think step by step, then output JSON only." % (
                    msg.get("user_id"),
                    msg.get("conversation_type"),
                    " (media: %s)" % msg.get("media_type") if msg.get("media_type") else "",
                    txt[:600]))

    def heuristic(self, msg, ctx):
        txt = msg.get("message_text", "") or ""
        ctype = (msg.get("conversation_type") or "").lower()
        fwd = int(msg.get("forwarded_count") or 0)
        media = msg.get("media_type")

        # 媒体消息（图片/语音）离线无 OCR/ASR，按对话类型降级处理
        if media in ("image", "voice"):
            if ctype == "business":
                return self._pred("notify", "business_update", "Media from a verified business; treat as update.", 0.8)
            if ctype == "group":
                return self._pred("digest", "event", "Media inside a group; safe to defer.", 0.7)
            return self._pred("digest", "unknown", "Media without text; deferred.", 0.6)

        # 1) 诈骗优先
        if SCAM.search(txt):
            return self._pred("mute", "scam", "Likely scam/phishing pattern detected.", 0.92)
        # 2) 促销：opt-in 用户才 digest，否则 mute
        if PROMO.search(txt):
            if self._opted_in(ctx, msg):
                return self._pred("digest", "promotion", "Promotional but user opted into this business.", 0.7)
            return self._pred("mute", "promotion", "Unsolicited promotion; muted.", 0.8)
        # 3) 紧急 / 付款
        if PAYMENT.search(txt):
            return self._pred("notify", "payment", "Time-sensitive payment/order update.", 0.88)
        if URGENT.search(txt):
            return self._pred("notify", "urgent", "Urgent action or deadline mentioned.", 0.86)
        # 4) 事件
        if EVENT.search(txt):
            return self._pred("notify", "event", "Event/appointment the user likely needs.", 0.84)
        # 5) 个人
        if PERSONAL.search(txt):
            return self._pred("notify", "personal", "Direct personal message asking for response.", 0.85)
        # 6) 群内问候
        if GREET.search(txt) and ctype == "group":
            return self._pred("digest", "greeting", "Casual greeting; read later.", 0.8)
        # 7) 转发链
        if fwd > 3:
            return self._pred("digest", "forward", "Forwarded chain; low priority.", 0.7)
        # 8) 业务账号
        if ctype == "business":
            return self._pred("notify", "business_update", "Verified business update.", 0.83)
        # 8.5) 群内时间敏感 / 管理类通知 -> notify（如校车提前、停水通知）
        if ctype == "group" and (TIME.search(txt) or ADMIN.search(txt)):
            return self._pred("notify", "event", "Time-sensitive or administrative group notice.", 0.84)
        # 9) 群消息
        if ctype == "group":
            return self._pred("digest", "event", "Group info; not urgent.", 0.75)
        # 10) 兜底
        return self._pred("digest", "unknown", "No strong signal; safe to defer.", 0.6)

    def extract_evidence(self, msg, ctx):
        sender = msg.get("sender_user_id") or msg.get("business_id")
        if not sender:
            return []
        hits = []
        for h in ctx.get("history", []):
            if h.get("sender_user_id") == sender or h.get("business_id") == sender:
                mid = h.get("message_id")
                if mid:
                    hits.append(mid)
        return hits[:2]

    def _opted_in(self, ctx, msg):
        uid = msg.get("user_id")
        bid = msg.get("business_id")
        for r in ctx.get("business_history", []):
            if r.get("user_id") == uid and r.get("business_id") == bid:
                if str(r.get("allows_promotions", "")).strip() == "1" and not r.get("promotions_opted_out_at"):
                    return True
        return False

    def _pred(self, action, mtype, reason, conf):
        return {"action": action, "message_type": mtype, "reason": reason,
                "confidence": conf}
