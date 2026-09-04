# F068 accessibility cases

There is no page to audit with axe. The accessible surfaces are the gate's findings, which a developer reads in a CI log, and `crates/persistence/README.md`, which is the recipe someone follows when adding a repository. Files: `testing/features/F068/accessibility/{output_a11y_tests.rs,readme_structure_tests.rs}`. Flag `F068_FEATURE`.

- `output_is_ascii_only` — NFR-F068-03: every byte of the gate's output on all fixture trees is ASCII, so a screen reader, a plain terminal, and a CI log render it identically.
- `no_color_is_honoured` — NFR-F068-03: `NO_COLOR=1` removes all escape sequences; exit codes and wording are unchanged, and without it no meaning is carried by colour alone.
- `findings_name_the_file_and_line` — NFR-F068-03: every `BLOCKED:` line carries a path and a line number, so the reader navigates by keyboard rather than by scanning a diff visually.
- `codes_are_words_not_symbols` — NFR-F068-03: the six rule codes `persist.raw_sql`, `persist.connection_type`, `persist.escape_hatch`, `persist.table_unmapped`, `persist.table_double_write`, and `persist.array_column`, plus `persist.jsonb_unlisted` and `persist.policy_stale`, are printed verbatim and are self-describing without a legend.
- `no_line_exceeds_200_characters` — NFR-F068-03: the widest finding message, including a full migration path and a column list, stays within the limit.
- `json_is_a_structural_equivalent` — NFR-F068-03, FR-F068-16: every fact in the text output — code, path, line, message, item count, and outcome — is present in the `--json` object, so a reader or tool that cannot parse the text form loses nothing.
- `readme_headings_are_hierarchical` — NFR-F068-03: `crates/persistence/README.md` has one heading per recipe step, in order, with no level skipped, so the four-step recipe is navigable by heading.
- `readme_tables_are_plain_text` — NFR-F068-03: the statement-shape and error-mapping tables use a header row and a separator only, with no nested markup, and read correctly in order.
- `compile_error_message_is_actionable` — FR-F068-02, NFR-F068-03: the `trybuild` expectation for a hand-written implementation is checked to name the sealed module and the crate's recipe, so the failure tells the reader what to do instead of only what broke.

Evidence: captured output and README structure reports under `testing/evidence/F068/accessibility/`.
