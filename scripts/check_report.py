"""检查Word报告的基础结构，以及可选HTML简介版的未替换槽位；不判断语义或视觉。"""

import argparse
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile


def read_docx_text(path: Path) -> str:
    try:
        with ZipFile(path) as package:
            types = ET.fromstring(package.read("[Content_Types].xml"))
            rels = ET.fromstring(package.read("_rels/.rels"))
            root = ET.fromstring(package.read("word/document.xml"))
    except (OSError, BadZipFile, KeyError, ET.ParseError, RuntimeError) as exc:
        raise ValueError("DOCX无法读取或结构无效（文件包或XML损坏）") from exc

    ct = "{http://schemas.openxmlformats.org/package/2006/content-types}"
    pr = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    office_rels = {
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
        "http://purl.oclc.org/ooxml/officeDocument/relationships/officeDocument",
    }
    if (
        types.tag != ct + "Types" or rels.tag != pr + "Relationships"
        or not any(
            node.get("PartName") == "/word/document.xml"
            and node.get("ContentType") ==
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
            for node in types.findall(ct + "Override")
        )
        or not any(
            node.get("Type") in office_rels
            and node.get("Target") in {"word/document.xml", "/word/document.xml"}
            and node.get("TargetMode", "Internal") == "Internal"
            for node in rels.findall(pr + "Relationship")
        )
    ):
        raise ValueError("DOCX缺少有效的正文类型声明或包入口")

    namespaces = (
        "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "http://purl.oclc.org/ooxml/wordprocessingml/main",
    )
    word_ns = next(("{" + ns + "}" for ns in namespaces
                    if root.tag == "{" + ns + "}document"), None)
    if word_ns is None:
        raise ValueError("DOCX正文XML根节点无效")
    body = root.find(word_ns + "body")
    if body is None:
        raise ValueError("DOCX缺少Word正文")

    # 按命名空间提取可见正文，不依赖w前缀；XML注释、属性和字段指令不算正文。
    parts = []
    for node in body.iter():
        if node.tag == word_ns + "t":
            parts.append(node.text or "")
        elif node.tag in {word_ns + "p", word_ns + "br", word_ns + "cr"}:
            parts.append("\n")
        elif node.tag == word_ns + "tab":
            parts.append("\t")
    text = "".join(parts)
    if not text.strip():
        raise ValueError("Word正文为空或没有可检查的文字")
    return text


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--docx", required=True)
parser.add_argument("--html")
args = parser.parse_args()

errors: list[str] = []
docx_path = Path(args.docx)
docx_text = ""
if not docx_path.is_file():
    errors.append("Word文件不存在")
else:
    try:
        docx_text = read_docx_text(docx_path)
    except ValueError as exc:
        errors.append(str(exc))

if docx_text:
    required = [
        "AI 工具使用说明",
        "作品简介与基本信息",
        "制作流程与关键协作事件",
        "制作流程总览",
        "制作环节及任务",
        "使用的 AI / 工具",
        "AI / 工具所承担的工作",
        "小组成员的工作",
        "产出与当前状态",
        "链接或素材",
        "关键协作事件",
        "可复用方法与关键认识",
        "未解决问题与下一步行动",
        "提交前核对",
    ]
    for heading in required:
        if heading not in docx_text:
            errors.append(f"Word缺少必要结构：{heading}")

    forbidden = [
        "阶段性复盘",
        "最终复盘",
        "总结复盘",
        "报告类型",
        "制作路径总览",
        "制作路径与关键协作事件",
    ]
    for phrase in forbidden:
        if phrase in docx_text:
            errors.append(f"Word仍有已停用表述：{phrase}")

    if re.search(r"【\s*(填写|由学生确认)", docx_text):
        errors.append("Word仍有方括号填写提示")

if args.html:
    html_path = Path(args.html)
    if not html_path.is_file():
        errors.append("HTML文件不存在")
    else:
        try:
            html = html_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append("HTML无法读取或不是有效UTF-8文本")
            html = ""
        if not html.strip():
            errors.append("HTML文件为空")
        if not re.search(r"<html\b", html, re.I) or not re.search(r"</html>", html, re.I):
            errors.append("HTML结构不完整")
        if re.search(r"\{\{[^{}]+\}\}|__[A-Z][A-Z0-9_]*__", html):
            errors.append("HTML存在未替换槽位")
        if "viewport" not in html:
            errors.append("HTML缺少移动端viewport声明")

print(
    json.dumps(
        {
            "errors": errors,
            "scope": "仅Word基础结构、停用表述和可选HTML槽位检查；内容准确性、证据、语义与视觉需另查",
        },
        ensure_ascii=False,
        indent=2,
    )
)
raise SystemExit(bool(errors))
