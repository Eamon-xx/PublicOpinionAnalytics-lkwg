from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


from public_opinion.normalize import normalize_comments


SAMPLE_CSV = """序号,上级评论ID,评论ID,用户ID,用户名,用户等级,性别,评论内容,评论时间,回复数,点赞数,个性签名,IP属地,是否是大会员,头像
1,,c1,u1,用户甲,5,男,"第一行
第二行",2026-05-22 00:00:01,3,10,,浙江,否,https://example.com/a.jpg
2,c1,c2,u2,用户乙,6,保密,顶,2026-05-22 00:00:02,0,5,签名,江苏,是,https://example.com/b.jpg
3,c1,c2,u2,用户乙,6,保密,重复评论,2026-05-22 00:00:03,0,6,签名,江苏,是,https://example.com/b.jpg
"""


class NormalizeCommentsTests(unittest.TestCase):
    def test_normalize_comments_parses_multiline_csv_and_deduplicates_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "remark.csv"
            csv_path.write_text(SAMPLE_CSV, encoding="utf-8")

            comments = normalize_comments(csv_path)

        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0].comment_id, "c1")
        self.assertEqual(comments[0].comment_text_raw, "第一行\n第二行")
        self.assertEqual(comments[0].comment_text_clean, "第一行 第二行")
        self.assertTrue(comments[0].is_root)
        self.assertFalse(comments[1].is_root)
        self.assertTrue(comments[1].is_direct_reply_to_root)
        self.assertEqual(comments[1].reply_depth, 1)
        self.assertEqual(comments[1].like_count, 5)


if __name__ == "__main__":
    unittest.main()
