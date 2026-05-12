from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.dependency_catalog import DependencyCatalog
from app.core.module_splitter import split_text_into_modules


class DependencyMappingTest(unittest.TestCase):
    def test_maps_module_to_external_system_and_api(self):
        project_root = Path(__file__).resolve().parents[2]
        deps_json = project_root / "work" / "input" / "dependencies" / "external_systems.placeholder.json"
        catalog = DependencyCatalog.load(deps_json)

        text = "\n".join(
            [
                "1. 支付模块",
                "对接支付宝(Alipay)接口，完成支付下单。",
                "调用 /v1/pay 创建支付，返回 tradeNo。",
                "",
                "2. 登录模块",
                "通过统一认证中心获取 token。",
            ]
        )
        modules = split_text_into_modules(text)
        pay = next((x for x in modules if x.get("module") == "支付模块"), None)
        self.assertIsNotNone(pay)
        deps = catalog.match_systems(pay.get("text") or "")
        ids = [d.get("id") for d in deps]
        self.assertIn("PAY_ALIPAY", ids)
        alipay = next((d for d in deps if d.get("id") == "PAY_ALIPAY"), None)
        self.assertIsNotNone(alipay)
        api_ids = [a.get("id") for a in (alipay.get("apis") or []) if isinstance(a, dict)]
        self.assertIn("ALIPAY_PAY_CREATE", api_ids)


if __name__ == "__main__":
    unittest.main()
