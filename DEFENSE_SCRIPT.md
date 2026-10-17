# HackerRank Orchestrate — AI 评委 30 分钟答辩逐字稿

> 用法：10-25 开赛前每天读两遍，**念熟到不过脑**。答辩时评委是 AI，语速稳定比流利更重要。
> 方括号 `[ ]` 是填空位：开赛拿到自己的项目后，把数字换上去（对照表见文末）。
> 铁律：每个论断带证据；不会就说不会，然后讲怎么查——AI 评委对"诚实+方法"给分，对编造零容忍。

---

## 0. 万能救场句型（卡壳时用，背熟这 5 句）

1. 想拖时间：*"That's a great question — let me answer it in two parts."*
2. 没听清：*"Could you rephrase the question, please?"*（AI 评委会换种问法，不扣分）
3. 真不会：*"I don't know the exact answer, but here's how I would find out: [步骤]."*
4. 答偏了被拉回：*"Good point — to come back to your question: [一句话重答]."*
5. 结束每个长答案：*"So in short: [一句话总结]."*（帮 AI 评委抓得分点）

---

## 1. Opening — 30 秒自我介绍（评委必先问 "Introduce yourself and your project"）

> "Hi, thanks for the opportunity. I'm Zhiyilang, an RPA and AI agent developer based in Shanghai. My project is [PROJECT_NAME] — [ONE_SENTENCE_DESCRIPTION]. The core idea is simple: **the model proposes, and deterministic code decides.** The LLM handles understanding and explanation; a rule-based adjudication layer handles every decision that matters, and every decision ships with a receipt citing the evidence it used. The agent runs fully offline with zero dependencies, and it passes [N] automated assertions including hostile-locale scenarios. I built it in 24 hours using Codex, and I have the full AI chat log as the build record."

**中文注释**：最后一句主动提 Codex+chat log——直接踩中两个评分点（$5k 专项资格 + "如何指挥 AI 工具"）。

---

## 2. 十问逐字稿

### Q1. What problem does your agent solve, and why does it matter?（Impact）

> "It solves [THE_PROBLEM] for [WHO]. Before this agent, [THE_PAIN — one sentence with a number or a scene]. My agent takes [INPUT] and produces [OUTPUT] — for example, [ONE_CONCRETE_EXAMPLE_FROM_THE_RUN]. The reason it matters: [WHY_NOW — one sentence]. I validated it on the real dataset the challenge provided — [N] rows processed, [RESULT_SUMMARY] — not a toy example."

### Q2. Why did you split the architecture this way? What does the model do vs. the deterministic code?

> "The split follows one principle: **let the model describe, let deterministic code decide.** The model is excellent at understanding ambiguous input — intent, preferences, natural-language explanation. But it must never be the last word on anything that matters: a classification, a routing decision, a payment, a flag. So every model output passes through an adjudication layer that checks format, verifies citations against source rows, and recomputes any numbers. If a check fails, the output is downgraded or dropped — it never silently passes. This is the same pattern I use across all my open-source projects."

### Q3. What happens when the model is wrong?（必问）

> "Three layers of defense. First, **prevention**: the prompt demands structured output with evidence IDs, and the adjudicator rejects anything malformed. Second, **detection**: my assertion suite covers the failure paths explicitly — bad input, empty input, missing evidence, contradictory citations — currently [N] assertions, all passing, including a hostile-locale run with UTF-8 disabled. Third, **degradation**: if the LLM is unavailable or fails, the agent falls back to a deterministic heuristic engine, so the demo never breaks — I demonstrated that fallback in my video. A wrong answer is treated as data to validate, never as a conclusion."

### Q4. How do you verify the agent actually works?（必问）

> "By evidence, not by claim. First, the assertion suite: `python eval.py` runs [N] checks offline — [LIST_2-3_AREAS: rule hits / patch generation / receipt structure / bilingual consistency]. Second, the run itself produces an output file — `output.csv` — with [N] real rows, and every row carries its evidence message IDs, so any single decision can be traced back to its source. Third, CI runs the suite across Python [VERSIONS]. Anyone can clone the repo and reproduce all of this in thirty seconds — no keys, no setup."

### Q5. What was the hardest engineering decision, and what trade-off did you make?

> "The hardest call was [DECISION — e.g., 'keeping the agent fully offline instead of calling a hosted model for every step']. I chose [CHOICE] over [ALTERNATIVE] because [REASON — auditability / reproducibility / zero cost]. The trade-off is [HONEST_COST — e.g., 'the heuristic engine is less fluent than a big model']. But for this use case, [WHY_THE_TRADE_IS_WORTH_IT — e.g., 'a wrong but confident answer is worse than a conservative correct one']. If I had more time, I would [NEXT_STEP]."

