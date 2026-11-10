from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorkflowContractTests(unittest.TestCase):
    def test_default_pr_review_does_not_authorize_untrusted_execution(self):
        process = ROOT / "processes" / "pr-review"
        self.assertIn("default: true", (process / "meta.yaml").read_text())
        criteria = (process / "criteria.md").read_text()
        self.assertIn("Review by static inspection by default", criteria)
        self.assertIn("separate", criteria)
        self.assertIn("explicit operator authorization", criteria)
        self.assertNotIn("Run targeted compilation/tests when feasible", criteria)
        self.assertNotIn("requires `--tags=intest`, use it", criteria)
        self.assertNotIn("enabling failpoints, ensure they are disabled afterward", criteria)
        self.assertIn("Use static inspection only", (ROOT / "prompts" / "reviewer.prompt").read_text())

    def test_skill_language_and_output_contract(self):
        content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        markers = [
            "Infer the review-output language from the user prompt that triggers",
            "Do not ask a separate language-preference question",
            "Write artifacts to the workspace root",
            "second_opinion_meta.json",
            "second_opinion.md",
            "second_opinion.json",
            "second_opinion_github_comments.json",
            "ask whether to post only after review outputs are complete",
            "use `gh` CLI; if `gh` is unavailable or unauthenticated, fail posting explicitly.",
            "prefer inline/file comments over general comments",
            "Chat findings are supplementary; they do not replace required file outputs.",
        ]
        for marker in markers:
            self.assertIn(marker, content, f"Missing contract marker in SKILL.md: {marker}")

    def test_pr_review_language_and_root_output_contract(self):
        content = (ROOT / "processes" / "pr-review" / "criteria.md").read_text(encoding="utf-8")
        markers = [
            "Apply shared language contract from `fragments/review-language-contract.md`.",
            "Write these files in the repository root.",
            "Printed chat findings do not satisfy",
            "If the initial user request explicitly asked for GitHub posting, proceed with posting flow.",
            "Otherwise ask whether the user wants posting and wait for explicit confirmation.",
            "For actual posting, use `gh` CLI.",
            "If `gh` is unavailable or unauthenticated, fail the posting step explicitly and stop.",
        ]
        for marker in markers:
            self.assertIn(marker, content, f"Missing contract marker in pr-review criteria: {marker}")

    def test_review_branch_language_and_root_output_contract(self):
        content = (ROOT / "processes" / "review-branch" / "criteria.md").read_text(
            encoding="utf-8"
        )
        markers = [
            "Apply shared language contract from `fragments/review-language-contract.md`.",
            "Write these files in the repository root.",
            "Printed chat findings do not satisfy",
            "If the initial user request explicitly asked for GitHub posting, proceed with posting flow.",
            "Otherwise ask whether the user wants posting and wait for explicit confirmation.",
            "For actual posting, use `gh` CLI.",
            "If `gh` is unavailable or unauthenticated, fail the posting step explicitly and stop.",
            "Posting GitHub review comments requires PR context (`<pr_url>` input mode).",
            "If the review runs in `<review_remote_url> <review_branch>` mode without a PR URL, fail posting explicitly and keep local outputs only.",
        ]
        for marker in markers:
            self.assertIn(
                marker,
                content,
                f"Missing contract marker in review-branch criteria: {marker}",
            )

    def test_language_fragment_contract(self):
        content = (ROOT / "fragments" / "review-language-contract.md").read_text(
            encoding="utf-8"
        )
        markers = [
            "Infer review-output language from the user prompt that triggers second opinion.",
            "Use that language for `second_opinion.md` and user-facing review communication.",
            "Do not ask a separate language-preference question unless the user asks to override.",
            "Keep repository assets and code in English",
        ]
        for marker in markers:
            self.assertIn(
                marker,
                content,
                f"Missing contract marker in review-language fragment: {marker}",
            )

    def test_output_fragment_requires_root_files(self):
        content = (ROOT / "fragments" / "output-review-findings.md").read_text(
            encoding="utf-8"
        )
        markers = [
            "Write both files in the repository root.",
            "Printed chat findings do not satisfy",
            "Source: <type>/<id>",
        ]
        for marker in markers:
            self.assertIn(marker, content, f"Missing contract marker in output fragment: {marker}")

    def test_github_comment_fragment_contract(self):
        content = (ROOT / "fragments" / "github-comment-contract.md").read_text(
            encoding="utf-8"
        )
        markers = [
            "Write `second_opinion_github_comments.json` in the repository root",
            "Always use English in GitHub comments",
            "Source: <type>/<id> | [Second Opinion](https://github.com/PingCAP-QE/second-opinion)",
            "Do not add repository shell posting scripts",
            "If `gh` is unavailable or not authenticated, fail the posting step explicitly and stop.",
            "Posting review comments requires PR context.",
            "Prefer modes in this order: `inline` > `file` > `general`.",
            "subject_type=file",
            "retry once as `file` mode before using `general`",
            "do not add an extra review body comment per finding",
        ]
        for marker in markers:
            self.assertIn(
                marker,
                content,
                f"Missing contract marker in github comment fragment: {marker}",
            )

    def test_github_side_effects_policy_contract(self):
        content = (ROOT / "policies" / "github-side-effects.yaml").read_text(
            encoding="utf-8"
        )
        markers = [
            "produce `second_opinion.md` and `second_opinion.json` first, then ask whether to post.",
            "For actual GitHub comment posting, use `gh` CLI.",
            "If `gh` is unavailable or unauthenticated, fail the posting step explicitly",
            "Posting review comments requires PR context.",
            "always use English.",
            "Source: <type>/<id> | [Second Opinion](https://github.com/PingCAP-QE/second-opinion)",
            "Prefer comment modes in this order: inline, then file, then general.",
            "subject_type=file",
            "retry as file comment before using a general comment",
            "do not add an extra review body comment per finding",
        ]
        for marker in markers:
            self.assertIn(
                marker,
                content,
                f"Missing contract marker in github-side-effects policy: {marker}",
            )
