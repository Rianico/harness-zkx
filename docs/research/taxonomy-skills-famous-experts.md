# Taxonomy of Agent Skills — How Famous Labs & Experts Classify Skills

> Research note — primary sources only. Saved at `docs/research/taxonomy-skills-famous-experts.md` per repo convention (`docs/research/` exists, empty).

## Question

How do famous developers / AI labs and experts taxonomize "skills" for AI agents? Specifically: what dimensions, category names, trigger / invocation models, and structural conventions do they use, and how do those compare to the LSZ harness's 4-type taxonomy (Orchestration / Complex Workflow / Domain Knowledge / Action)?

## Method

- Searched official docs and first-party sources, not secondary blogs; fetched canonical pages with `fetch_content`; extracted verbatim passages via `get_search_content`.
- Verified with `source_check`-style citation capture (URL + quoted passage) and local file citation (`file:line`).
- Covered 5 primary authorities + local control:
  1. **Agent Skills open standard** — `agentskills.io/specification` (Anthropic-published, updated Dec 18 2025)
  2. **Anthropic Claude Code — Skills** — `code.claude.com/docs/en/skills`
  3. **Anthropic Engineering — Equipping agents for the real world with Agent Skills** — `anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills`
  4. **OpenAI Agents SDK — Tools** — `openai.github.io/openai-agents-python/tools`
  5. **Microsoft Semantic Kernel — Plugins** — `learn.microsoft.com/en-us/semantic-kernel/concepts/plugins`
  6. **LangChain — Tools** — `docs.langchain.com/oss/python/langchain/tools`
  7. **LSZ harness local** — `skills/ai-engineering-expert/subskills/skill-authoring/SKILL.md` (control)

## Findings per Source

### 1. Agent Skills Open Standard (`agentskills.io/specification`) — No semantic taxonomy, only structural

