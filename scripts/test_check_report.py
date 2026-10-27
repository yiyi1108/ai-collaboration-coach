"""维护用回归测试：临时合成报告只验证检查器，不代表真实学生经历或报告质量。"""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class ReportCheckerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "report.docx"
        with ZipFile(ROOT / "assets/ai-tool-use-guide-template.docx") as package:
            self.original = {name: package.read(name) for name in package.namelist()}
        self.parts = dict(self.original)
        root = ET.fromstring(self.parts["word/document.xml"])
        # 将完整模板所有填写槽替换为明确的模拟材料，保留原有栏目、表格和说明。
        for para in root.iter(W + "p"):
            nodes = list(para.iter(W + "t"))
            text = "".join(node.text or "" for node in nodes)
            if nodes and "【" in text:
                nodes[0].text = re.sub(r"【[^】]*】", "模拟测试材料（非真实学生经历）", text)
                for node in nodes[1:]:
                    node.text = ""
        self.parts["word/document.xml"] = ET.tostring(root, encoding="utf-8")

    def write_package(self):
        with ZipFile(self.path, "w") as package:
            for name, data in self.parts.items():
                package.writestr(name, data)

    def check(self, accepted, contains=None, html=None, write=True):
        if write:
            self.write_package()
        cmd = [sys.executable, str(ROOT / "scripts/check_report.py"), "--docx", str(self.path)]
        if html is not None:
            html_path = Path(self.tmp.name) / "report.html"
            html_path.write_bytes(html)
            cmd += ["--html", str(html_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertEqual(result.stderr, "")
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0 if accepted else 1, report)
        self.assertEqual(bool(report["errors"]), not accepted)
        if contains:
            self.assertIn(contains, "\n".join(report["errors"]))

    def test_filled_template(self):
        self.check(True)

    def test_unfilled_template(self):
        self.parts = self.original
        self.check(False, "填写提示")

    def test_missing_file(self):
        self.check(False, "不存在", write=False)

    def test_empty_file(self):
        self.path.write_bytes(b"")
        self.check(False, "结构无效", write=False)

    def test_not_zip(self):
        self.path.write_text("not a Word package", encoding="utf-8")
        self.check(False, "结构无效", write=False)

    def test_required_package_parts(self):
        for name in ("[Content_Types].xml", "_rels/.rels", "word/document.xml"):
            with self.subTest(part=name):
                data = self.parts.pop(name)
                self.check(False, "结构无效")
                self.parts[name] = data

    def test_naked_xml_zip(self):
        self.parts = {"word/document.xml": self.parts["word/document.xml"]}
        self.check(False, "结构无效")

    def test_malformed_xml(self):
        for name in ("[Content_Types].xml", "_rels/.rels", "word/document.xml"):
            with self.subTest(part=name):
                original = self.parts[name]
                self.parts[name] = b"<broken"
                self.check(False, "结构无效")
                self.parts[name] = original

    def test_invalid_entry(self):
        self.parts["_rels/.rels"] = self.parts["_rels/.rels"].replace(
            b'Target="word/document.xml"', b'Target="missing.xml"')
        self.check(False, "包入口")

    def test_invalid_content_type(self):
        self.parts["[Content_Types].xml"] = self.parts["[Content_Types].xml"].replace(
            b"wordprocessingml.document.main+xml", b"wordprocessingml.template.main+xml")
        self.check(False, "类型声明")

    def test_wrong_document_root(self):
        self.parts["word/document.xml"] = b"<document><body>text</body></document>"
        self.check(False, "根节点")

    def test_missing_body(self):
        self.parts["word/document.xml"] = ET.tostring(ET.Element(W + "document"))
        self.check(False, "缺少Word正文")

    def test_empty_and_whitespace_body(self):
        for text in ("", "  \n\t\u3000"):
            with self.subTest(text=repr(text)):
                root = ET.Element(W + "document")
                body = ET.SubElement(root, W + "body")
                para = ET.SubElement(body, W + "p")
                run = ET.SubElement(para, W + "r")
                ET.SubElement(run, W + "t").text = text
                self.parts["word/document.xml"] = ET.tostring(root)
                self.check(False, "正文为空")

    def test_arbitrary_xml_text_not_body_text(self):
        root = ET.Element(W + "document")
        body = ET.SubElement(root, W + "body")
        body.text = "AI 工具使用说明"
        body.append(ET.Comment("AI 工具使用说明"))
        self.parts["word/document.xml"] = ET.tostring(root)
        self.check(False, "正文为空")

    def test_missing_heading(self):
        self.parts["word/document.xml"] = self.parts["word/document.xml"].replace(
            "未解决问题与下一步行动".encode(), "后续事项".encode())
        self.check(False, "缺少必要结构")

    def test_old_report_term(self):
        root = ET.fromstring(self.parts["word/document.xml"])
        root.find(".//" + W + "t").text += "阶段性复盘"
        self.parts["word/document.xml"] = ET.tostring(root)
        self.check(False, "停用表述")

    def test_split_runs_and_different_prefix(self):
        root = ET.fromstring(self.parts["word/document.xml"])
        for run in list(root.iter(W + "r")):
            for node in list(run):
                if node.tag == W + "t" and node.text:
                    text = node.text
                    run.remove(node)
                    for char in text:
                        ET.SubElement(run, W + "t").text = char
        # ET使用ns0等前缀，且字符转义为数字实体；仍应完整读取标题。
        self.parts["word/document.xml"] = ET.tostring(root, encoding="ascii")
        self.check(True)

    def test_valid_html(self):
        self.check(True, html=b'<html><head><meta name="viewport"></head><body>ok</body></html>')

    def test_bad_html(self):
        cases = [
            (b"", "HTML文件为空"),
            (b'<html><meta name="viewport">', "HTML结构不完整"),
            (b'<html><meta name="viewport">{{TITLE}}</html>', "未替换槽位"),
            (b'<html><meta name="viewport">__TITLE__</html>', "未替换槽位"),
            (b'<html></html>', "viewport"),
            (b'\xff\xfe', "UTF-8"),
        ]
        for html, message in cases:
            with self.subTest(message=message):
                self.check(False, message, html=html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
