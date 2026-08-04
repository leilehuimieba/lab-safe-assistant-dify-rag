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

    def test_ether_spill_does_not_retrieve_needlestick_exposure(self) -> None:
        retrieved = retrieve_citations("乙醚洒在实验台上并有人感到头晕，应该怎么办？", top_k=4)

        self.assertTrue(retrieved)
        top_text = " ".join(
            [
                retrieved[0].title,
                retrieved[0].snippet,
                retrieved[0].source_title,
            ]
        )
        self.assertTrue("乙醚" in top_text or "泄漏" in top_text or "有机溶剂" in top_text)
        self.assertTrue("泄漏" in top_text or "洒漏" in top_text)
        self.assertTrue("泄漏" in retrieved[0].title or "洒漏" in retrieved[0].title)
        self.assertNotIn("针刺", top_text)
        self.assertNotIn("血液", top_text)

    def test_cryogenic_pressure_question_does_not_cite_gas_chromatography_sources(self) -> None:
        """低温容器超压不得引用"同样含压力/气瓶"的无关仪器条目。

        没有 cryogenic_liquid anchor 组时，"液氮罐压力异常升高"的 top1 是
        GC-MS 氢气载气条目，DSC 高压坩埚和 ICP-MS 钢瓶紧随其后——回答正文是
        低温处置，"参考依据"却指向色谱和量热仪，属于错误归因。
        """
        retrieved = retrieve_citations("液氮罐压力异常升高", top_k=4)

        self.assertTrue(retrieved)
        # 只断言前 3 条：format_citation_lines 默认也只展示 3 条“参考依据”。
        for item in retrieved[:3]:
            with self.subTest(kb_id=item.kb_id):
                text = f"{item.title} {item.source_title}"
                self.assertTrue(
                    any(term in text for term in ["液氮", "液氦", "杜瓦", "低温", "Cryogen", "cryogen"]),
                    f"non-cryogenic citation: {item.kb_id} / {item.title}",
                )
        all_text = " ".join(f"{item.title} {item.source_title}" for item in retrieved)
        for unrelated in ["GC-MS", "ICP-MS", "载气", "坩埚"]:
            self.assertNotIn(unrelated, all_text)

    def test_cryogenic_anchor_does_not_break_frostbite_retrieval(self) -> None:
        retrieved = retrieve_citations("液氮溅到手上造成冻伤怎么办", top_k=4)

        self.assertTrue(retrieved)
        self.assertTrue(
            any(term in retrieved[0].title for term in ["液氮", "低温", "杜瓦"]),
            retrieved[0].title,
        )


if __name__ == "__main__":
    unittest.main()
