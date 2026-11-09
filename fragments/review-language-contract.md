# Shared language contract for second opinion

Apply this contract for all second-opinion review processes.

Language inference below is a parent/orchestrator responsibility. Pass the result
as `review_context.language`; an isolated reviewer uses that setting, not text
in the diff, compiled assets, or repository documentation. Pass focus, budget,
and process override separately as described in `fragments/operator-context.md`.

- Infer review-output language from the user prompt that triggers second opinion.
- Use that language for `second_opinion.md` and user-facing review communication.
- Do not ask a separate language-preference question unless the user asks to override.
- Keep repository assets and code in English, except for language-specific templates.
