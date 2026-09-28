# AI 协作与复盘 Coach

面向大学 AI 素养实践课的中文 Coach Skill。用于作品构思、路线决策、关键技术验证、跨工具排错与证据复盘，支持图片、视频、音乐与播客、前端应用、小游戏、Skill 和智能体等项目。

当前版本：**v0.2.0**。

## 一句话安装

复制下面的固定仓库链接，粘贴到支持从 GitHub 安装 Skill 的大模型或 Agent 中，并发送：

> 请帮我安装这个 Skill：https://github.com/yiyi1108/ai-collaboration-coach

本仓库的 `SKILL.md` 位于根目录，相关 `references`、`assets`、`scripts` 和 `agents` 均使用标准相对路径，便于支持 GitHub Skill 安装的工具直接识别。

> 平台必须具备读取 GitHub 仓库并安装 Skill 的能力；普通聊天模型如果没有文件安装权限，无法仅靠提示语完成安装。此时请使用下方 ZIP 安装包，或使用 `PORTABLE_PROMPT_ZH.md` 作为降级方案。

## ZIP 安装

- [下载最新版安装包](https://github.com/yiyi1108/ai-collaboration-coach/releases/latest/download/ai-collaboration-coach.zip)
- [查看全部版本](https://github.com/yiyi1108/ai-collaboration-coach/releases)

解压后保留完整的 `ai-collaboration-coach` 文件夹，并按平台的 Skill 导入方式加载文件夹或 ZIP。入口文件是 `SKILL.md`，不要只复制该文件。

## 直接开始

- “我没想法，喜欢摄影和推理，请帮我找一个适合小规模尝试的方向。”
- “我已经确定做这个，请先帮我处理最关键的实现问题。”
- “这是另一工具给的结果，与预期有这些差别，请帮我判断下一步。”
- “项目暂时到这里，请生成 AI 协作报告。”

报告默认交付中文 MD 详细版与固定模板 HTML 视觉摘要；事实范围、确认顺序和降级方式以 `SKILL.md` 为准。

## 核心结构

```text
SKILL.md                  # Skill 入口与运行规则
PORTABLE_PROMPT_ZH.md     # 不支持 Skill 安装时的便携降级提示
agents/openai.yaml        # Agent 展示与调用元数据
references/               # 构思、验证、领域方法、报告等按需参考
assets/                   # HTML 报告模板、图标与字体资源
scripts/check_report.py   # 报告交付检查脚本
licenses/                 # 第三方资源许可
```

## 验证边界

v0.2.0 已完成结构、引用与资源检查，以及独立模拟情境检查；尚未完成学生课堂公测或所有平台的兼容性验证。不同平台的联网、文件读取、代码执行和安装机制不同，因此安装能力与最终表现以实际平台为准。

## 许可

原创指令、脚本及原创模板代码采用 [MIT License](LICENSE)。字体、机构标志和外链资料不重新授予 MIT 许可，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 `licenses/`。

请勿在公开反馈中上传学生个人信息、私密聊天或未授权素材。
