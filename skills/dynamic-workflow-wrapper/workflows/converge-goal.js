/**
 * converge-goal.js — AFK goal convergence loop for pi-dynamic-workflows.
 *
 * Topology: Prepare (worktree) ➔ Developer ➔ Deterministic Gate (eval-gate / stack tests)
 *           ➔ Semantic Review (Crux invariants)
 * Cyclic control helper: gate(thunk, validator, { attempts })
 *
 * Isolation contract: every round after Prepare runs against ONE persistent worktree —
 * created by `wt` when the project ships `.config/wt.toml` (so copy-ignored and the
 * pre-merge gate apply), else by `git worktree`. Two runtime traps fix the shape of this
 * file. Do not "simplify" them away:
 *
 *   1. `agent(prompt, { cwd })` is NOT forwarded. The runtime derives the subagent cwd
 *      from `options.isolation === "worktree"` only (dist/workflow.js:
 *      `const runCwd = worktree?.isolated ? worktree.cwd : undefined`), and the documented
 *      agent option list is label/phase/schema/model/tier/isolation/thread/agentType/
 *      timeoutMs/retries — no `cwd`. A script-level cwd is silently ignored, so the
 *      worktree must instead be an explicit contract in every prompt: absolute paths for
 *      read/edit/write, `cd <worktree> &&` (or `git -C <worktree>`) for every shell command.
 *   2. The built-in `isolation: "worktree"` is per-CALL and removed in a `finally` after
 *      each agent returns. A convergence loop must accumulate commits across rounds, so
 *      per-call throwaway worktrees cannot be used here.
 */

export const meta = {
  name: "converge-goal",
  description:
    "Autonomous iterative goal convergence loop in a dedicated worktree, gated by stack tests and crux code-review",
  phases: [
    { title: "Plan & Prepare" },
    { title: "Iterate & Gate" },
    { title: "Finalize" },
  ],
};

// 1. Resolve arguments
const task = args && typeof args.task === "string" ? args.task : "Complete the requested coding task.";
const maxAttempts =
  args && Number.isInteger(args.maxAttempts) ? Math.max(1, Math.min(args.maxAttempts, 10)) : 5;
const evalDir = args && typeof args.evalDir === "string" ? args.evalDir : null;
const stackHint = args && typeof args.stack === "string" ? args.stack : null;
const baseArg = args && typeof args.base === "string" && args.base.trim() !== "" ? args.base.trim() : null;
const branchArg =
  args && typeof args.branch === "string" && args.branch.trim() !== "" ? args.branch.trim() : null;

const root = typeof cwd === "string" ? cwd : process.cwd();
const slug =
  String(task)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48)
    .replace(/-+$/g, "") || "task";
const branch = branchArg || `converge/${slug}`;
const requestedBase = baseArg || "main";

// 2. Structured Schemas
const prepSchema = {
  type: "object",
  properties: {
    summary: { type: "string" },
    status: { type: "string", enum: ["COMPLETED", "BLOCKED"] },
    worktreePath: { type: "string" },
    branch: { type: "string" },
    base: { type: "string" },
    baseSource: { type: "string" },
    tool: { type: "string", enum: ["wt", "git"] },
    reused: { type: "boolean" },
    cleanRoot: { type: "boolean" },
    issues: { type: "array", items: { type: "string" } },
  },
  required: [
    "summary",
    "status",
    "worktreePath",
    "branch",
    "base",
    "baseSource",
    "tool",
    "reused",
    "cleanRoot",
    "issues",
  ],
};

const devSchema = {
  type: "object",
  properties: {
    summary: { type: "string" },
    status: { type: "string", enum: ["COMPLETED", "BLOCKED"] },
    artifacts: {
      type: "array",
      items: {
        type: "object",
        properties: {
          path: { type: "string" },
          kind: { type: "string" },
        },
        required: ["path", "kind"],
      },
    },
    commits: { type: "array", items: { type: "string" } },
    filesChanged: { type: "array", items: { type: "string" } },
    checks: {
      type: "array",
      items: {
        type: "object",
        properties: {
          name: { type: "string" },
          command: { type: "string" },
          ok: { type: "boolean" },
          exitCode: { type: "integer" },
          tail: { type: "string" },
        },
        required: ["name", "command", "ok"],
      },
    },
    issues: { type: "array" },
  },
  required: ["summary", "status", "filesChanged"],
};

const gateSchema = {
  type: "object",
  properties: {
    summary: { type: "string" },
    status: { type: "string", enum: ["COMPLETED", "BLOCKED", "REJECTED"] },
    ok: { type: "boolean" },
    artifacts: { type: "array" },
    phases: {
      type: "array",
      items: {
        type: "object",
        properties: {
          name: { type: "string" },
          command: { type: "string" },
          ok: { type: "boolean" },
          exitCode: { type: "integer" },
          tail: { type: "string" },
        },
        required: ["name", "command", "ok"],
      },
    },
    issues: { type: "array" },
  },
  required: ["summary", "status", "ok", "phases"],
};

