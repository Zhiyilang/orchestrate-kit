"""通用解题引擎。

换一道新题时，只改 problems/ 下的具体实现类（实现 Problem 接口），
本引擎 + orchestrate_kit 内的 loader / verifier / agent / log_utils 全部复用。

用法：
    python solve.py                      # 离线启发式跑 dataset/messages.csv
    ORC_MODE=llm python solve.py        # 用 LLM（需 OPENAI_API_KEY）
"""
import os
import csv

from orchestrate_kit import loader, agent, verifier, log_utils

OUT_COLS = ["message_id", "action", "message_type", "reason",
            "confidence", "evidence_message_ids"]


def run(problem, dataset_dir, out_path, mode="offline", log_path=None):
    log = log_utils.get_logger(log_path)
    log.info("START", "problem=%s mode=%s dataset=%s" % (problem.name, mode, dataset_dir))

    msgs = loader.load_messages(dataset_dir)
    ctx = loader.load_context(dataset_dir, problem.extra_context())
    valid_ev = {r.get("message_id", "") for r in ctx.get("history", [])}

    rows = []
    for m in msgs:
        pred = agent.propose(problem, m, ctx, mode, log)
        pred = verifier.verify(pred, problem.allowed_actions,
                               problem.allowed_types, valid_ev)
        rows.append({
            "message_id": m.get("message_id", ""),
            "action": pred["action"],
            "message_type": pred["message_type"],
            "reason": pred["reason"],
            "confidence": pred["confidence"],
            "evidence_message_ids": pred["evidence_message_ids"],
        })

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()
        w.writerows(rows)

    log.info("DONE", "wrote %d rows -> %s" % (len(rows), out_path))
    return rows


if __name__ == "__main__":
    from problems.whatsapp_router import WhatsAppRouter

    HERE = os.path.dirname(os.path.abspath(__file__))
    prob = WhatsAppRouter()
    out = run(prob,
              os.path.join(HERE, "dataset"),
              os.path.join(HERE, "dataset", "output.csv"),
              mode=os.environ.get("ORC_MODE", "offline"))
    print("produced", len(out), "rows")
