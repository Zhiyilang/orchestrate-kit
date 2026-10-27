# Voice / empty-text routing gap — measured, and why we stopped chasing it

Date: 2026-10-22. Status: **investigated, closed as unlearnable with the shipped features.**
Decision: **do not** tune `heuristic()` to flip this row. Recorded so nobody spends
another hour on it before the October round.

## The gap

`eval.py` on the only official ground truth (`dataset/sample_messages.csv`, 30 rows):

```
sample_rows=30 action_acc=96.67% type_acc=96.67%
full_gt=110 action=110/110 type=110/110
RESULT: 140 passed, 0 failed
```

29/30. The single miss is `sample_msg_042`:

| field | value |
|---|---|
| `media_type` | `voice` |
| `message_text` | `''` (empty) |
| `conversation_type` | `group` (`group_008`) |
| `sender_user_id` | `u_041` |
| `user_id` | `u_028` |
| **ground truth** | **`notify` / `urgent`** — *"A close contact sent a short urgent request that should interrupt the user."* |
| **our prediction** | `digest` / `personal` |

## Why it is not a bug in the classifier

`sample_msg_041` is the same message in every respect the classifier can see, and its
ground truth is the *opposite*:

| | `sample_msg_041` | `sample_msg_042` |
|---|---|---|
| sender | `u_041` | `u_041` (same) |
| group | `group_008` | `group_008` (same) |
| media | `voice` | `voice` (same) |
| text | `''` | `''` (same) |
| **ground truth** | `digest` / `personal` | `notify` / `urgent` |

Everything that differs is either unusable or noise:

1. **`evidence_message_ids` is sequential filler, not a signal.**
   `041→message_0046`, `042→message_0047`, `043→message_0048`, `044→message_0049`,
   `045→message_0050`, `046→message_0051`, `047→message_0052`, `048→message_0053`.
   Perfectly +1 per row. It cannot be used as a feature, and note `message_0047` is a
   *business* message from `business_004` — it has nothing to do with this group voice
   note, which confirms the column is generated, not curated.

2. **The sender→receiver relationship is identical for both rows.**
   Pair stats computed from `message_history.csv` + `message_events.csv`:

   ```
   u_024 <- u_041   n=1  replied=0  avg_rt=-    (message_0046: opened, 120 min, no reply)
   u_028 <- u_041   n=1  replied=0  avg_rt=-    (message_0035: opened, 120 min, no reply)
   ```

   One historical message each, neither replied to, same 120-minute reaction. There is no
   "close contact" signal that separates them, and the ground-truth wording ("close
   contact") therefore has **no measurable basis in the shipped data**.

3. **Time / DND does not separate them either.**
   `u_024` DND `00:00-06:30`, message at `11:09`; `u_028` DND `23:30-07:30`, message at
   `14:16`. Both well outside the do-not-disturb window.

4. **`voice_notes.csv` carries no usable feature** — only `voice_note_id,file_path`.
   No duration, no transcript. The "short" in "short urgent request" is not observable.

5. **The user profile points the wrong way.** `u_028` is *more* dismissive than `u_024`
   (`notifications_dismissed_30d` 45 vs `messages_opened_30d` 42 → `_user_dismissive()`
   is `True` for `u_028`, `False` for `u_024`), yet the ground truth demands *interrupting*
   `u_028` and *deferring* the more engaged `u_024`. Any engagement-based rule moves this
   row further from the label, not closer.

Conclusion: the label is **annotator variance on two feature-identical rows**. Fitting it
would require keying on `user_id`/`message_id`, i.e. memorising the answer key.

## Why we do not fit it anyway

* **Zero money value.** The August round is submitted and closed; 96.67% is final. The
  October round (starts 2026-10-24 20:30) ships a **new dataset**, so an August-fitted
  rule does not even transfer.
* **Negative transfer risk.** Rules tuned on 30 rows of noise degrade on the hidden
  labelled set, which is what actually scores.
* **It would trip the regression guard.** `dataset/baseline_aug.csv` (110 rows) is the
  frozen August output; `eval.py` asserts `gt_act == 110 and gt_typ == 110`. Any rule
  that moves a row turns the whole suite red and destroys the 140/140 claim — for one
  row of an already-closed round.

## What we verified and kept

* `media_type` **is** consumed by `heuristic()` (branch 1); `voice_notes.csv` /
  `images.csv` are intentionally *not* loaded because they expose no feature beyond
  `media_id`. This is a deliberate choice, not an oversight.
* Current voice policy (unchanged): business voice → `notify/business_update`;
  group voice with admin/time text → `notify/event`; resale → `mute|digest/promotion`;
  otherwise group voice → `digest/personal`. It is correct on 4/5 labelled media rows
  and on all 110 frozen rows.
* `env -u PYTHONUTF8 LC_ALL=C python eval.py` still returns rc=0 (hostile-locale safe).

## If the October dataset also ships voice/image

Re-run this analysis *before* tuning: check whether the ground truth separates
feature-identical rows. If it does not, the ceiling is the ceiling — spend the race time
on pipeline throughput and evidence quality instead, which the AI judge can actually see.