const reviewSchema = {
  type: "object",
  properties: {
    summary: { type: "string" },
    status: { type: "string", enum: ["COMPLETED", "BLOCKED"] },
    route: { type: "string", enum: ["continue", "remediate", "blocked"] },
    score: { type: "integer" },
    artifacts: { type: "array" },
    issues: {
      type: "array",
      items: {
        type: "object",
        properties: {
          id: { type: "string" },
          severity: { type: "string", enum: ["P1", "P2", "P3"] },
          file: { type: "string" },
          line: { type: "integer" },
          invariant: { type: "string" },
          defect: { type: "string" },
          remediation: { type: "string" },
        },
        required: ["id", "severity", "file", "defect", "remediation"],
      },
    },
    priorIssues: { type: "array" },
  },
  required: ["summary", "status", "route", "issues"],
};

// 3. Execution Ledger
const ledger = [];
let touchedFiles = [];

// 4. Plan & Prepare — allocate the run's worktree
phase("Plan & Prepare");
log(
  `converge-goal: starting AFK run for task: "${task}" (maxAttempts: ${maxAttempts}, branch: ${branch}, base: ${requestedBase})`,
);

const prepPrompt = [
  `You are the Prepare node of an AFK convergence run. You allocate the ONE worktree every later round will use.`,
  `You do not implement, gate, review, merge, or open a PR, and you never modify repository files.`,
  `Ignore any part of your role definition describing a dependency DAG or the ship-tasks workflow — this is a single-goal converge run.`,
  ``,
  `Session root (your cwd, must stay untouched): ${root}`,
  `Branch to create or reuse: ${branch}`,
  `Requested base: ${requestedBase}`,
  ``,
  `Procedure — run each step, and put the exact failing command plus its output in \`issues\` when one fails:`,
  ``,
  `1. Admission: \`git status --porcelain\`. Untracked \`.lsz/\` entries are tolerated; any other output means the root is dirty → status BLOCKED, worktreePath "", cleanRoot false.`,
  `2. Resolve the base: if \`git rev-parse --verify ${requestedBase}\` succeeds, use ${requestedBase} with baseSource "arg-or-requested". Otherwise fall back to the repository default branch (\`git rev-parse --abbrev-ref origin/HEAD\`) and report that as baseSource "origin-head". If neither resolves → BLOCKED.`,
  `3. Create the worktree with worktrunk when the project is wired for it (\`command -v wt\` succeeds AND \`.config/wt.toml\` exists) — worktrunk is preferred because it runs the project's hooks (copy-ignored, pre-merge gate) and allocates ports:`,
  `   a. Inspect \`wt list --format=json\` for an entry whose \`branch\` equals \`${branch}\`. If one exists, REUSE it (do not recreate): reused true, and take its \`path\`.`,
  `   b. Otherwise \`wt switch --create ${branch} --base <base> --no-cd\`. If the branch already exists without a worktree, drop --create: \`wt switch ${branch} --no-cd\`. Always pass --no-cd.`,
  `   c. Resolve the absolute path from \`wt list --format=json\` (the entry whose \`branch\` matches → \`path\`). tool "wt".`,
  `4. Fallback when worktrunk is unavailable: \`git worktree add <repo-parent>/<repo-name>-<slug> -b ${branch} <base>\` where <slug> is the branch name with any \`/\` replaced by \`-\`; tool "git". If that path already exists as a worktree, reuse it instead.`,
  `5. Verify and report EVERY path absolute: the path exists as a directory; \`git -C <path> rev-parse --abbrev-ref HEAD\` equals \`${branch}\`; \`git -C <path> status --porcelain\` is empty. Any mismatch → BLOCKED.`,
  `6. Do not run package installs or build steps — worktrunk's copy-ignored hook handles gitignored state.`,
  ``,
  `Return the schema. On BLOCKED, return worktreePath "" and never guess a path.`,
].join("\n");

const prep = await agent(prepPrompt, {
  agentType: "ticket-planner",
  label: "prepare",
  schema: prepSchema,
});

const worktreePath = prep && typeof prep.worktreePath === "string" ? prep.worktreePath.trim() : "";
const prepared = Boolean(prep) && prep.status === "COMPLETED" && worktreePath !== "" && prep.cleanRoot === true;

