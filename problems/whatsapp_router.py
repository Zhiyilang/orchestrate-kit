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
# 2026-10-17 夜彩排加固：一词多义修正（join/claim）、否定语境护栏、
# 凭据钓鱼新模式、改期/物流/反馈/公告模式、商家垃圾画像+用户参与画像分流。
PROMO = re.compile(r"\b(buy|offer|sale|discount|subscribe|win|prize|limited|book now|book today|shop|deal)\b"
                   r"|\b(special|exclusive|limited|flash) offer\b|\boffer (available|ends|valid|today)\b"
                   r"|\b(selling|for sale|second[- ]hand|pickup is near|pickup near)\b"
                   r"|\b(per person|per night|all[- ]in|tap below|swipe up)\b"
                   r"|\b\d{1,3}\s?% off\b|\bwon'?t wait\b|\bhurry\b|\bexpire soon\b|\blast chance\b"
                   r"|(rs|usd|\$|₹|€|£)\s?[\d,]+", re.I)
SCAM = re.compile(r"\b(verify|account suspended|otp|click here|password|congrat|lottery|inherit|urgent payment|转账|中奖|密码|验证码)\b"
                  r"|claim (your|the) (prize|reward|money|gift|bonus|winnings)", re.I)
# 凭据钓鱼：要验证码/登录码 + 索取动作（八月真题 QR/clearance 钓鱼的同族缺口）
PHISH = re.compile(r"\b(login|verification|security|one[- ]time|\d[- ]digit) code\b"
                   r"|\b(reply|send|share|enter|confirm)\b[^.!?]{0,40}\bcode\b", re.I)
URGENT = re.compile(r"\b(urgent|asap|immediately|deadline|overdue|eod|now|紧急|立刻)\b", re.I)
PAYMENT = re.compile(r"\b(payment|invoice|bill|due|overdue|refund|paid|账单|付款)\b", re.I)
# 物流状态更新（"order/packed/hub" 是履约通知，不是付款催办）
ORDER_STATUS = re.compile(r"\b(has been (packed|shipped|dispatched)|out for delivery|reach(ing)? the (local )?hub"
                          r"|expected to (reach|arrive)|tracking (id|number|link)|order ending \d+)\b", re.I)
# 会议改期/临时调动 = urgent
RESCHEDULE = re.compile(r"\b(pulled to|moved to|rescheduled|postponed|brought forward|pushed to|moved up|last[- ]minute)\b", re.I)
EVENT = re.compile(r"\b(meeting|event|invite|rsvp|session|class|appointment|会议|活动|邀请|预约)\b", re.I)
PERSONAL = re.compile(r"\b(mom|dad|family|bro|sis|call|catch up|how are you|在吗|妈妈|爸爸|家人|电话)\b", re.I)
# 群内闲聊/约球局——含 tonight 也不是 urgent
CASUAL = re.compile(r"\b(anyone (watching|going|up for)|no pressure|might start|if you (want|get a chance)"
                    r"|score thread|watch(ing)? the match|if you get (a chance|time))\b", re.I)
