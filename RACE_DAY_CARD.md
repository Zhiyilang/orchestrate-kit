# 🏁 HackerRank 开赛日速查卡（贴在显示器边，24h 限时赛）

> **赛制**：**10-24（下周六）20:30（北京）开赛**，24h。⚠️ 时区歧义已双源裁定：官方页 "8:30 PM CST" + Internshala "6:00 PM IST" 换算后同为 20:30 北京——曾误按 CDT 读成 10-25 09:30，差 13 小时。**20:00 前到位，宁可早等**。
> 本卡 = GOLDEN_PLAYBOOK.md 的命令级压缩版。
> 详细原理在 `GOLDEN_PLAYBOOK.md`，答辩逐字稿在 `DEFENSE_SCRIPT.md`——本卡只管**开赛后每一分钟做什么**。

---

## 0:00–1:00 起步四步（照做，不跳步）

```bash
cd orchestrate-kit

# ① 复制靶场改头换面（拿冠军 August 赛的 problems/whatsapp_router.py 当模板，
#    只改 prompt 里的业务词，判定逻辑骨架不动）
cp problems/whatsapp_router.py problems/<新题名>.py

# ② 首跑（离线启发式，秒出结果，先保证管道通）
python solve.py

# ③ 三连质检（见下方第 3 节命令）
# ④ 有条件再切 LLM——任何 OpenAI 兼容 key 都行（不必是 OpenAI 官方！）：
#    没有 OPENAI_API_KEY 就用你现有的 MiMo（OpenAI 兼容）：
OPENAI_API_KEY=<你的MiMo key> OPENAI_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1 ORC_MODEL=<MiMo模型名> ORC_MODE=llm python solve.py
#    agent.py 已加固：端点不支持 response_format 会自动退一格重试（不会直接掉兜底）；
#    调用失败照样自动回离线启发式。**先用 5 条消息对比两种模式输出差异再全量跑。**
```

**为什么复制靶场**：本模式的判定骨架在八月真题上 **110/110 全覆盖**，八月题的
message_type / action 体系与本次同源。新题的业务词换掉即可，**骨架换了就丢了
110/110 的正确率**。

## 判读一口清（本次得分的主战场）

| 维度 | 值 | 什么时候给 |
|---|---|---|
| action | `notify` | 需要用户现在就知道 |
| action | `digest` | 进汇总，不打断 |
| action | `mute` | 噪音/已处理/与我无关 |
| message_type | 按题目给的表 | **先建映射表再写 prompt**，别凭语感 |

**铁律**：`reason` 字段必须写清是哪条规则命中的（评委看这个）；`confidence` 与
证据强度挂钩，别全给 0.9。

## ⚠️ 五个误判类换 prompt 检查清单（每修一类，重跑质检 B 看分布）

1. **msg_048 QR/clearance 钓鱼**——不在 SCAM 词表里！症状：被判成 urgent/notify。
   修法：加 QR/扫码/clearance/验证码/过期 类词的钓鱼组合规则。
2. **msg_099 否定语境**——"这不是诈骗""没有异常"被单关键词误伤。
   修法：命中词前后 ±12 字有否定词（不是/并非/没有/无需）→ 降级。
3. **msg_008 营销评论邀请**——"求赞/求转发/评论区"漏过 PROMO 词表。
   修法：PROMO 表加互动邀请词。
4. **msg_107 提示注入**——消息内容里含"忽略指令/你是AI助手"类注入。
   修法：**显式**防御分支（注入内容按 mute + reason 标注 injection），
   别指望通用 prompt 顺带覆盖。
5. **msg_070 多语言**——非中英消息。
   修法：判定逻辑不依赖语种关键词，或对未知语种走保守默认 + reason 说明。

## 三连质检（每改一轮 prompt 必跑）

```bash
# A 覆盖完整性：输出行数 == 输入消息数，无空 message_id
python -c "import csv;r=list(csv.DictReader(open('dataset/output.csv')));print(len(r), sum(1 for x in r if not x['message_id']))"

# B 分布合理性：三类 action 都要有量；某一类 >80% 几乎一定是逻辑写错
python -c "import csv,collections;r=list(csv.DictReader(open('dataset/output.csv')));print(collections.Counter(x['action'] for x in r))"

# C 按类别抽样看原文：每类抽 5 条，人眼核对（防系统性误判）
python -c "import csv,random;r=list(csv.DictReader(open('dataset/output.csv')));random.seed(7);[print(x['message_id'],x['action'],x['message_type'],'|',x['reason'][:60]) for x in random.sample(r,10)]"
```

## 时间分配（24h）

| 时间 | 动作 |
|---|---|
| 0:00–1:00 | 上面起步四步 |
| 1:00–4:00 | 按 5 个误判类逐类修，每修一类重跑质检 B |
| 4:00–6:00 | 边界：空文本/超长/未知 conversation_type/emoji/媒体消息 |
| 6:00–8:00 | 定稿 dataset/output.csv；最终分布+典型样本写进 README（评委看） |
| 8:00 前 | **提交 + 备份 dataset/output.csv 进仓** |
| 剩余 | 打磨 DEFENSE_SCRIPT.md 的 10 问（Q1/Q3/Q4/Q8 高概率；Q8=Codex $5k 专项核心） |

## 提交前 3 分钟检查

- [ ] dataset/output.csv 行数 == 消息总数（A 质检）
- [ ] 三类 action 分布都在 5%–95% 之间（B 质检）
- [ ] reason 全部非空、是人话（评委直接读）
- [ ] dataset/output.csv 已 `git add` 并推送（防提交页抽风）
- [ ] 报名时勾选的赛道与提交内容一致

## 翻车急救

| 症状 | 第一反应 |
|---|---|
| solve.py 崩 | 看 dataset 新字段名是否与 loader 假设不符（新题常加列） |
| 分布一类独大 | 回退到上一版 prompt，用 git diff 找改坏的那条 |
| LLM 超时/限流 | 立刻切回离线模式，别在比赛日 debug key |
| 题目要求与八月差异大 | **以本次题目 README 为准**，靶场只借骨架不借结论 |

生成时间：2026-10-17 · 开赛时间以官方邮件为准（**10-24 20:30 北京**，双源裁定口径；若邮件显示不同时间，以邮件为准并立即按邮件时间前 1 小时到位）。