if (!prepared) {
  const reason =
    (prep && prep.summary) || "Prepare node failed to produce a usable worktree (no output from the subagent).";
  log(`converge-goal: prepare failed — ${reason}`);
  return {
    status: "BLOCKED",
    converged: false,
    attempts: 0,
    maxAttempts,
    task,
    worktree: null,
    touchedFiles: [],
    ledger: [{ attempt: 0, stage: "prepare", failed: true, feedback: reason, issues: (prep && prep.issues) || [] }],
    summary: `Blocked before round 1: ${reason}`,
  };
}

const worktree = {
  path: worktreePath,
  branch: (prep && prep.branch) || branch,
  base: (prep && prep.base) || requestedBase,
  tool: prep.tool,
  reused: prep.reused === true,
};
log(
  `converge-goal: worktree ready — ${worktree.path} (branch ${worktree.branch}, base ${worktree.base}, tool ${worktree.tool}${worktree.reused ? ", reused" : ""})`,
);

/**
 * The isolation contract every downstream node receives. It is prose because the runtime
 * does not forward a per-agent cwd (see the file header, trap 1) — the worktree has to be
 * carried by absolute paths and command prefixes instead.
 */
const workspace = [
  `## Workspace contract (binding)`,
  `Worktree — do ALL work here: ${worktree.path}`,
  `Branch: ${worktree.branch} | Base: ${worktree.base}`,
  `Session root — never edit, commit, or run stack commands there: ${root}`,
  `pi-dynamic-workflows does not forward a per-agent cwd, so your shell starts in the session root.`,
  `Therefore: prefix every shell command with \`cd ${worktree.path} && \` (or address the tree with \`git -C ${worktree.path}\`),`,
  `and pass absolute paths under ${worktree.path} to read/edit/write.`,
  `First command — \`cd ${worktree.path} && git rev-parse --abbrev-ref HEAD\` must print \`${worktree.branch}\`; if it does not, stop and return status BLOCKED.`,
  `The session root must stay clean: \`git -C ${root} status --porcelain --untracked-files=no\` stays empty.`,
].join("\n");

phase("Iterate & Gate");

