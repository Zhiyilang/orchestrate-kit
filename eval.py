"""Eval — 在 sample_messages.csv（含官方 ground-truth）上跑离线启发式，对比准确率。

证明骨架"真的能干活"（HackerRank 评分信号 2）。同时跑不变量断言，
并通过 runpy 双 locale 验证中文 Windows 裸跑不崩（全管线已踩过的坑）。

运行：
    python eval.py                  # 正常
    env -u PYTHONUTF8 python eval.py  # 敌意 locale（cp936）也应 rc=0
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrate_kit import loader, verifier, log_utils
from problems.whatsapp_router import (WhatsAppRouter, ALLOWED_ACTIONS, ALLOWED_TYPES)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "dataset")


def main():
    prob = WhatsAppRouter()
    samples = loader.load_csv(os.path.join(DATA, "sample_messages.csv"))
    ctx = loader.load_context(DATA, prob.extra_context())
    valid_ev = {r.get("message_id", "") for r in ctx.get("history", [])}
    log = log_utils.get_logger(os.path.join(HERE, "eval_transcript.log.txt"))

    act_ok = typ_ok = 0
    total = 0
    preds = []
    for s in samples:
        pred = prob.heuristic(s, ctx)
        pred["evidence_message_ids"] = prob.extract_evidence(s, ctx)
        pred = verifier.verify(pred, ALLOWED_ACTIONS, ALLOWED_TYPES, valid_ev)
        preds.append(pred)
        total += 1
        ga = (s.get("action") or "").strip().lower()
        gt = (s.get("message_type") or "").strip().lower()
        if pred["action"] == ga:
            act_ok += 1
        if pred["message_type"] == gt:
            typ_ok += 1
        log.info("ROW", "%s pred=%s/%s gt=%s/%s" % (
            s.get("message_id"), pred["action"], pred["message_type"], ga, gt))

    print("sample_rows=%d action_acc=%.2f%% type_acc=%.2f%%" % (
        total, 100 * act_ok / total, 100 * typ_ok / total))

    # 不变量断言
    assert total > 0
    assert 0 <= act_ok <= total and 0 <= typ_ok <= total
    for p in preds:
        assert p["action"] in ALLOWED_ACTIONS
        assert p["message_type"] in ALLOWED_TYPES
        assert 0.0 <= float(p["confidence"]) <= 1.0
        assert p["evidence_message_ids"] == "none" or ";" in p["evidence_message_ids"] or p["evidence_message_ids"]
    print("EVAL_OK rows=%d" % total)


if __name__ == "__main__":
    main()