**Source:** [Source: https://agentskills.io/specification]

> "A skill is a directory containing, at minimum, a `SKILL.md` file" and "The `SKILL.md` file must contain YAML frontmatter followed by Markdown content." Frontmatter required: `name` (1–64 chars, lowercase alphanumeric + hyphens, matches directory name) and `description` (1–1024 chars). Optional: `license`, `compatibility`, `metadata` (map<string,string>), `allowed-tools` (experimental).

> "Progressive disclosure: 1. Metadata (~100 tokens) — name+description loaded at startup; 2. Instructions (<5000 tokens recommended) — full SKILL.md body when activated; 3. Resources (as needed) — scripts/, references/, assets/ loaded only when required."

**Taxonomy:** The spec deliberately does **not** impose a semantic type system. It classifies by **structural layer** (metadata / instructions / resources) and **resource kind** (`scripts/` executable, `references/` docs, `assets/` static). The recommended body shape is open: "Step-by-step instructions, Examples, Common edge cases." No Orchestration vs Domain vs Action distinction — that is left to implementors.

**Dimensions:** file location, frontmatter validity, progressive-disclosure level, resource directory.

### 2. Anthropic Claude Code — Skills (Product Docs)

**Source:** [Source: https://code.claude.com/docs/en/skills]

> "Skills extend what Claude can do. Create a `SKILL.md` file with instructions, and Claude adds it to its toolkit. Claude uses skills when relevant, or you can invoke one directly with `/skill-name`."
> "Create a skill when you keep pasting the same instructions, checklist, or multi-step procedure into chat, or when a section of CLAUDE.md has grown into a procedure rather than a fact."
> "Claude Code skills follow the Agent Skills open standard ... Claude Code extends the standard with additional features like invocation control, subagent execution, and dynamic context injection."

**Key extensions beyond spec (Claude Code–only frontmatter):**
[Source: https://code.claude.com/docs/en/skills — Frontmatter reference table]

> `disable-model-invocation`, `user-invocable`, `allowed-tools` / `disallowed-tools`, `model`, `effort`, `context: fork`, `agent`, `background`, `hooks`, `paths`, `shell`, `argument-hint` + `arguments`.
> "Where you store a skill determines who can use it: Enterprise > Personal (`~/.claude/skills/`) > Project (`.claude/skills/`) > Plugin (`<plugin>/skills/`)." With conflict resolution and `plugin-name:skill-name` namespace.

**Informal sub-taxonomy inside docs:**

- By **invocation:** auto (Claude decides via description) vs explicit `/skill-name`; `disable-model-invocation: true` for manual-only, `user-invocable: false` for background knowledge.
- By **content intent:** "Reference content ... runs inline" vs "Task content ... step-by-step instructions for a specific action ... often actions you want to invoke directly" [Source: same page, Types of skill content].
- By **distribution scope:** enterprise / personal / project / plugin / synced (`~/.claude/skills/synced/`).

No named "Orchestration / Action" labels — but the concepts exist as content advice.

### 3. Anthropic Engineering Blog — Equipping agents ... (Conceptual Rationale)

**Source:** [Source: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills]

> "Building a skill for an agent is like putting together an onboarding guide for a new hire."
> "Progressive disclosure is the core design principle that makes Agent Skills flexible and scalable. Like a well-organized manual that starts with a table of contents, then specific chapters, and finally a detailed appendix, skills let Claude load information only as needed"
> "Skills can also include code for Claude to execute as tools at its discretion ... because code is deterministic, this workflow is consistent and repeatable. ... Skills provide Claude with new capabilities through instructions and code."
> Update note: "We've published Agent Skills as an open standard for cross-platform portability. (December 18, 2025)"

**Taxonomy implied:** Skills as **composable procedural knowledge** — each skill packages a bundle of expertise to turn a general agent into a specialist. Example: the PDF skill teaches Claude to manipulate PDFs (extract form fields via a bundled Python script, then fill forms via `forms.md`). Classification is by **capability domain** (document, creative, enterprise) — the public repo groups `[./skills](./skills): Creative & Design, Development & Technical, Enterprise & Communication, and Document Skills` [Source: https://github.com/anthropics/skills — README.md#Skill Sets], not by workflow shape.

### 4. OpenAI Agents SDK — Tools (Python)

**Source:** [Source: https://openai.github.io/openai-agents-python/tools]

> "Tools let agents take actions: things like fetching data, running code, calling external APIs, and even using a computer. The SDK supports five categories: Hosted OpenAI tools; Local/runtime execution tools (`ComputerTool` and `ApplyPatchTool` always run in your environment, while `ShellTool` can run locally or in a hosted container); `FunctionTool` instances; Agents as tools; Experimental: Codex tool."

**Sub-taxonomy within hosted/runtime:**

- **Hosted (OpenAI-managed):** `WebSearchTool`, `FileSearchTool`, `CodeInterpreterTool`, `HostedMCPTool`, `ImageGenerationTool`, `ToolSearchTool`, `ProgrammaticToolCallingTool`.
- **Local/runtime:** `ComputerTool`/`AsyncComputer` (GUI), `ShellTool` (local or `container_auto`/`container_reference` + `skills` references), `ApplyPatchTool`/`ApplyPatchEditor`, `LocalShellTool` (legacy).
- **Function tools:** any Python function decorated with `@tool`; schema auto-derived from signature + docstring via `inspect`+`griffe`+`pydantic`; supports `defer_loading=True` + `tool_namespace(name, description, tools=[...])` for grouped deferred loading.
- **Agents as tools:** expose an agent as callable without full handoff.
- **ToolSearchTool:** defers large surfaces until runtime; "Prefer namespaces or hosted MCP servers over many individually deferred functions" [Source: same page, Hosted tool search].

**Dimensions:** _who executes_ (hosted vs local), _where networked_ (MCP, OpenAI servers, local process), _granularity_ (single function vs namespace vs agent), _deferral_ (immediate vs `defer_loading`), _duality_ (direct vs `programmatic` via `allowed_callers`).

OpenAI does **not** use the word "skill" as a first-class type here; "skill" surfaces instead in the container shell via `ShellTool.environment.skills: [SkillReference]` (e.g., `csv_skill` referencing `skill_id`/`version`) [Source: same page, Hosted container shell + skills]. That is a _mounted skill bundle_ for hosted shell, closer to Anthropic's notion than to a tool taxonomy.

### 5. Microsoft Semantic Kernel — Plugins

**Source:** [Source: https://learn.microsoft.com/en-us/semantic-kernel/concepts/plugins]

> "Plugins are a key component of Semantic Kernel. ... you can encapsulate your existing APIs into a collection that can be used by an AI."
> "At a high-level, a plugin is a group of functions that can be exposed to AI apps and services. The functions within plugins can then be orchestrated by an AI application to accomplish user requests."
> "Importing different types of plugins: using native code, using an OpenAPI specification or from a MCP Server"
> "Within a plugin, you will typically have two different types of functions, those that retrieve data for retrieval augmented generation (RAG) and those that automate tasks."

**Taxonomy:**

- **By origin:** Native code (annotated `KernelFunction` / `@kernel_function`) vs OpenAPI vs MCP Server.
- **By role:** _Data retrieval_ (RAG) vs _Task automation_ (human-in-the-loop).
- **Organization:** Plugin = named group (`plugin_name="Lights"`), functions have `name` + `Description`, parameters have `Description`; snake_case recommended because "most LLM have been trained with Python for function calling" [Source: same page, Getting started].

Guidance includes token economy: "We recommend that you use no more than 20 tools in a single API call ... ideally, no more than 10 tools." [Source: same page, Import only the necessary plugins]; also "Minimize function parameters" and "Find a right balance between number of functions and responsibilities."

**Relationship to skills:** [Source: https://devblogs.microsoft.com/agent-framework/skills-to-plugins-fully-embracing-the-openai-plugin-spec-in-semantic-kernel] — SK _renamed_ "skills" to "plugins" to embrace the OpenAI plugin spec; historical "SK Skills" are now plugins.

### 6. LangChain — Tools

**Source:** [Source: https://docs.langchain.com/oss/python/langchain/tools]

> "Tools extend what agents can do—letting them fetch real-time data, execute code, query external databases, and take actions in the world. Under the hood, tools are callable functions with well-defined inputs and outputs that get passed to a chat model."

**Taxonomy of tool use:**

- **Create:** `@tool` decorator; type hints required for input schema; reserved args: `config`, `runtime`.
- **Context access:** `ToolRuntime` (state / context / store / stream_writer / execution_info / server_info).
- **Return shapes:** `string` vs `object` vs `Command` (state-mutating) vs multimodal blocks; `return_direct=True` to short-circuit.
- **Dynamic selection:** Filtering pre-registered tools vs Runtime registration (`wrap_model_call`/`wrap_tool_call`); "Too many tools may overwhelm the model (overload context) and increase errors" [Source: same page, Dynamic tool selection].
- **Headless tools:** schema-only on server, implementation on client (browser APIs, privacy, latency) — interrupt/resume handshake.
- **Prebuilt tools/toolkits** + **Server-side tool use** (provider-executed built-ins).

**Dimensions:** schema strictness, statefulness (Command mutates graph), execution site (server vs client/headless), dynamism, and built-in vs custom.

### 7. LSZ Harness — Local Skill Taxonomy (Control)

**Source:** [Source: skills/ai-engineering-expert/subskills/skill-authoring/SKILL.md:88-99 — Skill Taxonomy table, lines 88–99]

> "Every LSZ skill falls into one of four types: | Orchestration — Multi-phase, multi-party, fan-out/fan-in workflows — Owns sequencing, branching, checkpoints; delegates all implementation | Complex Workflow — Substantial single-purpose workflow with multiple phases — May invoke agents; owns phase transitions | Domain Knowledge — Guides, patterns, expert methodology — Retrieval-time expertise; does not own orchestration | Action — Narrow, simple workflows — Low-ambiguity; compact and self-contained |"

**Additional local dimensions:**

- **Frontmatter budgets:** `description` max 300 chars (LSZ hard gate) vs spec 1024; block scalars `>-`/`|` required [Source: same SKILL.md — Required Frontmatter section].
- **Parent-skill pattern:** `metadata.manage: [article, publish]` parent + `managed-by: write` sub-skills under `subskills/` (hidden from Claude discovery; dispatched via `Read` not `Skill` tool) [Source: same SKILL.md — Parent Skill with Sub-Skills].
- **Explicit decision rule:** "Does this need multiple phases or parties? → orchestration; single multi-step workflow? → complex workflow; expertise to load on demand? → domain knowledge; narrow self-contained? → action" [Source: same SKILL.md — Phase 1: Gather, bullet 4].

## Synthesis — Comparative Table

| Authority                                | Top-level buckets                                                                                                  | Primary dimension                          | Invocation / Trigger                                                                                               | Granularity / Composition                                                                             | Notable constraint                                                           |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **Agent Skills spec** (`agentskills.io`) | None (open) — only structural layers: metadata / instructions / resources (`scripts/`, `references/`, `assets/`)   | Structure + progressive disclosure         | Description-based auto-load                                                                                        | Skill = directory `SKILL.md` + resources                                                              | `name` 64 chars, `description` 1024, `<500 lines` body guidance              |
| **Anthropic Claude Code**                | By scope: Enterprise / Personal / Project / Plugin / Synced; by content: Reference vs Task                         | Distribution scope + intent                | Auto (description) + explicit `/name`; `disable-model-invocation` / `user-invocable` / `context: fork`             | Bundled skills prompt-based orchestration                                                             | Adds `argument-hint`/`arguments`, `allowed-tools`, `model`/`effort`, `paths` |
| **Anthropic Engineering blog**           | By capability domain: Creative & Design, Development & Technical, Enterprise, Document                             | Domain expertise as onboarding guide       | Same as above                                                                                                      | Composable procedural knowledge + deterministic code tools                                            | Publishing as open standard Dec 2025                                         |
| **OpenAI Agents SDK**                    | 5 tool categories: Hosted, Local/runtime, FunctionTool, Agents-as-tools, Codex; sub: namespaces + deferred loading | Execution site (who runs) + deferral       | `FunctionTool` via `@tool`; `ToolSearchTool` + `tool_namespace` deferral; `allowed_callers` direct vs programmatic | `tool_namespace` ≤10 funcs; hosted container `ShellTool.environment.skills: [SkillReference]`         | Hosted skills only via container shell, not top-level skill type             |
| **Microsoft Semantic Kernel**            | Plugin origin: Native / OpenAPI / MCP; function role: RAG retrieval vs Task automation                             | Origin + role                              | `KernelFunction` annotation, `kernel.add_plugin(plugin, plugin_name)`                                              | Plugin = group of functions; rename history: skills→plugins                                           | ≤20 tools/call (ideally ≤10) for accuracy                                    |
| **LangChain**                            | Tool lifecycle: Create / Context / Return / Dynamic / Headless / Prebuilt / Server-side                            | Schema + state + execution site + dynamism | `@tool` + `ToolRuntime` injection; `return_direct` / `Command`; headless interrupt/resume                          | `Command` state-mutating returns; headless schema-only vs implementation                              | Reserved `config`/`runtime`, strict schema, ≤10-20 tools guidance shared     |
| **LSZ harness**                          | **4 types:** Orchestration / Complex Workflow / Domain Knowledge / Action                                          | Workflow phases × parties × ambiguity      | Skill `description` trigger (300c hard gate) + optional `argument-hint`/`arguments`                                | Orchestration delegates subagents; Complex Workflow owns phases; Domain = retrieval; Action = compact | Parent-skill `manage`/`managed-by` + `subskills/` hidden from discovery      |

### Key contrasts that matter for LSZ

1. **Spec is intentionally non-taxonomic; LSZ is opinionated.** The Agent Skills spec refuses to name workflow types, while LSZ needs them to decide _who owns sequencing_ (orchestrator vs skill) and _how to write_ (dispatch table vs phase definitions vs domain guide). [Source: spec vs `skill-authoring/SKILL.md` taxonomy table].

2. **Anthropic's informal "Reference vs Task" maps to LSZ's Domain vs Action/Complex Workflow, but LSZ splits Task further** by multi-party fan-out (Orchestration) vs single workflow (Complex) vs compact (Action). The decision tree ("Does this need multiple phases or parties?") prevents hero-mode orchestrators [Source: Claude Code docs — Types of skill content vs LSZ Phase 1 Gather bullet 4].

3. **OpenAI/MSK/LangChain taxonomize by _execution site_ and _tool count economics_; LSZ taxonomizes by _ownership and workflow shape_.** All agree on "keep tool count low" (OpenAI ≤20 ideally ≤10; SK cites same; LangChain warns overload) — LSZ expresses this as description budget (300c) and progressive disclosure rather than a numeric tool cap.

4. **"Skill" naming is unstable across ecosystems.** SK explicitly renamed skills→plugins to align with OpenAI [Source: MS Blog — Skills to plugins]. OpenAI repurposed "skills" as hosted container `SkillReference` for shell [Source: OpenAI Tools — Hosted container shell + skills]. Anthropic's open standard reclaimed "skills" as `SKILL.md` bundles. LSZ follows Anthropic's `SKILL.md` spec but adds its own 4-type overlay.

5. **Parent-skill pattern is LSZ-specific.** Neither the spec nor Anthropic docs describe `subskills/` hidden from discovery dispatched via `Read`; LSZ invented it to keep router context lean while preserving `manage`/`managed-by` governance [Source: `skill-authoring/SKILL.md` — Parent Skill with Sub-Skills].

## Citations (primary sources, verbatim)

- Agent Skills spec frontmatter + progressive disclosure — [Source: https://agentskills.io/specification] — quoted in §1.
- Claude Code Skills — [Source: https://code.claude.com/docs/en/skills] — "Skills extend what Claude can do ...", "Claude Code skills follow the Agent Skills open standard ...", frontmatter table, scope hierarchy.
- Equipping agents ... — [Source: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills] — onboarding guide, progressive disclosure principle, code-execution-as-tool.
- OpenAI Agents SDK Tools — [Source: https://openai.github.io/openai-agents-python/tools] — five categories, hosted container skills reference, tool search/namespaces.
- Semantic Kernel Plugins — [Source: https://learn.microsoft.com/en-us/semantic-kernel/concepts/plugins] — plugin anatomy, import types, RAG vs task automation, ≤20 tools guidance.
- LangChain Tools — [Source: https://docs.langchain.com/oss/python/langchain/tools] — `@tool`, `ToolRuntime`, `return_direct`/`Command`, dynamic/headless taxonomy.
- LSZ control — [Source: skills/ai-engineering-expert/subskills/skill-authoring/SKILL.md:88-99] — 4-type table and decision rule; also frontmatter constraints and parent-skill pattern in same file.

## Open Questions

- Should LSZ keep its 4-type split or converge toward Anthropic's lighter Reference/Task + scope model now that the spec is open? Evidence suggests keeping the 4 types is justified because LSZ governs _orchestration ownership_ (who sequences subagents), which the spec intentionally leaves unspecified.
- Is the 300c description budget (LSZ) still right, or should it track the spec's 1024c with soft trimming? LSZ's gate catches bloat that Anthropic tolerates via 1,536-char truncation.
- For taxonomy item 7 (originally deferred): a full redefinition would need real implementation data across scaffold/language flavors — not just docs. Next grill should collect that.

---

_Generated via primary-source research — web + fetched docs — on 2026-04-15. File: `docs/research/taxonomy-skills-famous-experts.md`._
