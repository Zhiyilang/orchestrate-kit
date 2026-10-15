"""AI 聊天记录日志 — 满足 Orchestrate 的 chat_transcript 提交要求。

AGENTS.md 要求 AI 编码工具把对话摘要追加到固定路径的 log.txt。
本模块统一接管日志，提交时把该文件作为 chat_transcript 上传即可。
"""
import os
import threading
from datetime import datetime


class Transcript:
    def __init__(self, path=None):
        if path is None:
            base = os.environ.get("USERPROFILE") or os.environ.get("HOME") or "."
            path = os.path.join(base, "hackerrank_orchestrate", "log.txt")
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._lock = threading.Lock()

    def info(self, stage, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = "[%s] %s: %s\n" % (ts, stage, msg)
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line)

    def event(self, **kw):
        self.info("EVENT", " | ".join("%s=%s" % (k, v) for k, v in kw.items()))


def get_logger(path=None):
    return Transcript(path)
