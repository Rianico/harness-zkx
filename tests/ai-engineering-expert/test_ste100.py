"""Unit tests for ASD-STE100 deterministic linter (ste100.py)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add ste100 script location to sys.path
_scripts_dir = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "ai-engineering-expert"
    / "subskills"
    / "skill-authoring"
    / "scripts"
)
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from ste100 import (  # noqa: E402
    STE100_BANNED_PHRASAL_VERBS,
    STE100_BANNED_WORDS,
    STE100_MAX_SENTENCE_WORDS,
    _strip_code_blocks,
    _strip_headings,
    _strip_html_entities,
    _strip_inline_code,
    _strip_tables,
    lint_banned_words,
    lint_nominalizations,
    lint_phrasal_verbs,
    lint_semicolons,
    lint_sentence_lengths,
    main,
    split_sentences,
)


class TestSentenceSplitting:
    """Deterministic sentence splitting and element stripping."""

    def test_basic_sentence_split(self):
        text = "This is sentence one. This is sentence two! Is this three?"
        sentences = split_sentences(text)
        assert sentences == ["This is sentence one.", "This is sentence two!", "Is this three?"]

    def test_empty_string(self):
        assert split_sentences("") == []
        assert split_sentences("   \n\n  ") == []

    def test_strip_code_blocks(self):
        text = "before ```code``` after"
        assert _strip_code_blocks(text) == "before   after"

    def test_strip_code_blocks_tilde_fences(self):
        text = "before ~~~code~~~ after"
        assert _strip_code_blocks(text) == "before   after"

    def test_strip_tables(self):
        text = "before\n| col1 | col2 |\nafter"
        assert "| col1 |" not in _strip_tables(text)

    def test_strip_tables_without_outer_pipes(self):
        text = "before\ncol1 | col2\n-- | --\nval1 | val2\nafter"
        clean = _strip_tables(text)
        assert "col1 | col2" not in clean
        assert "val1 | val2" not in clean
        assert "before" in clean
        assert "after" in clean

    def test_strip_headings(self):
        text = "# Heading\nprose"
        assert "# Heading" not in _strip_headings(text)

    def test_strip_inline_code(self):
        text = "run `my_cmd` now"
        assert _strip_inline_code(text) == "run code now"

    def test_strip_html_entities(self):
        text = "a &amp; b &lt; c"
        assert "&amp;" not in _strip_html_entities(text)

    def test_max_sentence_words_constant(self):
        assert STE100_MAX_SENTENCE_WORDS == 20

    def test_list_items_split(self):
        text = "- First item\n- Second item\n* Third item\n+ Fourth item"
        sentences = split_sentences(text)
        assert sentences == ["- First item", "- Second item", "* Third item", "+ Fourth item"]


class TestSentenceLengths:
    """STE-100 Rule 5.1 sentence length verification."""

    def test_short_sentences_pass(self):
        text = "Short sentence one. Short sentence two."
        assert lint_sentence_lengths(text, max_words=20) == []

    def test_long_sentence_detected(self):
        long_sentence = "Word " * 22 + "end."
        issues = lint_sentence_lengths(long_sentence, max_words=20)
        assert len(issues) == 1
        assert "23 words" in issues[0]

    def test_inline_code_does_not_inflate_word_count(self):
        text = "Run `command with twenty very long parameter options and flags` now."
        assert lint_sentence_lengths(text, max_words=20) == []

    def test_code_blocks_do_not_inflate_word_count(self):
        text = "Start.\n```\n" + "long code line\n" * 50 + "```\nEnd."
        assert lint_sentence_lengths(text, max_words=20) == []

    def test_tilde_code_blocks_do_not_inflate_word_count(self):
        text = "Start.\n~~~\n" + "long code line\n" * 50 + "~~~\nEnd."
        assert lint_sentence_lengths(text, max_words=20) == []

    def test_custom_max_words(self):
        text = "One two three four five."
        issues = lint_sentence_lengths(text, max_words=4)
        assert len(issues) == 1
        assert "5 words (max 4)" in issues[0]

    def test_parenthetical_text_counts_as_one_word(self):
        """STE-100 Rule 8.5: text in parentheses counts as one word."""
        base = "Configure the production runtime environment for every connected client device across all regions now"
        text = f"{base} (see the migration appendix notes for details)."
        assert len(text.split()) > 20
        assert lint_sentence_lengths(text, max_words=20) == []

    def test_nested_parenthetical_text_counts_as_one_word(self):
        """STE-100 Rule 8.5: nested parentheses still count as one word."""
        logis = "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau"
        text = f"{logis} (see the note (with an inner aside) here)."
        assert lint_sentence_lengths(text, max_words=20) == []

    def test_hyphenated_words_count_as_one_word(self):
        """STE-100 Rule 8.7: a hyphenated word counts as one word."""
        text = "state-of-the-art production-ready enterprise-grade latency-sensitive configuration."
        assert lint_sentence_lengths(text, max_words=8) == []

    def test_parenthetical_does_not_mask_long_sentence(self):
        """STE-100 Rule 8.5 is a counting rule, not an exemption for long sentences."""
        text = " ".join(["word"] * 21) + " (short)."
        issues = lint_sentence_lengths(text, max_words=20)
        assert len(issues) == 1
        assert "22 words" in issues[0]


class TestBannedWords:
    """CS-adapted STE-100 banned words."""

    def test_clean_prose_passes(self):
        assert lint_banned_words("The algorithm returns the computed hash.") == []

    def test_existing_banned_terms(self):
        for word in ["comprehensive", "robust", "properly", "various", "should work"]:
            issues = lint_banned_words(f"This is a {word} solution.")
            assert len(issues) >= 1
            assert word in issues[0].lower()

    def test_cs_adapted_banned_terms(self):
        for term in [
            "seamless",
            "cutting-edge",
            "effortless",
            "blazing-fast",
            "state-of-the-art",
            "game-changing",
        ]:
            issues = lint_banned_words(f"Our {term} pipeline delivers results.")
            assert len(issues) >= 1
            assert term in issues[0].lower() or term.replace("-", " ") in issues[0].lower()

    def test_hyphen_and_space_variants(self):
        assert len(lint_banned_words("This is cutting-edge technology.")) >= 1
        assert len(lint_banned_words("This is cutting edge technology.")) >= 1
        assert len(lint_banned_words("This is blazing-fast indexing.")) >= 1
        assert len(lint_banned_words("This is blazing fast indexing.")) >= 1
        assert len(lint_banned_words("This is state-of-the-art modeling.")) >= 1
        assert len(lint_banned_words("This is state of the art modeling.")) >= 1
        assert len(lint_banned_words("This is game-changing speed.")) >= 1
        assert len(lint_banned_words("This is game changing speed.")) >= 1

    def test_case_insensitive(self):
        assert len(lint_banned_words("A SEAMLESS interface.")) >= 1
        assert len(lint_banned_words("A Robust validator.")) >= 1
        assert len(lint_banned_words("A CUTTING-EDGE tool.")) >= 1

    def test_backticked_identifiers_insulated(self):
        """Technical tokens in inline code must not be flagged."""
        text = "Set `robust_mode = True` and use `seamless_auth()` in config."
        assert lint_banned_words(text) == []

    def test_code_blocks_insulated(self):
        text = "```\nval = robust_function()\n# comprehensive comment\n```\nPlain sentence."
        assert lint_banned_words(text) == []

    def test_tables_insulated(self):
        """Reference tables containing banned words must not trigger self-lint failures."""
        text = "| Banned Term | Description |\n| --- | --- |\n| robust | Strong and reliable |\n| seamless | Continuous |"
        assert lint_banned_words(text) == []

    def test_tables_without_outer_pipes_insulated(self):
        """GFM tables without outer pipes must not trigger self-lint failures."""
        text = "Term | Description\n--- | ---\nrobust | Strong and reliable\nseamless | Continuous"
        assert lint_banned_words(text) == []

    def test_banned_words_dictionary_integrity(self):
        for term, reason in STE100_BANNED_WORDS.items():
            assert term, f"Empty term: {reason}"
            assert reason, f"Empty reason for {term}"
            assert " " in term or "-" in term or term.isalpha()


class TestPhrasalVerbs:
    """Soft phrasal verbs check."""

    def test_clean_prose_passes(self):
        assert lint_phrasal_verbs("Start the service. Initialize workers.") == []

    def test_all_banned_phrasal_verbs_flagged(self):
        phrasal_examples = {
            "spin up": "We spin up a new container.",
            "kick off": "Let us kick off the evaluation.",
            "dive into": "We will dive into the implementation details.",
            "reach out": "Please reach out to the ops team.",
            "circle back": "We can circle back to this item later.",
            "touch base": "I will touch base with the team.",
        }
        for verb, text in phrasal_examples.items():
            issues = lint_phrasal_verbs(text)
            assert len(issues) >= 1, f"Failed to detect: {verb}"
            assert verb in issues[0].lower()

    def test_phrasal_verb_inflections(self):
        assert len(lint_phrasal_verbs("The daemon spins up three threads.")) >= 1
        assert len(lint_phrasal_verbs("They spun up a cluster.")) >= 1
        assert len(lint_phrasal_verbs("Spinning up instances now.")) >= 1
        assert len(lint_phrasal_verbs("The job kicked off at midnight.")) >= 1
        assert len(lint_phrasal_verbs("Kicking off the task.")) >= 1
        assert len(lint_phrasal_verbs("He dove into the log files.")) >= 1
        assert len(lint_phrasal_verbs("Diving into the stack trace.")) >= 1
        assert len(lint_phrasal_verbs("We reached out yesterday.")) >= 1
        assert len(lint_phrasal_verbs("Reaching out for help.")) >= 1
        assert len(lint_phrasal_verbs("She circled back on Monday.")) >= 1
        assert len(lint_phrasal_verbs("Circling back now.")) >= 1
        assert len(lint_phrasal_verbs("He touched base with engineering.")) >= 1

    def test_hyphenated_phrasal_verbs(self):
        assert len(lint_phrasal_verbs("We will spin-up the container.")) >= 1
        assert len(lint_phrasal_verbs("Let us kick-off the task.")) >= 1
        assert len(lint_phrasal_verbs("Time to touch-base tomorrow.")) >= 1
        assert len(lint_phrasal_verbs("Please reach-out to the lead.")) >= 1
        assert len(lint_phrasal_verbs("We can circle-back next week.")) >= 1

    def test_phrasal_verbs_insulated_in_code(self):
        text = "Run `spin_up()` or `touch base` inside the console."
        assert lint_phrasal_verbs(text) == []

        fenced = "```bash\nspin up server\n```\nStart server."
        assert lint_phrasal_verbs(fenced) == []

    def test_phrasal_verbs_dictionary_integrity(self):
        for verb, reason in STE100_BANNED_PHRASAL_VERBS.items():
            assert verb
            assert reason


class TestSemicolons:
    """STE-100 Rule 8.1 semicolon check in prose."""

    def test_clean_prose_passes(self):
        assert lint_semicolons("First sentence. Second sentence.") == []

    def test_semicolon_in_prose_flagged(self):
        text = "This is clause one; this is clause two."
        issues = lint_semicolons(text)
        assert len(issues) == 1
        assert "Semicolon in prose (STE-100 Rule 8.1)" in issues[0]

    def test_semicolon_in_inline_code_insulated(self):
        text = "Set `int count = 0;` in your loop declaration."
        assert lint_semicolons(text) == []

    def test_semicolon_in_code_block_insulated(self):
        text = '```c\nint x = 42;\nprintf("%d", x);\n```\nNormal sentence.'
        assert lint_semicolons(text) == []

    def test_semicolon_in_tilde_code_block_insulated(self):
        text = '~~~c\nint x = 42;\nprintf("%d", x);\n~~~\nNormal sentence.'
        assert lint_semicolons(text) == []

    def test_html_entities_insulated(self):
        text = "Use &amp; for ampersands, &lt; for less-than, and &gt; for greater-than."
        assert lint_semicolons(text) == []

    def test_numeric_and_hex_html_entities_insulated(self):
        text = "Special symbols like &#160; and &#x20; represent spaces."
        assert lint_semicolons(text) == []

    def test_html_tags_with_semicolons_insulated(self):
        text = 'Use <span style="color:red;font-size:12px;">styled text</span> here.'
        assert lint_semicolons(text) == []

    def test_tables_insulated(self):
        text = "| Header 1 | Header 2 |\n| -------- | -------- |\n| val1; val2 | val3 |"
        assert lint_semicolons(text) == []

    def test_urls_insulated(self):
        """Semicolons in query strings or URL paths must not trigger prose warnings."""
        text = "Check https://example.org/path?a=1;b=2 for full details."
        assert lint_semicolons(text) == []

    def test_mailto_and_tel_uris_insulated(self):
        """Semicolons in mailto/tel query strings or parameters must not trigger prose warnings."""
        text = "Contact mailto:dev@example.org?subject=hi;body=there or tel:+12345;ext=678."
        assert lint_semicolons(text) == []

    def test_markdown_link_titles_with_semicolons_insulated(self):
        """Semicolons within markdown link titles or destinations must not trigger prose warnings."""
        text = 'Click [here](https://example.org/api?a=1;b=2 "API; docs") for details.'
        assert lint_semicolons(text) == []

    def test_html_comments_insulated(self):
        """Semicolons within HTML comments must not trigger prose warnings."""
        text = "<!-- Note: check status; ignore if none -->\nNormal sentence here."
        assert lint_semicolons(text) == []


class TestNominalizations:
    """Smothered verbs check."""

    def test_clean_direct_verbs_pass(self):
        text = "Validate the input schema. Deploy the service. Inspect logs."
        assert lint_nominalizations(text) == []

    def test_perform_nominalization_flagged(self):
        assert len(lint_nominalizations("We perform a validation of incoming requests.")) == 1
        assert len(lint_nominalizations("The script performs an installation.")) == 1
        assert len(lint_nominalizations("He performed the deployment yesterday.")) == 1

    def test_conduct_nominalization_flagged(self):
        assert len(lint_nominalizations("Conduct an inspection of the container.")) == 1
        assert len(lint_nominalizations("She conducts an assessment of memory usage.")) == 1
        assert len(lint_nominalizations("They conducted a verification.")) == 1

    def test_carry_out_nominalization_flagged(self):
        assert len(lint_nominalizations("Carry out a migration of existing tables.")) == 1
        assert len(lint_nominalizations("The engine carries out the conversion.")) == 1
        assert len(lint_nominalizations("We carried out the deployment.")) == 1

    def test_intermediate_adjective_nominalization(self):
        text = "Carry out an automated verification before merge."
        assert len(lint_nominalizations(text)) == 1

    def test_nominalization_insulated_in_code(self):
        text = "Run `perform a validation` using the test harness."
        assert lint_nominalizations(text) == []

        fenced = "```\nperform a validation\n```\nNormal sentence."
        assert lint_nominalizations(fenced) == []

    def test_make_nominalization_flagged(self):
        """'make' + verbal noun must be flagged."""
        assert len(lint_nominalizations("We make a determination on cache validity.")) == 1
        assert len(lint_nominalizations("The engine makes an assessment.")) == 1

    def test_legitimate_cs_nouns_not_flagged(self):
        """Legitimate CS nouns must not trigger false positive smothered verb warnings."""
        assert lint_nominalizations("The module will perform the function as expected.") == []
        assert lint_nominalizations("The coordinator conducts the transaction across nodes.") == []
        assert lint_nominalizations("Workers perform an operation on the shard.") == []


class TestCLIEntryPoint:
    """CLI execution via main()."""

    def test_clean_file_returns_zero(self):
        with tempfile.TemporaryDirectory() as d:
            md_file = Path(d) / "clean.md"
            _ = md_file.write_text("# Clean\n\nDirect actions only. Run the test.\n")
            exit_code = main([str(md_file)])
            assert exit_code == 0

    def test_file_with_violations_returns_one(self):
        with tempfile.TemporaryDirectory() as d:
            md_file = Path(d) / "violations.md"
            _ = md_file.write_text(
                "# Test\n\nThis is a comprehensive and seamless solution; it performs a validation.\n"
            )
            exit_code = main([str(md_file)])
            assert exit_code == 1

    def test_nonexistent_path_returns_two(self):
        exit_code = main(["/nonexistent/path/for/sure/doc.md"])
        assert exit_code == 2

    def test_directory_scan(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            _ = (p / "f1.md").write_text("# File 1\nClean sentence here.\n")
            _ = (p / "f2.md").write_text("# File 2\nAnother clean sentence.\n")
            exit_code = main([str(p)])
            assert exit_code == 0

    def test_frontmatter_stripped_in_cli(self):
        with tempfile.TemporaryDirectory() as d:
            md_file = Path(d) / "with_frontmatter.md"
            _ = md_file.write_text(
                "---\nname: test\ndescription: A comprehensive guide.\n---\n\n# Body\n\nClean text.\n"
            )
            exit_code = main([str(md_file)])
            assert exit_code == 0
