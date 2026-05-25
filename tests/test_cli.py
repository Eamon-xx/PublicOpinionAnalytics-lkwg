import unittest


from public_opinion.cli import build_parser


class CliParserTests(unittest.TestCase):
    def test_cli_shows_help_and_subcommands(self) -> None:
        parser = build_parser()

        help_text = parser.format_help()

        self.assertIn("normalize", help_text)
        self.assertIn("prepare-model", help_text)
        self.assertIn("merge-labels", help_text)
        self.assertIn("aggregate", help_text)
        self.assertIn("build-batches", help_text)
        self.assertIn("run-batch-label", help_text)
        self.assertIn("validate-labels", help_text)


if __name__ == "__main__":
    unittest.main()