const outcome = await gate(
  async (feedback, attempt) => {
    const roundNumber = attempt + 1;
    log(`converge-goal: entering round ${roundNumber}/${maxAttempts}`);

    // Step A: Developer Implementation / Remediation
    const devPrompt = [
      `Task: ${task}`,
      `Round: ${roundNumber} of ${maxAttempts}`,
      stackHint ? `Project Stack: ${stackHint}` : "",
      evalDir ? `Eval Criteria Directory: ${evalDir}` : "",
      feedback ? `\n[FEEDBACK FROM PREVIOUS ROUND - REMEDIATION REQUIRED]\n${feedback}\n` : "",
      workspace,
      `Implement minimal changes with failing test first (TDD). Commit on \`${worktree.branch}\` inside the worktree using Conventional Commits (add \`Closes #NN\` when the task names an issue). Never push.`,
      `Return schema with filesChanged (absolute worktree paths) and summary.`,
    ]
      .filter(Boolean)
      .join("\n");

    const devResult = await agent(devPrompt, {
      agentType: "developer",
      label: `dev:round-${roundNumber}`,
      schema: devSchema,
    });

    if (!devResult) {
      log(`converge-goal: developer returned null (unrecoverable or aborted)`);
      return { ok: false, stage: "developer", feedback: "Developer subagent failed to produce output." };
    }

    if (devResult.status === "BLOCKED") {
      log(`converge-goal: developer declared BLOCKED`);
      return { ok: false, stage: "developer", blocked: true, feedback: devResult.summary };
    }

    if (Array.isArray(devResult.filesChanged)) {
      touchedFiles = Array.from(new Set([...touchedFiles, ...devResult.filesChanged]));
    }

    // Step B: Deterministic Gate (eval-gate & stack test runners)
    const gatePrompt = [
      `Run deterministic verification for task: "${task}"`,
      workspace,
      `Touched files: ${JSON.stringify(touchedFiles)}`,
      evalDir ? `Eval Directory: ${evalDir}` : "",
      stackHint ? `Stack: ${stackHint}` : "",
      `Discover the commands from the project's own manifests inside the worktree (package.json / pyproject.toml / Cargo.toml / go.mod); run the full suite from \`${worktree.path}\`.`,
      `Every phase must include these two isolation checks, which fail the round when they fail:`,
      `  - \`git -C ${worktree.path} rev-parse --abbrev-ref HEAD\` prints \`${worktree.branch}\` (phase name "worktree-branch").`,
      `  - \`git -C ${root} status --porcelain --untracked-files=no\` is empty, i.e. no tracked change leaked into the session root (phase name "root-untouched").`,
      `Then the stack gates: typecheck, tests, lint, format check, build. Return evidence as { command, ok, exitCode, tail } with tails capped at 20 lines.`,
      `Never fix anything yourself and never run \`wt merge\`.`,
    ]
      .filter(Boolean)
      .join("\n");

    const gateResult = await agent(gatePrompt, {
      agentType: "gate-runner",
      label: `gate:round-${roundNumber}`,
      schema: gateSchema,
    });

    const gatePassed = gateResult && gateResult.ok === true;
    const failedPhases = (gateResult && gateResult.phases ? gateResult.phases : []).filter((p) => !p.ok);

    if (!gatePassed || failedPhases.length > 0) {
      const gateDiagnostics = failedPhases
        .map((p) => `Check '${p.name}' failed (${p.command}):\n${p.tail || "No output"}`)
        .join("\n\n");
      const feedbackMsg = `Deterministic gate failed:\n${gateDiagnostics || (gateResult && gateResult.summary) || "Unknown test failure"}`;

      ledger.push({
        attempt: roundNumber,
        devSummary: devResult.summary,
        gatePassed: false,
        reviewPassed: false,
        failingStage: "gate-runner",
        feedback: feedbackMsg,
      });

      return { ok: false, stage: "gate-runner", feedback: feedbackMsg };
    }

    // Step C: Semantic Crux Code Review
    const reviewPrompt = [
      `Audit code changes for Crux invariants (refutability, domain state safety, clean boundaries).`,
      `Task / Goal: ${task}`,
      workspace,
      `Diff under review — read it with \`git -C ${worktree.path} diff ${worktree.base}...HEAD\` plus \`git -C ${worktree.path} log --oneline ${worktree.base}..HEAD\`.`,
      `Touched files: ${JSON.stringify(touchedFiles)}`,
      `Deterministic gate passed. Focus exclusively on semantic correctness and invariant violations.`,
    ].join("\n");

    const reviewResult = await agent(reviewPrompt, {
      agentType: "code-reviewer",
      label: `review:round-${roundNumber}`,
      schema: reviewSchema,
    });

    const blockerIssues =
      (reviewResult && reviewResult.issues
        ? reviewResult.issues
        : []
      ).filter((i) => i.severity === "P1" || i.severity === "P2");
    const reviewPassed = reviewResult && reviewResult.route === "continue" && blockerIssues.length === 0;

    if (!reviewPassed) {
      const issueDetails = blockerIssues
        .map((i) => `[${i.severity}] ${i.file}:${i.line || 0} - ${i.defect}\nRemediation: ${i.remediation}`)
        .join("\n\n");
      const feedbackMsg = `Semantic code-review reported Crux violations:\n${issueDetails || (reviewResult && reviewResult.summary) || "Remediation needed"}`;

      ledger.push({
        attempt: roundNumber,
        devSummary: devResult.summary,
        gatePassed: true,
        reviewPassed: false,
        failingStage: "code-reviewer",
        feedback: feedbackMsg,
      });

      return { ok: false, stage: "code-reviewer", feedback: feedbackMsg };
    }

    // Step D: All Gates Green
    ledger.push({
      attempt: roundNumber,
      devSummary: devResult.summary,
      gatePassed: true,
      reviewPassed: true,
      failingStage: null,
      feedback: null,
    });

    return {
      ok: true,
      devResult,
      gateResult,
      reviewResult,
    };
  },
  (result) => {
    // gate() validator requires an object returning { ok: boolean, feedback?: string }
    if (!result || !result.ok) {
      if (result && result.blocked) {
        return { ok: false, feedback: `BLOCKED: ${result.feedback}` };
      }
      return { ok: false, feedback: (result && result.feedback) || "Round failed verification gate." };
    }
    return { ok: true };
  },
  { attempts: maxAttempts },
);

phase("Finalize");

const finalStatus = outcome.ok ? "CONVERGED" : outcome.value && outcome.value.blocked ? "BLOCKED" : "EXHAUSTED";
log(
  `converge-goal: workflow finished with status: ${finalStatus} (${outcome.attempts} attempts); worktree left in place at ${worktree.path} on ${worktree.branch}`,
);

return {
  status: finalStatus,
  converged: outcome.ok,
  attempts: outcome.attempts,
  maxAttempts,
  task,
  // The worktree is deliberately NOT removed: it holds this run's commits and is the
  // handoff point for review/merge (`wt merge` or a PR). Merge/commit ownership stays
  // with the operator — this workflow never merges and never opens a PR.
  worktree,
  root,
  touchedFiles,
  ledger,
  summary: outcome.ok
    ? `Task converged in ${outcome.attempts} attempt(s) with all gates passed. Worktree: ${worktree.path} (branch ${worktree.branch}, base ${worktree.base}).`
    : `Task terminated with status ${finalStatus}: ${(outcome.value && outcome.value.feedback) || "Exhausted attempt limit."} Worktree left in place: ${worktree.path} (branch ${worktree.branch}).`,
};
