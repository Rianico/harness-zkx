/**
 * converge-goal.js — AFK goal convergence loop for pi-dynamic-workflows.
 *
 * Topology: Developer ➔ Deterministic Gate (eval-gate / stack tests) ➔ Semantic Review (Crux invariants)
 * Cyclic control helper: gate(thunk, validator, { attempts })
 */

export const meta = {
  name: "converge-goal",
  description: "Autonomous iterative goal convergence loop gated by eval-gate and crux code-review",
  phases: [
    { title: "Plan & Prepare" },
    { title: "Iterate & Gate" },
    { title: "Finalize" },
  ],
};

// 1. Resolve arguments
const task = args && typeof args.task === "string" ? args.task : "Complete the requested coding task.";
const maxAttempts = args && Number.isInteger(args.maxAttempts) ? Math.max(1, Math.min(args.maxAttempts, 10)) : 5;
const evalDir = args && typeof args.evalDir === "string" ? args.evalDir : null;
const stackHint = args && typeof args.stack === "string" ? args.stack : null;

// 2. Structured Schemas
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
    route: { type: "string", enum: ["continue", "remediate", "blocked"] },
    ok: { type: "boolean" },
    artifacts: { type: "array" },
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
  required: ["summary", "status", "ok"],
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

phase("Plan & Prepare");
log(`converge-goal: starting AFK run for task: "${task}" (maxAttempts: ${maxAttempts})`);

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
      `Implement minimal changes with failing test first (TDD). Return schema with filesChanged and summary.`,
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
      `Touched files: ${JSON.stringify(touchedFiles)}`,
      evalDir ? `Eval Directory: ${evalDir}` : "",
      stackHint ? `Stack: ${stackHint}` : "",
      `Execute test suites, typechecks, and linters. Return evidence with raw command tails.`,
    ]
      .filter(Boolean)
      .join("\n");

    const gateResult = await agent(gatePrompt, {
      agentType: "gate-runner",
      label: `gate:round-${roundNumber}`,
      schema: gateSchema,
    });

    const gatePassed = gateResult && gateResult.ok === true;
    const checkList = gateResult?.checks ?? gateResult?.phases ?? [];
    const failedChecks = checkList.filter((p) => !p.ok);

    if (!gatePassed || failedChecks.length > 0) {
      const gateDiagnostics = failedChecks
        .map((p) => `Check '${p.name}' failed (${p.command}):\n${p.tail || "No output"}`)
        .join("\n\n");
      const feedbackMsg = `Deterministic gate failed:\n${gateDiagnostics || gateResult?.summary || "Unknown test failure"}`;

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
      `Touched files: ${JSON.stringify(touchedFiles)}`,
      `Deterministic gate passed. Focus exclusively on semantic correctness and invariant violations.`,
    ].join("\n");

    const reviewResult = await agent(reviewPrompt, {
      agentType: "code-reviewer",
      label: `review:round-${roundNumber}`,
      schema: reviewSchema,
    });

    const blockerIssues =
      reviewResult?.issues?.filter((i) => i.severity === "P1" || i.severity === "P2") ?? [];
    const reviewPassed = reviewResult && reviewResult.route === "continue" && blockerIssues.length === 0;

    if (!reviewPassed) {
      const issueDetails = blockerIssues
        .map((i) => `[${i.severity}] ${i.file}:${i.line || 0} - ${i.defect}\nRemediation: ${i.remediation}`)
        .join("\n\n");
      const feedbackMsg = `Semantic code-review reported Crux violations:\n${issueDetails || reviewResult?.summary || "Remediation needed"}`;

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
      if (result?.blocked) {
        return { ok: false, feedback: `BLOCKED: ${result.feedback}` };
      }
      return { ok: false, feedback: result?.feedback || "Round failed verification gate." };
    }
    return { ok: true };
  },
  { attempts: maxAttempts },
);

phase("Finalize");

const finalStatus = outcome.ok ? "CONVERGED" : outcome.value?.blocked ? "BLOCKED" : "EXHAUSTED";
log(`converge-goal: workflow finished with status: ${finalStatus} (${outcome.attempts} attempts)`);

return {
  status: finalStatus,
  converged: outcome.ok,
  attempts: outcome.attempts,
  maxAttempts,
  task,
  touchedFiles,
  ledger,
  summary: outcome.ok
    ? `Task converged in ${outcome.attempts} attempt(s) with all gates passed.`
    : `Task terminated with status ${finalStatus}: ${outcome.value?.feedback || "Exhausted attempt limit."}`,
};
