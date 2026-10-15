"""数据加载层 — 通用 CSV 读取 + 上下文表加载。零依赖（仅 csv / os）。"""
import csv
import os


def load_csv(path):
    """读取任意 CSV 为 dict 列表；文件缺失返回空列表。"""
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_messages(dataset_dir):
    return load_csv(os.path.join(dataset_dir, "messages.csv"))


def load_context(dataset_dir, extra):
    """extra: {逻辑名: 文件名}。返回 {逻辑名: [dict,...]}。"""
    ctx = {}
    for name, fname in (extra or {}).items():
        p = os.path.join(dataset_dir, fname)
        if os.path.exists(p):
            ctx[name] = load_csv(p)
    return ctx
