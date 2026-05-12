from __future__ import annotations

import re
from typing import Iterable

from ..models.models import ExternalDependency


class DependencyExtractor:
    _URL = re.compile(r"(?i)\bhttps?://[^\s\)\]）】\}<>\"']+")
    _IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
    _DOMAIN = re.compile(r"(?i)\b([a-z0-9][a-z0-9-]{0,62}\.)+(com|cn|net|org|io|gov|edu|co|info|xyz)\b")
    _QUOTED = re.compile(r"[《“\"\[]\s*([^《》“”\"\[\]]{2,40})\s*[》”\"\]]")
    _INTEGRATION = re.compile(
        r"(?i)(?:对接|接入|集成|调用|依赖|使用|访问|通过|与|从|向)\s*([\w\u4e00-\u9fff][\w\u4e00-\u9fff_\-]{1,39})\s*(?:系统|平台|服务|接口|api|sdk|库|组件|中间件|数据库)"
    )
    _PROTOCOL = re.compile(r"(?i)\b(https?|wss?|tcp|udp|grpc|rest|soap|sftp|ftp|smtp|imap|mqtt|snmp)\b")
    _UPPER_ABBR = re.compile(r"\b[A-Z][A-Z0-9_\-]{1,14}\b")

    _KNOWN: dict[str, str] = {
        "redis": "middleware",
        "kafka": "middleware",
        "rabbitmq": "middleware",
        "elasticsearch": "middleware",
        "opensearch": "middleware",
        "mysql": "database",
        "postgresql": "database",
        "oracle": "database",
        "sqlserver": "database",
        "mongodb": "database",
        "hadoop": "platform",
        "spark": "platform",
        "flink": "platform",
        "kubernetes": "platform",
        "docker": "platform",
        "ldap": "identity",
        "oauth": "identity",
        "oidc": "identity",
        "saml": "identity",
        "jwt": "identity",
        "prometheus": "observability",
        "grafana": "observability",
        "zabbix": "observability",
        "wechat": "external_platform",
        "微信": "external_platform",
        "alipay": "external_platform",
        "支付宝": "external_platform",
        "钉钉": "external_platform",
        "飞书": "external_platform",
        "lark": "external_platform",
        "aws": "cloud",
        "azure": "cloud",
        "gcp": "cloud",
        "阿里云": "cloud",
        "腾讯云": "cloud",
    }

    def extract(self, text: str) -> list[ExternalDependency]:
        t = (text or "").strip()
        if not t:
            return []

        out: dict[str, ExternalDependency] = {}

        self._add_matches(out, t, self._URL, "url", 0.95)
        self._add_matches(out, t, self._DOMAIN, "domain", 0.85)
        self._add_matches(out, t, self._IP, "ip", 0.85)
        self._add_matches(out, t, self._PROTOCOL, "protocol", 0.75, group=1)
        self._add_matches(out, t, self._INTEGRATION, "external_system", 0.7, group=1)

        for term in self._find_known_terms(t):
            idx = self._index_of(t, term)
            self._add(out, term, self._KNOWN.get(term, "external_system"), self._snippet(t, idx), 0.8)

        for m in self._QUOTED.finditer(t):
            name = (m.group(1) or "").strip()
            if not name:
                continue
            idx = m.start(1)
            self._add(out, name, self._guess_type_from_context(t, idx), self._snippet(t, idx), 0.55)

        for m in self._UPPER_ABBR.finditer(t):
            name = (m.group(0) or "").strip()
            if len(name) < 2:
                continue
            idx = m.start(0)
            typ = self._guess_type_from_context(t, idx) or "abbr"
            self._add(out, name, typ, self._snippet(t, idx), 0.35)

        return list(out.values())

    def _add_matches(
        self,
        out: dict[str, ExternalDependency],
        text: str,
        pattern: re.Pattern,
        typ: str,
        confidence: float,
        group: int = 0,
    ) -> None:
        for m in pattern.finditer(text):
            name = (m.group(group) if group else m.group(0) or "").strip()
            if not name:
                continue
            idx = m.start(group) if group else m.start(0)
            self._add(out, name, typ, self._snippet(text, idx), confidence)

    def _add(self, out: dict[str, ExternalDependency], name: str, typ: str, evidence: str, confidence: float) -> None:
        n = (name or "").strip()
        if not n:
            return
        key = self._normalize_key(n)
        existing = out.get(key)
        if existing is not None:
            if confidence > (existing.confidence or 0.0):
                existing.type = typ
                existing.evidence = evidence
                existing.confidence = confidence
            return
        out[key] = ExternalDependency(name=n, type=typ, evidence=evidence, confidence=confidence)

    def _find_known_terms(self, text: str) -> Iterable[str]:
        for k in self._KNOWN.keys():
            if self._index_of(text, k) >= 0:
                yield k

    def _index_of(self, text: str, needle: str) -> int:
        if any(ord(ch) > 127 for ch in needle):
            return text.find(needle)
        return text.lower().find(needle.lower())

    def _normalize_key(self, name: str) -> str:
        t = (name or "").strip()
        if any(ord(ch) > 127 for ch in t):
            return t
        return re.sub(r"[\s_\-]+", "", t.lower())

    def _snippet(self, text: str, idx: int) -> str:
        if not text:
            return ""
        at = max(0, idx)
        start = max(0, at - 40)
        end = min(len(text), at + 80)
        sub = text[start:end]
        return sub.replace("\r", " ").replace("\n", " ").strip()

    def _guess_type_from_context(self, text: str, idx: int) -> str:
        if not text:
            return "external_system"
        start = max(0, idx - 24)
        end = min(len(text), idx + 24)
        ctx = text[start:end].lower()
        if "sdk" in ctx or "库" in ctx or "library" in ctx:
            return "library"
        if "api" in ctx or "接口" in ctx or "rest" in ctx or "soap" in ctx:
            return "api"
        if "数据库" in ctx or "db" in ctx or "mysql" in ctx or "oracle" in ctx:
            return "database"
        if "消息" in ctx or "mq" in ctx or "kafka" in ctx or "rabbit" in ctx:
            return "middleware"
        if "第三方" in ctx or "外部" in ctx or "对接" in ctx or "集成" in ctx:
            return "external_system"
        return "external_system"