### Q6. In what situations would your solution fail?（主动讲=加分）

> "Let me be specific about failure modes, because documenting them is part of the engineering. First, [FAILURE_1 — e.g., 'inputs whose evidence is contradictory: the adjudicator will drop the decision and report low confidence rather than guess']. Second, [FAILURE_2 — e.g., 'very long inputs beyond the context window: currently truncated with a logged warning, not silently']. Third, [FAILURE_3 — e.g., 'domain shift: the rules encode assumptions about [DOMAIN], so a different domain needs new rules, not just a new prompt']. Each of these is covered by at least one assertion that pins the behavior — so the failure is visible, not hidden."

### Q7. Why didn't you use framework X?（LangChain 等）

> "I evaluated [FRAMEWORK] and chose zero-dependency standard library for three reasons. **Auditability**: every line that makes a decision is code I wrote and can point to — in a framework, the decision logic hides in abstractions. **Reproducibility**: the judges — and any user — can clone and run the whole agent in thirty seconds, offline, no dependency resolution, no supply-chain risk. **Debuggability under time pressure**: in a 24-hour build, every framework bug costs hours I didn't have. Frameworks shine for large teams and long-lived products; for a single auditable agent, the standard library won. That said, [FRAMEWORK]'s idea of [SPECIFIC_IDEA] is good, and my [MODULE] is essentially that idea, implemented transparently."

### Q8. How did you direct AI tools to build this?（Codex 专项核心题）

> "I used Codex as my build partner with a strict protocol. **First, I designed before prompting**: the architecture — loader, agent, adjudicator, receipts — was mine, decided up front. **Second, I built in slices**: each slice was a prompt with an explicit acceptance test, and I only moved on when the tests passed. **Third, I rejected unevidenced output**: any code that couldn't demonstrate its behavior with a run was rewritten, not patched. **Fourth, the AI chat log is the design record** — you can see every decision, every rejection, every iteration in it. The principle throughout: AI writes code, but I own the architecture and the verification. The full log is submitted with the project."

### Q9. If you had another 24 hours, what would you do first?

> "Two things, in order. First, [HIGHEST_VALUE_ITEM — e.g., 'a git-diff input mode, so the agent reviews changes instead of whole files — the real review workflow']. Second, [SECOND_ITEM — e.g., 'property-based tests on the adjudicator: generate adversarial inputs and assert the receipts stay consistent']. I would not add features — I would deepen the verification of what exists. A smaller agent I fully trust beats a bigger one I don't."

### Q10. Can this become a real product? What's next?

> "Yes, and the path is concrete. The open-source core is the reference implementation — developers adopt it, and it becomes the standard pattern for [DOMAIN]. The product layer is [PRODUCT_IDEA — e.g., 'a managed control plane: team policies, approval workflows, immutable audit logs'] sold to [BUYER]. Next step after this competition: [ONE_CONCRETE_STEP — e.g., 'run three pilots with real users and publish the failure-mode report']. The grant or prize money would fund exactly that: hardening the adjudicator and the first pilots."

---

## 3. 数字对照表（开赛后 5 分钟填完，答辩前只看这张表）

| 占位符 | 填什么 | 默认参考值（来自现成仓） |
|---|---|---|
| `[PROJECT_NAME]` | 你的项目名 | — |
| `[N] assertions` | 开赛日 eval.py 实测数 | kit 现成 30；别高报，现场可复现 |
| `[VERSIONS]` | CI 矩阵 | 照自己仓的 ci.yml 念 |
| `[N] rows` | output.csv 行数 | 跑完 solve.py 后数一下 |
| `[THE_PROBLEM]/[WHO]/[THE_PAIN]` | 开赛题目的用户与痛点 | 读题 30 分钟内写死 |
| `[DECISION]/[FAILURE_1-3]` | 你自己的真实决策与失败模式 | 构建期记笔记，答辩夜整理 |

## 4. 答辩前 10 分钟 checklist

- [ ] 数字对照表填完，念一遍（现场报错数字=直接失信）
- [ ] 逐字稿 Q1/Q3/Q4/Q8 念熟（这四问出现概率 100%）
- [ ] 终端开着：`python eval.py` 和 `python solve.py` 都能一键重跑（评委要求演示时 10 秒内开始）
- [ ] output.csv 打开在编辑器里（被问"证明它工作了"直接切窗口）
- [ ] AI chat log 文件路径记住（被问 Codex 使用直接报路径）