# 明确说"不着急/明天再说"的状态更新 → digest
DEFERRAL = re.compile(r"\b(tomorrow|no rush|nothing urgent|not urgent|later today|at your convenience|不急|稍后)\b", re.I)
GREET = re.compile(r"\b(good morning|good evening|hope|peace|vibes|早|晚安|好)\b", re.I)
# 售后反馈邀评（不是 promo，也不是要立即处理的 business_update）
FEEDBACK = re.compile(r"\b(thank you for choosing|we would love to hear|rate your|feedback (form|survey)|how did we do|review your experience)\b", re.I)
# 安全公告/防骗提醒（含 OTP/payment 字样但恰是反诈内容，先于 SCAM 判定）
ADVISORY = re.compile(r"\b(advisory|safety (tips|advisory)|never ask for|awareness|beware of|do not share)\b", re.I)
# 个人二手/社区转售
RESALE = re.compile(r"\b(selling|for sale|second[- ]hand|pickup is near|pickup near|photos for)\b", re.I)
# 否定护栏：命中词前 14 字符内有否定词则不成立（"Nothing urgent"/"这不是诈骗"）
NEG_GUARD = re.compile(r"\b(nothing|not|no|don'?t|never|isn'?t|aren'?t|without|neither|nor|并非|没有|无需|不是)\b[^.!?]{0,12}$", re.I)
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
                "business relationship and history. "
                "Hard rules: requests for login/verification codes are always scam; "
                "negated mentions ('nothing urgent', 'not a scam') are not signals; "
                "order-tracking updates are business_update, not payment; "
                "schedule changes ('pulled to 3', 'rescheduled') are urgent."
                % "|".join(ALLOWED_TYPES))

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

        # 0) 反诈/安全公告先行（含 OTP/payment 字样的 legit 公告先于诈骗判定）
        if ADVISORY.search(txt):
            if ctype == "business":
                return self._pred("digest", "business_update", "Safety advisory from a business; informational.", 0.75)
            return self._pred("digest", "event", "Safety advisory; informational.", 0.75)

        # 1) 媒体消息（图片/语音）离线无 OCR/ASR：文本信号优先，再按对话类型+上下文画像降级
        if media in ("image", "voice"):
            if ctype == "business":
                if self._biz_spam(ctx, msg):
                    return self._pred("mute", "spam", "Unverified business with spam signals; muted.", 0.85)
                if PROMO.search(txt):
                    if self._opted_in(ctx, msg):
                        return self._pred("digest", "promotion", "Promotional media; user opted into this business.", 0.7)
                    return self._pred("mute", "promotion", "Unsolicited promotional media; muted.", 0.8)
                if media == "voice":
                    return self._pred("notify", "business_update", "Voice note from a business; check promptly.", 0.7)
                return self._pred("notify", "business_update", "Media from a verified business; treat as update.", 0.8)
            if ctype == "group":
                if ADMIN.search(txt) or TIME.search(txt):
                    return self._pred("notify", "event", "Group media carrying an administrative/time-sensitive note.", 0.82)
                if RESALE.search(txt):
                    if self._user_dismissive(ctx, msg):
                        return self._pred("mute", "promotion", "Resale post; user dismisses most notifications.", 0.7)
                    return self._pred("digest", "promotion", "Peer resale post in a community; potentially useful.", 0.65)
                if media == "voice":
                    return self._pred("digest", "personal", "Voice note inside a group; personal, deferrable.", 0.7)
                return self._pred("digest", "event", "Media inside a group; safe to defer.", 0.7)
            return self._pred("digest", "unknown", "Media without text; deferred.", 0.6)

        # 2) 文本消息：商家垃圾画像（未验证 + 被举报/群发/域名不符）
        if ctype == "business" and self._biz_spam(ctx, msg):
            return self._pred("mute", "spam", "Unverified business with spam signals; muted.", 0.85)

        # 3) 凭据钓鱼（要登录码/验证码 + 索取动作）
        if PHISH.search(txt):
            return self._pred("mute", "scam", "Credential phishing pattern detected.", 0.93)

        # 4) 诈骗优先（否定语境护栏："Nothing urgent"/"这不是诈骗"不误伤）
        m = SCAM.search(txt)
        if m and not self._negated(txt, m):
            return self._pred("mute", "scam", "Likely scam/phishing pattern detected.", 0.92)

        # 5) 会议改期/临时调动 = urgent（先于付款，避免 "failed-payment screenshots" 抢判）
        if RESCHEDULE.search(txt):
            return self._pred("notify", "urgent", "Schedule change / last-minute shuffle.", 0.87)

        # 6) 促销：opt-in 用户才 digest；个人二手按用户参与画像；否则 mute
        if PROMO.search(txt):
            if self._opted_in(ctx, msg):
                return self._pred("digest", "promotion", "Promotional but user opted into this business.", 0.7)
            if RESALE.search(txt) or not msg.get("business_id"):
                if self._user_dismissive(ctx, msg):
                    return self._pred("mute", "promotion", "Resale post; user dismisses most notifications.", 0.7)
                return self._pred("digest", "promotion", "Peer resale post in a community; potentially useful.", 0.65)
            return self._pred("mute", "promotion", "Unsolicited promotion; muted.", 0.8)

        # 7) 物流履约状态（商家语境 = business_update，不是 payment）
        if ORDER_STATUS.search(txt):
            if ctype == "business":
                return self._pred("notify", "business_update", "Order fulfillment status from a business.", 0.85)
            return self._pred("notify", "payment", "Order/delivery status update.", 0.8)

        # 8) 售后反馈邀评 → digest（不打扰）
        if FEEDBACK.search(txt):
            return self._pred("digest", "business_update", "Post-purchase feedback request; no action needed.", 0.75)

        # 9) 紧急 / 付款（否定护栏）
        m = PAYMENT.search(txt)
        if m and not self._negated(txt, m):
            return self._pred("notify", "payment", "Time-sensitive payment/order update.", 0.88)
        m = URGENT.search(txt)
        if m and not self._negated(txt, m):
            return self._pred("notify", "urgent", "Urgent action or deadline mentioned.", 0.86)

        # 10) 群内闲聊（约球/求伴）含 tonight 也不是 urgent
        if CASUAL.search(txt):
            return self._pred("digest", "personal", "Casual social chat; no action needed.", 0.75)

        # 11) 明确不着急的状态更新
        if DEFERRAL.search(txt):
            return self._pred("digest", "personal", "Personal status update, explicitly not urgent.", 0.8)

        # 12) 群内问候（转发祝福链直接 mute）
        if GREET.search(txt) and ctype == "group":
            if fwd > 3 or re.search(r"\bforward(ing|ed)\b", txt, re.I):
                return self._pred("mute", "greeting", "Forwarded greeting/blessing chain; noise.", 0.75)
            return self._pred("digest", "greeting", "Casual greeting; read later.", 0.8)

        # 13) 转发链（fwd>3 一律 mute，先于事件/个人判定）
        if fwd > 3:
            return self._pred("mute", "forward", "Forwarded chain; noise.", 0.75)

        # 14) 事件
        if EVENT.search(txt):
            return self._pred("notify", "event", "Event/appointment the user likely needs.", 0.84)

        # 15) 个人
        if PERSONAL.search(txt):
            return self._pred("notify", "personal", "Direct personal message asking for response.", 0.85)

        # 16) 业务账号
        if ctype == "business":
            return self._pred("notify", "business_update", "Verified business update.", 0.83)

        # 17) 群内时间敏感 / 管理类通知 -> notify（如校车提前、停水通知）
        if ctype == "group" and (TIME.search(txt) or ADMIN.search(txt)):
            return self._pred("notify", "event", "Time-sensitive or administrative group notice.", 0.84)

        # 18) 群消息
        if ctype == "group":
            return self._pred("digest", "event", "Group info; not urgent.", 0.75)

        # 19) 兜底
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

    def _biz_spam(self, ctx, msg):
        """商家垃圾画像：未验证 + （被举报≥5 / 月群发>500 / 域名不符）。"""
        bid = msg.get("business_id")
        if not bid:
            return False
        for r in ctx.get("business", []):
            if r.get("business_id") == bid:
                verified = str(r.get("verified") or "0").strip() == "1"
                if verified:
                    return False
                try:
                    reports = int(r.get("user_reports_30d") or 0)
                    sent = int(r.get("messages_sent_30d") or 0)
                except ValueError:
                    return False
                dom = (r.get("official_domain") or "").strip()
                used = (r.get("domain_used_by_sender") or "").strip()
                dom_mismatch = bool(dom and used and dom.lower() != used.lower())
                return reports >= 5 or sent > 500 or dom_mismatch
        return False

    def _user_dismissive(self, ctx, msg):
        """用户参与画像：月关闭通知数 > 月打开数 → 低价值内容直接 mute。"""
        uid = msg.get("user_id")
        for r in ctx.get("users", []):
            if r.get("user_id") == uid:
                try:
                    opened = int(r.get("messages_opened_30d") or 0)
                    dismissed = int(r.get("notifications_dismissed_30d") or 0)
                except ValueError:
                    return False
                return dismissed > opened
        return False

    @staticmethod
    def _negated(txt, m):
        """命中词前 14 字符内有否定词 → 该命中不成立。"""
        pre = txt[max(0, m.start() - 14):m.start()]
        return bool(NEG_GUARD.search(pre))

    def _pred(self, action, mtype, reason, conf):
        return {"action": action, "message_type": mtype, "reason": reason,
                "confidence": conf}
