from __future__ import annotations

import unittest

from web_demo.services.fast_path_service import select_fast_path_citations
from web_demo.services.kb_service import retrieve_citations


class FastPathRelevanceTests(unittest.TestCase):
    def _select(self, question: str):
        retrieved = retrieve_citations(question, top_k=4)
        selected = select_fast_path_citations(
            question=question,
            citations=retrieved,
            low_confidence=False,
            rule=None,
            session_has_history=False,
        )
        return retrieved, selected

    def test_biological_waste_does_not_turn_into_incubator_answer(self) -> None:
        retrieved, selected = self._select("生物实验废弃物应如何分类处置？")

        self.assertTrue(selected)
        self.assertIn(selected[0].kb_id, {item.kb_id for item in retrieved})
        self.assertIn("生物废弃物", selected[0].title)
        self.assertNotIn("培养箱", selected[0].title)

    def test_high_voltage_precheck_keeps_high_voltage_context(self) -> None:
        retrieved, selected = self._select("高压电源使用前要检查什么？")

        self.assertTrue(selected)
        self.assertIn(selected[0].kb_id, {item.kb_id for item in retrieved})
        self.assertIn("高压电源", selected[0].title)
        self.assertNotIn("延长线", selected[0].title)

    def test_hplc_question_keeps_liquid_chromatography_context(self) -> None:
        retrieved, selected = self._select("使用高效液相色谱仪(HPLC)有哪些安全注意事项？")

        self.assertIn("hplc", retrieved[0].title.lower())
        self.assertTrue(selected)
        self.assertIn("hplc", selected[0].title.lower())
        self.assertNotIn("gc-ms", selected[0].title.lower())

    def test_biosafety_cabinet_question_keeps_cabinet_operation_context(self) -> None:
        retrieved, selected = self._select("使用生物安全柜时需要注意哪些操作规范？")

        self.assertIn("生物安全柜", retrieved[0].title)
        self.assertTrue(selected)
        self.assertIn("生物安全柜", selected[0].title)
        self.assertNotIn("手持uv灯", selected[0].title.lower())

    def test_muffle_furnace_question_retrieves_muffle_furnace(self) -> None:
        retrieved, selected = self._select("使用马弗炉时需要注意哪些安全事项？")

        self.assertIn("马弗炉", retrieved[0].title)
        self.assertTrue(selected)
        self.assertIn("马弗炉", selected[0].title)

    def test_power_outage_question_retrieves_outage_procedure(self) -> None:
        retrieved, selected = self._select("实验室突然停电应该怎么处理？")

        self.assertIn("停电", retrieved[0].title)
        self.assertTrue(selected)
        self.assertIn("停电", selected[0].title)


if __name__ == "__main__":
    unittest.main()
