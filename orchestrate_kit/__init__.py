"""orchestrate-kit — 可复用的 HackerRank Orchestrate 24 小时解题骨架。

设计原则（= 我们全部项目的 prove-then-act 架构）：
  模型负责理解与提议，确定性代码负责裁决与举证。
换一道新题时，只改 problems/ 下的具体实现，loader / verifier / agent / solve 全部复用。
"""
__version__ = "0.1.0"
