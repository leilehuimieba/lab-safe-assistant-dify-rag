from __future__ import annotations

import unittest

from web_demo.services.answer_service import append_truncation_notice, looks_truncated


class TruncationHeuristicTests(unittest.TestCase):
    def test_flags_answer_cut_off_mid_word(self) -> None:
        self.assertTrue(looks_truncated("氢氧化钠固体容易吸收空气中的水分和二氧化"))

    def test_does_not_flag_answer_ending_on_period(self) -> None:
        self.assertFalse(looks_truncated("请戴好手套和护目镜。"))

    def test_does_not_flag_answer_ending_on_question_or_exclamation(self) -> None:
        self.assertFalse(looks_truncated("是否已确认通风柜正常工作？"))
        self.assertFalse(looks_truncated("禁止将水倒入浓硫酸中！"))

    def test_empty_answer_is_not_flagged(self) -> None:
        self.assertFalse(looks_truncated(""))
        self.assertFalse(looks_truncated("   "))

    def test_does_not_flag_closing_offer_bullet_list(self) -> None:
        # DeepSeek's common sign-off style: a complete answer followed by an
        # unpunctuated "want more on X/Y/Z?" list -- not truncation.
        answer = (
            "皮肤接触：脱去污染衣物并用水清洗。"
            "如果你愿意，我还可以进一步补充：\n"
            "-**实验室使用丙酮的注意事项**\n"
            "-**工业环境下的安全规范**\n"
            "-**丙酮废液如何处理**"
        )
        self.assertFalse(looks_truncated(answer))

    def test_does_not_flag_offer_clause_ending_in_period(self) -> None:
        # Real EV-004 case: the offer-to-elaborate clause is itself a complete,
        # properly punctuated sentence, even though the list item right before
        # it has no punctuation of its own. Only the actual last character
        # (here "。") should matter.
        answer = (
            "-起火：可用二氧化碳、干粉灭火器灭火"
            "如果你愿意，我还可以进一步整理成“实验室使用乙醚安全操作规程”简明版。"
        )
        self.assertFalse(looks_truncated(answer))

    def test_does_not_flag_offer_clause_ending_in_closing_quote(self) -> None:
        # Real EV-045 case: offer clause ends on a closing Chinese quote with
        # no following period.
        answer = (
            "-金属火灾"
            "如果你愿意，我也可以帮你整理成一张“实验室火灾-灭火器对应表”"
        )
        self.assertFalse(looks_truncated(answer))


class TruncationNoticeTests(unittest.TestCase):
    def test_appends_notice_once(self) -> None:
        answer = "请戴好手套和护目镜。"
        with_notice = append_truncation_notice(answer)
        self.assertIn(answer, with_notice)
        self.assertIn("可能因生成长度限制被截断", with_notice)

    def test_does_not_duplicate_notice(self) -> None:
        once = append_truncation_notice("请戴好手套和护目镜。")
        twice = append_truncation_notice(once)
        self.assertEqual(once, twice)

    def test_empty_answer_returns_bare_notice(self) -> None:
        self.assertIn("可能因生成长度限制被截断", append_truncation_notice(""))


if __name__ == "__main__":
    unittest.main()
