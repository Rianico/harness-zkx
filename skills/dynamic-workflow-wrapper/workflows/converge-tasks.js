/**
 * converge-tasks.js — AFK convergence loop over a task list for pi-dynamic-workflows.
 *
 * Topology: Plan (ticket-planner) ➔ Prepare (admission + integration worktree) ➔
 *   per task [allocate copy ➔ developer ➔ deterministic gate ➔ crux review ➔ one merge attempt]
 *   ➔ Finalize (composite gate on the integration worktree)
 * Cyclic control helper: gate(thunk, validator, { attempts }) — one round budget per task.
 *
 * Delivery contract: the run ends at a verified LOCAL branch. It never pushes and never opens
 * a PR; `nextActions` names the operator step (merger Mode D). Nothing external is emitted
 * unattended, so a mis-verified run cannot reach a remote.
 *
 * Isolation contract — runtime and tooling facts that fix the shape of this file. Do not
 * "simplify" them away:
 *
 *   1. `agent(prompt, { cwd })` is NOT forwarded. The runtime derives a subagent cwd from
 *      `options.isolation === "worktree"` only, and the documented agent option list has no
 *      `cwd` — a script-level cwd is silently ignored. Every worktree is therefore an explicit
 *      contract in the prompt: absolute paths for read/edit/write, `cd <path> &&` or
 *      `git -C <path>` for every shell command.
 *   2. The built-in `isolation: "worktree"` is per-CALL and removed in a `finally` after each
 *      agent returns. A convergence loop accumulates commits across rounds, so per-call
 *      throwaway worktrees cannot be used here.
 *   3. The session root is never the integration branch. The integration branch gets its OWN
 *      worktree, so one universal `root-untouched` guard holds for every node and the
 *      operator's checked-out branch is never switched behind their back.
 *   4. `merge_copy.py` runs `wt merge` without `--no-remove`, so a SUCCESSFUL merge removes the
 *      task copy. A failed merge leaves it in place — which is exactly why repair and
 *      re-verification must happen before a retry, never after a success.
 *
 * Topology rule: the task list runs SEQUENTIALLY in dependency order. Every merge mutates one
 * integration branch, so concurrent task writers would race; `parallel()` is deliberately not
 * used for the task loop.
 *
 * Merge authority: the merger attempts the merge ONCE per call and never retries after a
 * repair. A repaired task copy must be re-verified (gate + review) before the next attempt, and
 * only this workflow can sequence that — so the attempt budget lives here, not in the role.
 *
 * Stagnation breaker: a round that reproduces the identical worktree diff AND the identical
 * failing checks as the previous round cannot converge — the fault is in the eval script or the
 * environment, not the code — so the loop stops immediately with `BLOCKED (eval-gate
 * stagnation)` instead of burning the remaining round budget. The gate reports a `diff-hash`
 * phase (`git diff <base>...HEAD | git hash-object --stdin`) purely so this is decidable.
 *
 * Timeouts: the workflow runtime exposes no clock (the VM neuters `Date`), so this script
 * cannot measure a cumulative run budget. `runTimeoutMs` (default 2h) bounds every agent call in
 * the run and `taskTimeoutMs` (opt-in) bounds each call belonging to one task; an explicit
 * `runTimeoutMs: null` disables the ceiling. A true cumulative run budget is still the `workflow`
 * tool's `agentTimeoutMs` input.
 *
 * Finalize changelog sync: after every task merges, a hand-drifted `## [Unreleased]` block makes
 * the composite gate dirty the tree and marks a fully successful run `BLOCKED`. The final gate
 * reports the drift as a read-only `changelog-check` phase; when that is the ONLY failing phase
 * the workflow dispatches one idempotent `chore: sync changelog unreleased section` commit and
 * re-runs the composite gate exactly once.
 */

export const meta = {
  name: 'converge-tasks',
  description: 'AFK convergence loop over one or more tasks: per-task developer, deterministic gate, crux review, merged into a local integration branch — never pushes, never opens a PR',
  phases: [{ title: 'Plan & Prepare' }, { title: 'Integrate & Gate' }, { title: 'Finalize' }]
};

// 1. Arguments
const rawArgs = args && typeof args === 'object' ? args : {};
const maxRounds = Number.isInteger(rawArgs.maxRounds) ? Math.max(1, Math.min(rawArgs.maxRounds, 10)) : 5;
const maxMergeAttempts = Number.isInteger(rawArgs.maxMergeAttempts) ? Math.max(1, Math.min(rawArgs.maxMergeAttempts, 3)) : 2;
// Per-agent timeouts. The runtime has no clock, so `runTimeoutMs` is a per-call ceiling, not a
// cumulative budget (pass `agentTimeoutMs` to the workflow tool for that). 2h by default so a
// hung subagent cannot run all night; `runTimeoutMs: null` disables the ceiling explicitly.
const DEFAULT_RUN_TIMEOUT_MS = 7_200_000;
const taskTimeoutMs = Number.isInteger(rawArgs.taskTimeoutMs) && rawArgs.taskTimeoutMs > 0 ? rawArgs.taskTimeoutMs : null;
const runTimeoutMs =
  rawArgs.runTimeoutMs === null
    ? null
    : Number.isInteger(rawArgs.runTimeoutMs) && rawArgs.runTimeoutMs > 0
      ? rawArgs.runTimeoutMs
      : DEFAULT_RUN_TIMEOUT_MS;
const stackHint = typeof rawArgs.stack === 'string' && rawArgs.stack.trim() ? rawArgs.stack.trim() : null;
const evalDir = typeof rawArgs.evalDir === 'string' && rawArgs.evalDir.trim() ? rawArgs.evalDir.trim() : null;
const requestedBase = typeof rawArgs.base === 'string' && rawArgs.base.trim() ? rawArgs.base.trim() : 'main';
const requestedIntegration = typeof rawArgs.integration === 'string' && rawArgs.integration.trim() ? rawArgs.integration.trim() : null;
const requestedBranch = typeof rawArgs.branch === 'string' && rawArgs.branch.trim() ? rawArgs.branch.trim() : null;
const root = typeof cwd === 'string' ? cwd : process.cwd();

/** Attach the resolved timeout ceiling to an agent call, or leave it at the run default. */
function callOptions(base, perTask = false) {
  const timeoutMs = perTask ? (taskTimeoutMs ?? runTimeoutMs) : runTimeoutMs;
  return timeoutMs === null ? base : { ...base, timeoutMs };
}

const knownGotchas = Array.isArray(rawArgs.knownGotchas)
  ? rawArgs.knownGotchas.filter(g => typeof g === 'string' && g.trim()).map(g => g.trim())
  : [];
const suggestions = [];

function recordSuggestions(source, items) {
  if (!Array.isArray(items)) return;
  for (const item of items) {
    if (!item) continue;
    if (typeof item === 'string' && item.trim()) {
      suggestions.push({
        source,
        category: 'General',
        observation: item.trim(),
        impact: '',
        workaround: '',
        suggestion: item.trim()
      });
    } else if (typeof item === 'object') {
      suggestions.push({
        source,
        category: typeof item.category === 'string' ? item.category : 'General',
        observation: typeof item.observation === 'string' ? item.observation : '',
        impact: typeof item.impact === 'string' ? item.impact : '',
        workaround: typeof item.workaround === 'string' ? item.workaround : '',
        suggestion: typeof item.suggestion === 'string' ? item.suggestion : ''
      });
    }
  }
}

function gotchasBlock() {
  return knownGotchas.length > 0
    ? `Known Environment Gotchas / Tips:\n${knownGotchas.map(g => `- ${g}`).join('\n')}`
    : '';
}

function slugify(value, limit = 48) {
  const slug = String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, limit)
    .replace(/-+$/g, '');
  return slug || 'task';
}

function branchFor(id) {
  return `task/${slugify(id, 40)}`;
}

const incoming = Array.isArray(rawArgs.tasks) && rawArgs.tasks.length > 0 ? rawArgs.tasks : [{ kind: 'task', ref: 'Complete the requested coding task.', dependsOn: [] }];

const tasks = [];
const duplicateIds = [];
const seenIds = new Set();
for (let i = 0; i < incoming.length; i += 1) {
  const entry = incoming[i] && typeof incoming[i] === 'object' ? incoming[i] : {};
  const ref = typeof entry.ref === 'string' && entry.ref.trim() ? entry.ref.trim() : `task ${i + 1}`;
  const id = typeof entry.id === 'string' && entry.id.trim() ? entry.id.trim() : ref;
  if (seenIds.has(id)) {
    duplicateIds.push(id);
    continue;
  }
  seenIds.add(id);
  const deps = Array.isArray(entry.dependsOn) ? entry.dependsOn : [];
  tasks.push({
    id,
    ref,
    kind: entry.kind === 'issue' ? 'issue' : 'task',
    dependsOn: deps.filter(dep => typeof dep === 'string' && dep.trim()).map(dep => dep.trim()),
    acceptance: [],
    issue: entry.kind === 'issue' ? ref : '',
    branch: tasks.length === 0 && requestedBranch ? requestedBranch : branchFor(id)
  });
}

const taskById = new Map(tasks.map(task => [task.id, task]));
const integrationWanted = tasks.length > 1 || requestedIntegration !== null;
const integrationBranch = requestedIntegration || `dev/${slugify(rawArgs.batch || tasks[0].id, 40)}`;
const reuseIntegration = requestedIntegration !== null;

// 2. Structured schemas
const planSchema = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    status: { type: 'string', enum: ['COMPLETED', 'BLOCKED'] },
    tasks: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          ref: { type: 'string' },
          issue: { type: 'string' },
          acceptance: { type: 'array', items: { type: 'string' } },
          dependsOn: { type: 'array', items: { type: 'string' } },
          notes: { type: 'string' }
        },
        required: ['id', 'ref', 'acceptance', 'dependsOn']
      }
    },
    issues: { type: 'array', items: { type: 'string' } },
    suggestions: { type: 'array' }
  },
  required: ['summary', 'status', 'tasks', 'issues']
};

const prepSchema = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    status: { type: 'string', enum: ['COMPLETED', 'BLOCKED'] },
    cleanRoot: { type: 'boolean' },
    base: { type: 'string' },
    baseSource: { type: 'string' },
    integrationBranch: { type: 'string' },
    integrationPath: { type: 'string' },
    integrationTool: { type: 'string', enum: ['wt', 'git', 'none'] },
    integrationReused: { type: 'boolean' },
    preMergeHook: { type: 'boolean' },
    rootBranch: { type: 'string' },
    issues: { type: 'array', items: { type: 'string' } },
    suggestions: { type: 'array' }
  },
  required: ['summary', 'status', 'cleanRoot', 'base', 'baseSource', 'integrationBranch', 'integrationPath', 'integrationTool', 'integrationReused', 'preMergeHook', 'rootBranch', 'issues']
};

const allocSchema = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    status: { type: 'string', enum: ['COMPLETED', 'BLOCKED'] },
    worktreePath: { type: 'string' },
    branch: { type: 'string' },
    base: { type: 'string' },
    baseSource: { type: 'string' },
    tool: { type: 'string', enum: ['wt', 'git'] },
    reused: { type: 'boolean' },
    issues: { type: 'array', items: { type: 'string' } },
    suggestions: { type: 'array' }
  },
  required: ['summary', 'status', 'worktreePath', 'branch', 'base', 'baseSource', 'tool', 'reused', 'issues']
};

const devSchema = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    status: { type: 'string', enum: ['COMPLETED', 'BLOCKED'] },
    artifacts: {
      type: 'array',
      items: {
        type: 'object',
        properties: { path: { type: 'string' }, kind: { type: 'string' } },
        required: ['path', 'kind']
      }
    },
    commits: { type: 'array', items: { type: 'string' } },
    filesChanged: { type: 'array', items: { type: 'string' } },
    checks: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          command: { type: 'string' },
          ok: { type: 'boolean' },
          exitCode: { type: 'integer' },
          tail: { type: 'string' }
        },
        required: ['name', 'command', 'ok']
      }
    },
    issues: { type: 'array', items: { type: 'string' } },
    suggestions: { type: 'array' }
  },
  required: ['summary', 'status', 'filesChanged', 'issues']
};

const gateSchema = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    status: { type: 'string', enum: ['COMPLETED', 'BLOCKED', 'REJECTED'] },
    ok: { type: 'boolean' },
    artifacts: { type: 'array' },
    phases: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          command: { type: 'string' },
          ok: { type: 'boolean' },
          exitCode: { type: 'integer' },
          tail: { type: 'string' }
        },
        required: ['name', 'command', 'ok']
      }
    },
    issues: { type: 'array' },
    suggestions: { type: 'array' }
  },
  required: ['summary', 'status', 'ok', 'phases', 'issues']
};

const reviewSchema = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    status: { type: 'string', enum: ['COMPLETED', 'BLOCKED'] },
    route: { type: 'string', enum: ['continue', 'remediate', 'blocked'] },
    score: { type: 'integer' },
    artifacts: { type: 'array' },
    issues: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          severity: { type: 'string', enum: ['P1', 'P2', 'P3'] },
          file: { type: 'string' },
          line: { type: 'integer' },
          invariant: { type: 'string' },
          defect: { type: 'string' },
          remediation: { type: 'string' }
        },
        required: ['id', 'severity', 'file', 'defect', 'remediation']
      }
    },
    priorIssues: { type: 'array' },
    suggestions: { type: 'array' }
  },
  required: ['summary', 'status', 'route', 'issues']
};

const mergeSchema = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    status: { type: 'string', enum: ['COMPLETED', 'BLOCKED'] },
    merged: { type: 'boolean' },
    outcome: { type: 'string', enum: ['MERGED', 'CONFLICT', 'GATE_FAILED', 'BLOCKED'] },
    attempts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          exitCode: { type: 'integer' },
          command: { type: 'string' },
          tail: { type: 'string' }
        },
        required: ['exitCode', 'command', 'tail']
      }
    },
    repaired: { type: 'boolean' },
    integrationBranch: { type: 'string' },
    taskBranch: { type: 'string' },
    worktreePath: { type: 'string' },
    issues: { type: 'array', items: { type: 'string' } },
    suggestions: { type: 'array' }
  },
  required: ['summary', 'status', 'merged', 'outcome', 'attempts', 'repaired', 'integrationBranch', 'taskBranch', 'worktreePath', 'issues']
};

const changelogSyncSchema = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    status: { type: 'string', enum: ['COMPLETED', 'BLOCKED'] },
    synced: { type: 'boolean' },
    commands: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          command: { type: 'string' },
          ok: { type: 'boolean' },
          exitCode: { type: 'integer' },
          tail: { type: 'string' }
        },
        required: ['command', 'ok']
      }
    },
    issues: { type: 'array', items: { type: 'string' } },
    suggestions: { type: 'array' }
  },
  required: ['summary', 'status', 'synced', 'issues']
};

// 3. Execution ledger
const ledger = [];
const taskRows = [];
const touchedFiles = new Set();

function accept(prompt, options) {
  return agent(prompt, options);
}

function report(message) {
  log(`converge-tasks: ${message}`);
}

/** First phase carrying `name`, or undefined when the gate did not report it. */
function phaseByName(result, name) {
  const phases = result && Array.isArray(result.phases) ? result.phases : [];
  return phases.find(phase => phase && phase.name === name);
}

/** Names of every non-green phase, in report order. */
function failedPhaseNames(result) {
  const phases = result && Array.isArray(result.phases) ? result.phases : [];
  return phases.filter(phase => phase && phase.ok !== true).map(phase => String(phase.name));
}

/**
 * Identity of a failed round: the worktree diff plus the exact failing checks. Two consecutive
 * rounds with the same signature cannot converge — the code did not change and the same checks
 * still fail — so the retry loop stops instead of burning the rest of the budget.
 */
function failureSignature(diffHash, failed) {
  const detail = failed.map(phase => `${phase.name}=${String(phase.tail || '').trim()}`).join('|');
  return `${diffHash}::${detail}`;
}

/** True when changelog drift is the ONLY reason the composite gate failed. */
function changelogDriftOnly(result) {
  if (!result || result.ok === true) return false;
  const failed = failedPhaseNames(result);
  return failed.length === 1 && failed[0] === 'changelog-check';
}

function taskWorkspace(task, worktreePath, branch, base) {
  return [
    `## Workspace contract (binding)`,
    `Worktree — do ALL work here: ${worktreePath}`,
    `Task branch: ${branch} | Base: ${base}`,
    `Session root — never edit, commit, or run stack commands there: ${root}`,
    `pi-dynamic-workflows does not forward a per-agent cwd, so your shell starts in the session root.`,
    `Therefore: prefix every shell command with \`cd ${worktreePath} && \` (or address the tree with \`git -C ${worktreePath}\`),`,
    `and pass absolute paths under ${worktreePath} to read/edit/write.`,
    `First command — \`cd ${worktreePath} && git rev-parse --abbrev-ref HEAD\` must print \`${branch}\`; if it does not, stop and return status BLOCKED.`,
    `The session root must stay clean and on its own branch. Admit the tree with the ephemeral-tolerant check that ignores machine-generated caches, and export \`PYTHONDONTWRITEBYTECODE=1\` so Python never creates \`__pycache__\` here:`,
    `  \`git -C ${worktreePath} status --porcelain --untracked-files=all | grep -vE '(__pycache__/|\\.pyc$|\\.DS_Store$|\\.lsz/)' || true\` must print nothing; \`git -C ${root} status --porcelain --untracked-files=no\` stays empty.`
  ].join('\n');
}

function acceptanceBlock(task) {
  if (!task.acceptance || task.acceptance.length === 0) return `Acceptance criteria: derive them from the task statement and state them in your summary.`;
  return [`Acceptance criteria (from the plan):`, ...task.acceptance.map(item => `  - ${item}`)].join('\n');
}

// 4. Plan & Prepare
phase('Plan & Prepare');
report(
  `starting run — ${tasks.length} task(s), ${integrationWanted ? `integration ${integrationBranch}` : 'no integration branch'}, base ${requestedBase}, ${maxRounds} round(s) per task, ${maxMergeAttempts} merge attempt(s) per task`
);

const planPrompt = [
  `You are the Plan node of an AFK convergence run. You expand each task reference into an executable spec.`,
  `You never create branches or worktrees, you never write repository files, and you never implement.`,
  gotchasBlock(),
  ``,
  `Session root (read-only for you): ${root}`,
  `Tasks as declared (JSON): ${JSON.stringify(tasks.map(task => ({ id: task.id, kind: task.kind, ref: task.ref, dependsOn: task.dependsOn })))}`,
  duplicateIds.length > 0 ? `The caller repeated these ids, which were collapsed: ${JSON.stringify(duplicateIds)}` : '',
  ``,
  `For each task:`,
  `  - keep the same \`id\` and \`ref\`;`,
  `  - for \`kind: "issue"\`, read the real issue with \`gh issue view <n> --json title,body,labels --repo <owner/repo>\` and put the number in \`issue\`; do not guess its content;`,
  `  - write \`acceptance\` as the concrete, checkable criteria that BOTH the deterministic gate and the reviewer will use (3-6 bullets);`,
  `  - every criterion that greps for a token, symbol, or identifier must anchor it with word boundaries (\`\\b<identifier>\\b\`, or \`rg -w\`) — a bare substring false-reds on unrelated symbols and burns the round budget; to measure added/removed lines use \`git diff --numstat\`, never a \`grep -cE '^-[^-]'\` style diff-line regex;`,
  `  - report \`dependsOn\` only for dependencies you can evidence (a shared file, a stated prerequisite, an issue link). Use task ids as they appear above.`,
  `You may read the repository to ground the criteria. Do not paste file bodies into your reply.`,
  `If a task reference is unintelligible, contradicts another task, or cannot be planned without a human decision, set status BLOCKED and say which one.`,
  `Return the schema.`
]
  .filter(Boolean)
  .join('\n');

const plan = await accept(planPrompt, callOptions({ agentType: 'ticket-planner', label: 'plan', schema: planSchema }));
recordSuggestions('ticket-planner', plan && plan.suggestions);
const planRows = plan && Array.isArray(plan.tasks) ? plan.tasks : [];
const planIssues = plan && Array.isArray(plan.issues) ? plan.issues : [];

for (const task of tasks) {
  const row = planRows.find(entry => entry && (entry.id === task.id || entry.ref === task.ref));
  if (!row) continue;
  task.acceptance = Array.isArray(row.acceptance) ? row.acceptance.filter(item => typeof item === 'string') : [];
  if (typeof row.issue === 'string' && row.issue.trim()) task.issue = row.issue.trim();
  const planned = Array.isArray(row.dependsOn) ? row.dependsOn.filter(dep => typeof dep === 'string') : [];
  for (const dep of planned) {
    if (dep === task.id) continue;
    if (!taskById.has(dep)) {
      planIssues.push(`${task.id}: planner declared dependency "${dep}", which is not a task in this run — ignored`);
      continue;
    }
    if (!task.dependsOn.includes(dep)) task.dependsOn.push(dep);
  }
}

const unknownDeps = [];
for (const task of tasks) {
  for (const dep of task.dependsOn) if (!taskById.has(dep)) unknownDeps.push(`${task.id} -> ${dep}`);
}

function resolveOrder() {
  const ordered = [];
  while (ordered.length < tasks.length) {
    const ready = tasks.filter(task => !ordered.includes(task.id) && task.dependsOn.every(dep => ordered.includes(dep)));
    if (ready.length === 0) {
      return {
        ok: false,
        order: ordered,
        reason: `dependency cycle among: ${tasks
          .filter(task => !ordered.includes(task.id))
          .map(task => task.id)
          .join(', ')}`
      };
    }
    for (const task of ready) ordered.push(task.id);
  }
  return { ok: true, order: ordered, reason: '' };
}

const orderResult = resolveOrder();
const planBlocked = !plan || plan.status === 'BLOCKED';
const admissionFailure = planBlocked
  ? `Plan node blocked: ${(plan && plan.summary) || 'no output from the planner'}`
  : unknownDeps.length > 0
    ? `Dependencies do not resolve: ${unknownDeps.join(', ')}`
    : orderResult.ok
      ? ''
      : orderResult.reason;

if (admissionFailure) {
  report(`planning failed — ${admissionFailure}`);
  return {
    status: 'BLOCKED',
    converged: false,
    maxRounds,
    maxMergeAttempts,
    tasks: tasks.map(task => ({ id: task.id, ref: task.ref, kind: task.kind, status: 'BLOCKED', rounds: 0, mergeAttempts: 0, issues: [admissionFailure] })),
    delivery: { mode: integrationWanted ? 'integration-branch' : 'task-branch', branch: '', base: requestedBase, worktreePath: '', verified: false },
    root,
    ledger: [{ taskId: null, round: 0, stage: 'plan', ok: false, feedback: admissionFailure }],
    planIssues,
    nextActions: ['Resolve the plan or dependency problem above, then re-run.'],
    summary: `Blocked before any work: ${admissionFailure}`,
    suggestions
  };
}

report(`plan complete — order: ${orderResult.order.join(' -> ')}`);

const prepPrompt = [
  `You are the Prepare node of an AFK convergence run. You perform admission checks and allocate the ONE integration worktree.`,
  `You do not implement, gate, review, or merge, and you never modify repository files.`,
  gotchasBlock(),
  ``,
  `Session root (your cwd, must stay untouched): ${root}`,
  `Requested base: ${requestedBase}`,
  `Integration branch requested: ${integrationWanted ? integrationBranch : 'none — this run has a single task and merges nothing'}`,
  reuseIntegration
    ? `The integration name was supplied by the operator, so reusing an existing branch/worktree of that name is authorized.`
    : `The integration name was derived, NOT supplied: if a branch or worktree of that name already exists, do NOT reuse it — report status BLOCKED with the existing path, because stacking on an earlier run's unverified commits is an operator decision.`,
  ``,
  `Procedure — run each step and put the exact failing command plus its output in \`issues\` when one fails:`,
  ``,
  `1. Admission: tolerate the untracked set every gate tolerates — machine-generated caches (\`__pycache__/\`, \`*.pyc\`, \`.DS_Store\`) and paths under \`.lsz/\`. Run \`git status --porcelain --untracked-files=all | grep -vE '(__pycache__/|\\.pyc$|\\.DS_Store$|\\.lsz/)' || true\`: any output means the root is dirty → status BLOCKED, cleanRoot false. Also \`export PYTHONDONTWRITEBYTECODE=1\` so a stray interpreter stops creating \`__pycache__\` mid-run.`,
  `2. Record \`git -C ${root} rev-parse --abbrev-ref HEAD\` as rootBranch — the session root's branch must NOT change during this run.`,
  `3. Resolve the base: if \`git rev-parse --verify ${requestedBase}\` succeeds, use ${requestedBase} with baseSource "requested". Otherwise fall back to the repository default branch (\`git rev-parse --abbrev-ref origin/HEAD\`) with baseSource "origin-head". If neither resolves → BLOCKED.`,
  `4. Record whether the project body wires the merge gate: \`rg -n '^\\[pre-merge\\]' .config/wt.toml\` (or \`grep -n\`) succeeds → preMergeHook true. This decides only whether merge attempts are composite-gated; the Finalize node re-runs the full stack gate on the integration worktree either way.`,
  integrationWanted
    ? `5. Allocate the integration worktree in its OWN worktree — never in the session worktree, and never by checking out ${integrationBranch} in ${root}. Prefer worktrunk when \`command -v wt\` succeeds AND \`.config/wt.toml\` exists: inspect \`wt list --format=json 2>/dev/null\` for an entry whose \`branch\` equals ${integrationBranch} (reuse only as instructed above), otherwise \`wt switch --create ${integrationBranch} --base <base> --no-cd\`, then read the absolute \`path\` from \`wt list --format=json 2>/dev/null\` and report integrationTool "wt". Always redirect stderr: wt prints a json-schema notice there, and merging it into stdout breaks jq. The payload is a bare array on schema 1 and an \`{ items: [...] }\` envelope on schema 2, with the path at \.path or \.worktree.path — accept both. Fallback: \`git worktree add <repo-parent>/<repo-name>-<integration-slug> -b ${integrationBranch} <base>\` with integrationTool "git", reusing that path when it already exists.`
    : `5. Report integrationBranch "", integrationPath "", integrationTool "none", integrationReused false — this single-task run merges nothing.`,
  integrationWanted
    ? `6. Verify and report every path absolute: the integration path exists as a directory; \`git -C <path> rev-parse --abbrev-ref HEAD\` equals ${integrationBranch}; and the ephemeral-tolerant admission check from step 1 run against the integration path prints nothing. Any mismatch → BLOCKED.`
    : `6. Verify the session root is still clean and still on the branch you recorded.`,
  `7. Do not run package installs or build steps — worktrunk's copy-ignored hook handles gitignored state.`,
  ``,
  `Return the schema. On BLOCKED, return integrationPath "" and never guess a path.`
]
  .filter(Boolean)
  .join('\n');

const prep = await accept(prepPrompt, callOptions({ agentType: 'merger', label: 'prepare', schema: prepSchema }));
recordSuggestions('prepare', prep && prep.suggestions);
const integrationPath = prep && typeof prep.integrationPath === 'string' ? prep.integrationPath.trim() : '';
const prepared = Boolean(prep) && prep.status === 'COMPLETED' && prep.cleanRoot === true && (!integrationWanted || integrationPath !== '');

if (!prepared) {
  const reason = (prep && prep.summary) || 'Prepare node failed to produce usable admission facts (no output from the subagent).';
  report(`prepare failed — ${reason}`);
  return {
    status: 'BLOCKED',
    converged: false,
    maxRounds,
    maxMergeAttempts,
    tasks: tasks.map(task => ({ id: task.id, ref: task.ref, kind: task.kind, status: 'DEFERRED', rounds: 0, mergeAttempts: 0, issues: [reason] })),
    delivery: {
      mode: integrationWanted ? 'integration-branch' : 'task-branch',
      branch: integrationWanted ? integrationBranch : '',
      base: (prep && prep.base) || requestedBase,
      worktreePath: '',
      verified: false
    },
    root,
    ledger: [{ taskId: null, round: 0, stage: 'prepare', ok: false, feedback: reason }],
    nextActions: ['Fix the admission failure above, then re-run.'],
    summary: `Blocked before round 1: ${reason}`,
    suggestions
  };
}

const base = (prep && prep.base) || requestedBase;
const baseSource = (prep && prep.baseSource) || 'requested';
const preMergeHook = prep.preMergeHook === true;
report(`prepare complete — base ${base} (${baseSource}), integration ${integrationPath || 'none'}, pre-merge hook ${preMergeHook ? 'declared' : 'absent'}`);

// 5. Integrate & Gate — one bounded round budget per task, one merge attempt per round
phase('Integrate & Gate');

const abortedTasks = [];
let haltedBy = null;

for (const taskId of orderResult.order) {
  const task = taskById.get(taskId);

  if (haltedBy) {
    taskRows.push({ id: task.id, ref: task.ref, kind: task.kind, status: 'DEFERRED', rounds: 0, mergeAttempts: 0, branch: task.branch, worktreePath: '', issues: [`batch halted by: ${haltedBy}`] });
    abortedTasks.push(task.id);
    continue;
  }

  const allocPrompt = [
    `You are the Allocate node of an AFK convergence run. You create the copy worktree for exactly ONE task.`,
    `You do not implement, gate, review, or merge, and you never modify repository files.`,
    gotchasBlock(),
    ``,
    `Task id: ${task.id}`,
    `Task: ${task.ref}`,
    `Task branch to create or reuse: ${task.branch}`,
    integrationWanted
      ? `Base for the copy — the integration branch, so this task starts from everything merged so far: ${integrationBranch} (worktree ${integrationPath})`
      : `Base for the copy: ${base}`,
    `Session root (must stay untouched, same branch): ${root}`,
    ``,
    `Procedure:`,
    `1. Prefer worktrunk when \`command -v wt\` succeeds AND \`.config/wt.toml\` exists: inspect \`wt list --format=json 2>/dev/null\` (always redirect stderr — wt prints a json-schema notice there and merging it into stdout breaks jq; the payload is a bare array on schema 1 and an \`{ items: [...] }\` envelope on schema 2, so read \.path or \.worktree.path); if an entry already has branch \`${task.branch}\`, reuse it (reused true) rather than recreating; otherwise \`wt switch --create ${task.branch} --base <base> --no-cd\`, then read the absolute \`path\` from \`wt list --format=json 2>/dev/null\` and report tool "wt".`,
    `2. Fallback: \`git worktree add <repo-parent>/<repo-name>-<task-slug> -b ${task.branch} <base>\` where <task-slug> is the branch name with \`/\` replaced by \`-\`; reuse that path when it already exists as a worktree; tool "git".`,
    `3. Verify and report absolute paths only: the path exists as a directory, \`git -C <path> rev-parse --abbrev-ref HEAD\` equals \`${task.branch}\`, and the ephemeral-tolerant check \`git -C <path> status --porcelain --untracked-files=all | grep -vE '(__pycache__/|\\.pyc$|\\.DS_Store$|\\.lsz/)' || true\` prints nothing. Any mismatch → status BLOCKED with worktreePath "".`,
    `4. Never check out, commit, merge, or push in the session root. Never push anywhere.`,
    ``,
    `Return the schema.`
  ].join('\n');

  const alloc = await accept(allocPrompt, callOptions({ agentType: 'merger', label: `alloc:${slugify(task.id, 24)}`, schema: allocSchema }, true));
  recordSuggestions('allocate', alloc && alloc.suggestions);
  const taskPath = alloc && typeof alloc.worktreePath === 'string' ? alloc.worktreePath.trim() : '';
  const taskBranch = (alloc && alloc.branch) || task.branch;
  const taskBase = (alloc && alloc.base) || (integrationWanted ? integrationBranch : base);

  if (!alloc || alloc.status !== 'COMPLETED' || taskPath === '') {
    const reason = (alloc && alloc.summary) || 'Allocate node failed to produce a usable task worktree (no output from the subagent).';
    report(`task ${task.id}: allocation failed — ${reason}`);
    taskRows.push({ id: task.id, ref: task.ref, kind: task.kind, status: 'BLOCKED', rounds: 0, mergeAttempts: 0, branch: taskBranch, worktreePath: '', issues: [reason] });
    abortedTasks.push(task.id);
    haltedBy = `task ${task.id} could not be allocated`;
    continue;
  }

  const workspace = taskWorkspace(task, taskPath, taskBranch, taskBase);
  let mergeAttempts = 0;
  // Signature of the previous FAILED round (diff hash + failing checks); the stagnation breaker
  // trips when two consecutive failed rounds share it.
  let lastFailedSignature = '';
  report(`task ${task.id}: copy ready at ${taskPath} (branch ${taskBranch}, base ${taskBase})`);

  const outcome = await gate(
    async (feedback, attempt) => {
      const roundNumber = attempt + 1;
      const nextMergeAttempt = integrationWanted ? mergeAttempts + 1 : 0;
      report(`task ${task.id}: round ${roundNumber}/${maxRounds}${integrationWanted ? ` (merge attempt ${Math.min(nextMergeAttempt, maxMergeAttempts)}/${maxMergeAttempts} on success)` : ''}`);

      const devPrompt = [
        `Task (${task.id}): ${task.ref}`,
        task.issue ? `Issue: ${task.issue}` : '',
        `Round: ${roundNumber} of ${maxRounds}`,
        stackHint ? `Project stack: ${stackHint}` : '',
        evalDir ? `Eval criteria directory: ${evalDir}` : '',
        acceptanceBlock(task),
        feedback ? `\n[FEEDBACK FROM THE PREVIOUS ROUND — REMEDIATION REQUIRED]\n${feedback}\n` : '',
        workspace,
        gotchasBlock(),
        `Implement the minimal change with a failing test first (TDD). Keep the change inside ${taskPath}.`,
        `Commit on \`${taskBranch}\` inside the worktree using Conventional Commits${task.issue ? ` and include \`Closes ${task.issue}\`` : ''}; keep code and docs in separate commits.`,
        `Strictly observe domain vocabulary in CONTEXT.md (_Avoid_: ...); never introduce banned synonyms in code, tests, or commit messages.`,
        `Zero tooling tampering: never modify .config/wt.toml, CI workflows, or git hooks to bypass gate limits or commitlint rules.`,
        `Multi-step state updates must be atomic in a single transaction (BEGIN IMMEDIATE); hybrid disk+db operations must surface desync warnings.`,
        `The repository's pre-merge gate may require exactly one new bullet under \`## [Unreleased]\` in CHANGELOG.md — add it when the repo tracks a changelog and the task is user-visible (respecting CONTRIBUTING.md hidden types).`,
        `Never push. Return the schema with filesChanged (absolute worktree paths) and a summary that is the approach, not a status log.`
      ]
        .filter(Boolean)
        .join('\n');

      const devResult = await accept(devPrompt, callOptions({ agentType: 'developer', label: `dev:${slugify(task.id, 20)}:r${roundNumber}`, schema: devSchema }, true));
      recordSuggestions('developer', devResult && devResult.suggestions);

      if (!devResult) {
        return { ok: false, stage: 'developer', feedback: `Developer subagent returned no output for task ${task.id}.` };
      }
      if (devResult.status === 'BLOCKED') {
        return { ok: false, stage: 'developer', blocked: true, feedback: devResult.summary };
      }
      if (Array.isArray(devResult.filesChanged)) {
        for (const changed of devResult.filesChanged) if (typeof changed === 'string') touchedFiles.add(changed);
      }

      const gatePrompt = [
        `Run deterministic verification for task (${task.id}): "${task.ref}"`,
        acceptanceBlock(task),
        workspace,
        gotchasBlock(),
        `Touched files: ${JSON.stringify(Array.from(touchedFiles))}`,
        evalDir ? `Eval directory: ${evalDir}` : '',
        stackHint ? `Stack: ${stackHint}` : '',
        `Discover the commands from the project's own manifests inside the worktree (package.json / pyproject.toml / Cargo.toml / go.mod) and run the full suite from \`${taskPath}\`.`,
        `Every run must include these two isolation checks, which fail the round when they fail:`,
        `  - \`git -C ${taskPath} rev-parse --abbrev-ref HEAD\` prints \`${taskBranch}\` (phase name "worktree-branch").`,
        `  - \`git -C ${root} status --porcelain --untracked-files=no\` is empty, i.e. no tracked change leaked into the session root (phase name "root-untouched").`,
        `  - \`git -C ${taskPath} diff ${taskBase}...HEAD | git hash-object --stdin\` prints the worktree's diff hash as the FIRST line of this phase's tail (phase name "diff-hash", always ok). The workflow uses it to detect a stagnant round.`,
        `Then the stack gates: typecheck, tests, lint, format check, build. Return evidence as { command, ok, exitCode, tail } with tails capped at 20 lines.`,
        `Never fix anything yourself, never merge, never run \`wt merge\`, never push.`
      ]
        .filter(Boolean)
        .join('\n');

      const gateResult = await accept(gatePrompt, callOptions({ agentType: 'gate-runner', label: `gate:${slugify(task.id, 20)}:r${roundNumber}`, schema: gateSchema }, true));
      recordSuggestions('gate-runner', gateResult && gateResult.suggestions);
      const failedPhases = (gateResult && Array.isArray(gateResult.phases) ? gateResult.phases : []).filter(phase => !phase.ok);

      if (!gateResult || gateResult.ok !== true || failedPhases.length > 0) {
        const diagnostics = failedPhases.map(phase => `Check '${phase.name}' failed (${phase.command}):\n${phase.tail || 'No output'}`).join('\n\n');
        const diffHashPhase = phaseByName(gateResult, 'diff-hash');
        const diffHash = diffHashPhase && typeof diffHashPhase.tail === 'string' ? diffHashPhase.tail.trim().split('\n')[0] : '';
        if (diffHash) {
          const signature = failureSignature(diffHash, failedPhases);
          if (signature === lastFailedSignature) {
            const feedback = `BLOCKED (eval-gate stagnation): round ${roundNumber} produced the identical worktree diff (${diffHash.slice(0, 12)}) and the identical failing checks as the previous round, so further rounds cannot converge — the fault is in the eval criteria or the environment, not the code.\n\n${diagnostics}`;
            ledger.push({ taskId: task.id, round: roundNumber, stage: 'gate-runner', ok: false, stalled: true, feedback });
            return { ok: false, stage: 'gate-runner', blocked: true, feedback };
          }
          lastFailedSignature = signature;
        }
        const feedback = `Deterministic gate failed:\n${diagnostics || (gateResult && gateResult.summary) || 'Unknown test failure'}`;
        ledger.push({ taskId: task.id, round: roundNumber, stage: 'gate-runner', ok: false, feedback });
        return { ok: false, stage: 'gate-runner', feedback };
      }

      // The gate went green, so the previous gate signature is no longer the round's state.
      lastFailedSignature = '';

      const reviewPrompt = [
        `Audit the code changes of task (${task.id}) for Crux invariants (refutability, domain state safety, clean boundaries).`,
        `Task: ${task.ref}`,
        acceptanceBlock(task),
        workspace,
        gotchasBlock(),
        `Diff under review — read it with \`git -C ${taskPath} diff ${taskBase}...HEAD\` plus \`git -C ${taskPath} log --oneline ${taskBase}..HEAD\`.`,
        `Touched files: ${JSON.stringify(Array.from(touchedFiles))}`,
        `The deterministic gate passed. Focus exclusively on semantic correctness and invariant violations, and re-verify each issue from the previous round as fixed or not-fixed.`,
        `Enforce the scope taxonomy: do NOT flag beneficial design deepening (submodule decompositions curing code smells, internal helper extractions, architecture/terminology test suites) as scope creep.`,
        `Review stability: honor remedies accepted in prior rounds; do not reverse or contradict prior-round guidance unless a fatal correctness flaw (P1) is proven with a failing counterexample.`
      ]
        .filter(Boolean)
        .join('\n');

      const reviewResult = await accept(reviewPrompt, callOptions({ agentType: 'code-reviewer', label: `review:${slugify(task.id, 20)}:r${roundNumber}`, schema: reviewSchema }, true));
      recordSuggestions('code-reviewer', reviewResult && reviewResult.suggestions);
      const blockerIssues = (reviewResult && Array.isArray(reviewResult.issues) ? reviewResult.issues : []).filter(issue => issue.severity === 'P1' || issue.severity === 'P2');
      const reviewPassed = reviewResult && reviewResult.route === 'continue' && blockerIssues.length === 0;

      if (!reviewPassed) {
        const details = blockerIssues.map(issue => `[${issue.severity}] ${issue.file}:${issue.line || 0} — ${issue.defect}\nRemediation: ${issue.remediation}`).join('\n\n');
        const feedback = `Semantic code review reported Crux violations:\n${details || (reviewResult && reviewResult.summary) || 'Remediation needed'}`;
        ledger.push({ taskId: task.id, round: roundNumber, stage: 'code-reviewer', ok: false, feedback });
        return { ok: false, stage: 'code-reviewer', feedback };
      }

      const reviewScore = Number.isInteger(reviewResult.score) ? reviewResult.score : 0;

      if (!integrationWanted) {
        ledger.push({ taskId: task.id, round: roundNumber, stage: 'converged', ok: true, feedback: null, mergeAttempts: 0 });
        return { ok: true, devResult, gateResult, reviewResult, reviewScore, mergeAttempts: 0, merged: false };
      }

      if (nextMergeAttempt > maxMergeAttempts) {
        return {
          ok: false,
          stage: 'merger',
          blocked: true,
          feedback: `Merge attempt budget exhausted (${maxMergeAttempts}) for task ${task.id} while attempting to merge \`${taskBranch}\` into \`${integrationBranch}\`.`
        };
      }
      mergeAttempts = nextMergeAttempt;

      const mergePrompt = [
        `You are the Merge node of an AFK convergence run. You attempt exactly ONE merge: task copy → integration branch.`,
        gotchasBlock(),
        ``,
        `Task id: ${task.id}`,
        `Task branch: ${taskBranch}`,
        `Task worktree: ${taskPath}`,
        `Integration branch: ${integrationBranch}`,
        `Integration worktree: ${integrationPath}`,
        `Merge attempt: ${mergeAttempts} of ${maxMergeAttempts}`,
        `Session root — never touch: ${root}`,
        ``,
        `Procedure:`,
        `1. History hygiene in the copy: Conventional Commits, atomic, code and docs separate; when the repo tracks CHANGELOG.md exactly one new bullet under \`## [Unreleased]\`. Commit what the developer left uncommitted with the same conventions; never rewrite their commits.`,
        `2. Run exactly one merge: \`uv run ~/.agents/skills/branch-worktree-pr/scripts/merge_copy.py ${taskPath} ${integrationBranch}\` (or the same skill script resolved from this repository). Exit 0 = merged, exit 2 = conflict, exit 1 = gate failure. The project's \`[pre-merge]\` gate runs inside it when declared.`,
        `3. On exit 2: finish the rebase INSIDE ${taskPath} only, using the resolve-merge-conflicts skill. Headless continue form: \`GIT_EDITOR=true GIT_SEQUENCE_EDITOR=true git -C ${taskPath} rebase --continue\`. Commit the resolution on ${taskBranch}.`,
        `4. On exit 1: fix the failing gate inside ${taskPath} only (read the gate output first; a CHANGELOG guard hit is fixed inside the copy and committed). \`merge_copy.py\` pre-checks commit body line lengths before merging and names the offending commit and line — reword that message (message-only, keeping its content) and commit, then retry.`,
        `5. Do NOT retry the merge in this call, even after a successful repair: the repaired copy must be re-gated and re-reviewed before the next attempt, and only the workflow can sequence that. Report \`repaired\` true and let the run re-verify.`,
        `6. Record EVERY attempt you made as { exitCode, command, tail } with the tail capped at 20 lines, and set \`outcome\`: MERGED (exit 0 on the first attempt of this call), CONFLICT, GATE_FAILED.`,
        `7. Never report whether re-verification is needed — the workflow derives that from the exit codes. Never edit the integration worktree, never \`--force\`, never raw \`git merge\`, never \`wt remove --force\`, never touch \`origin\`, never push, never open a PR. If the copy is missing or the integration branch is unreachable → BLOCKED, keep everything, report the failing command and its output.`,
        ``,
        `Return the schema.`
      ].join('\n');

      const mergeResult = await accept(mergePrompt, callOptions({ agentType: 'merger', label: `merge:${slugify(task.id, 20)}:a${mergeAttempts}`, schema: mergeSchema }, true));
      recordSuggestions('merger', mergeResult && mergeResult.suggestions);
      const merges = mergeResult && Array.isArray(mergeResult.attempts) ? mergeResult.attempts : [];
      const nonZero = merges.filter(entry => Number(entry.exitCode) !== 0);
      const merged = Boolean(mergeResult) && mergeResult.merged === true && mergeResult.outcome === 'MERGED' && nonZero.length === 0;

      if (!mergeResult || mergeResult.status === 'BLOCKED' || merges.length === 0) {
        const evidence = merges.map(entry => `${entry.command} → exit ${entry.exitCode}\n${entry.tail || ''}`).join('\n\n');
        const feedback = `Merge node blocked on attempt ${mergeAttempts}:\n${evidence || (mergeResult && mergeResult.summary) || 'no evidence returned'}`;
        ledger.push({ taskId: task.id, round: roundNumber, stage: 'merger', ok: false, mergeAttempts, feedback });
        return { ok: false, stage: 'merger', blocked: true, feedback };
      }

      if (!merged) {
        const evidence = merges.map(entry => `${entry.command} → exit ${entry.exitCode}\n${entry.tail || ''}`).join('\n\n');
        const feedback = [
          `Merge attempt ${mergeAttempts} did not land the task on \`${integrationBranch}\` (outcome ${mergeResult.outcome}).`,
          evidence,
          `The repair happened inside \`${taskPath}\`. Re-verify this task there — re-run the deterministic gate and the review against the repaired copy — and then let the next round retry the merge.`
        ].join('\n\n');
        ledger.push({ taskId: task.id, round: roundNumber, stage: 'merger', ok: false, mergeAttempts, feedback });
        return { ok: false, stage: 'merger', feedback };
      }

      ledger.push({ taskId: task.id, round: roundNumber, stage: 'merged', ok: true, feedback: null, mergeAttempts });
      return { ok: true, devResult, gateResult, reviewResult, reviewScore, mergeAttempts, merged: true };
    },
    value => {
      if (!value || !value.ok) {
        return { ok: false, feedback: (value && value.feedback) || 'Round failed verification gate.' };
      }
      return { ok: true };
    },
    { attempts: maxRounds }
  );

  const last = outcome.value;
  const blocked = Boolean(last && last.blocked);
  const status = outcome.ok ? (integrationWanted ? 'MERGED' : 'CONVERGED') : blocked ? 'BLOCKED' : 'EXHAUSTED';
  const issues = outcome.ok ? [] : [last && last.feedback ? last.feedback : 'Exhausted the round budget without convergence.'];

  taskRows.push({
    id: task.id,
    ref: task.ref,
    kind: task.kind,
    status,
    rounds: outcome.attempts,
    mergeAttempts: last && Number.isInteger(last.mergeAttempts) ? last.mergeAttempts : mergeAttempts,
    branch: taskBranch,
    worktreePath: taskPath,
    reviewScore: last && Number.isInteger(last.reviewScore) ? last.reviewScore : 0,
    issues
  });

  report(`task ${task.id}: ${status} after ${outcome.attempts} round(s)${integrationWanted ? `, ${mergeAttempts} merge attempt(s)` : ''}`);

  if (!outcome.ok) {
    haltedBy = `task ${task.id} ended ${status}`;
    abortedTasks.push(task.id);
  }
}

// 6. Finalize — the composite verification the operator relies on before opening a PR
phase('Finalize');

let compositeGate = null;
let finalizeChangelogSync = null;
const mergedAny = taskRows.some(row => row.status === 'MERGED');

if (integrationWanted && mergedAny && !haltedBy) {
  const finalPrompt = [
    `Run the composite deterministic verification for the whole integration branch.`,
    `Integration branch: ${integrationBranch}`,
    `Integration worktree — run everything from here: ${integrationPath}`,
    `Base: ${base}`,
    stackHint ? `Stack: ${stackHint}` : '',
    gotchasBlock(),
    `Session root — never touch: ${root}`,
    `pi-dynamic-workflows does not forward a per-agent cwd, so prefix every command with \`cd ${integrationPath} && \` or address the tree with \`git -C ${integrationPath}\`.`,
    `This is the verification a human will rely on before opening a pull request, so run the FULL suite on the integrated tree, not a subset:`,
    `  - phase "integration-branch": \`git -C ${integrationPath} rev-parse --abbrev-ref HEAD\` prints \`${integrationBranch}\`;`,
    `  - phase "integration-clean": \`git -C ${integrationPath} status --porcelain --untracked-files=all | grep -vE '(__pycache__/|\\.pyc$|\\.DS_Store$|\\.lsz/)' || true\` prints nothing (machine-generated caches and \`.lsz/\` are tolerated);`,
    `  - phase "root-untouched": \`git -C ${root} status --porcelain --untracked-files=no\` is empty;`,
    `  - phase "changelog-check": when BOTH \`CHANGELOG.md\` and \`scripts/changelog-unreleased.py\` exist, run \`uv run python scripts/changelog-unreleased.py check\` from the integration worktree and report it as a normal phase. It is READ-ONLY: exit 0 = in sync, exit 1 = drift. Never run \`update\`, never stage, never commit — the workflow repairs drift itself. Omit this phase when either file is absent.`,
    `  - then typecheck, tests, lint, format check, build from the project's own manifests.`,
    `Report every phase as { name, command, ok, exitCode, tail } with tails capped at 20 lines. Never fix anything yourself, never merge, never push.`
  ]
    .filter(Boolean)
    .join('\n');

  compositeGate = await accept(finalPrompt, callOptions({ agentType: 'gate-runner', label: 'final-gate', schema: gateSchema }));
  recordSuggestions('composite-gate', compositeGate && compositeGate.suggestions);

  // A hand-drifted `## [Unreleased]` block used to mark a fully merged run BLOCKED. When the
  // read-only changelog check is the ONLY failing phase the delivery is otherwise green, so sync
  // the block in one idempotent hidden-type commit and re-run the composite gate exactly once.
  if (changelogDriftOnly(compositeGate)) {
    report('finalize: changelog drift is the only failing check — syncing and re-verifying once');
    const syncPrompt = [
      `You are the Finalize changelog-sync node of an AFK convergence run.`,
      `Every task has already merged; the composite gate failed on no check except \`changelog-check\`, because the generated \`## [Unreleased]\` block drifted from CHANGELOG.md.`,
      `Integration branch: ${integrationBranch}`,
      `Integration worktree — work ONLY here: ${integrationPath}`,
      `Session root — never touch: ${root}`,
      gotchasBlock(),
      ``,
      `Procedure:`,
      `1. Confirm the drift read-only first: \`cd ${integrationPath} && uv run python scripts/changelog-unreleased.py check\` (exit 1 means drift).`,
      `2. Sync it: \`uv run python scripts/changelog-unreleased.py update\`.`,
      `3. Commit ONLY CHANGELOG.md with the hidden-type subject exactly \`chore: sync changelog unreleased section\` — the hidden type is mandatory, because a visible-type sync commit re-enters the generated block and re-triggers the drift forever.`,
      `4. Idempotence: when \`git -C ${integrationPath} status --porcelain -- CHANGELOG.md\` is already clean, make no commit and report synced false.`,
      `5. Verify: re-run \`check\` (it must exit 0), and \`git -C ${integrationPath} status --porcelain\` must be empty apart from tolerated ephemeral cache entries.`,
      `6. Never push, never touch \`origin\`, never edit a file other than CHANGELOG.md, never re-run a merge, never touch a task copy.`,
      ``,
      `Return the schema.`
    ]
      .filter(Boolean)
      .join('\n');
    const syncResult = await accept(syncPrompt, callOptions({ agentType: 'merger', label: 'finalize-changelog-sync', schema: changelogSyncSchema }));
    recordSuggestions('finalize-changelog-sync', syncResult && syncResult.suggestions);
    finalizeChangelogSync = syncResult
      ? { status: syncResult.status, synced: syncResult.synced === true, summary: syncResult.summary || '' }
      : { status: 'BLOCKED', synced: false, summary: 'changelog-sync node returned no output' };
    if (syncResult && syncResult.status === 'COMPLETED' && syncResult.synced === true) {
      compositeGate = await accept(finalPrompt, callOptions({ agentType: 'gate-runner', label: 'final-recheck', schema: gateSchema }));
      recordSuggestions('composite-gate-recheck', compositeGate && compositeGate.suggestions);
    } else {
      report('finalize: changelog-sync made no commit — not re-running the composite gate');
    }
  }
}

const compositeOk = !integrationWanted || !mergedAny ? true : Boolean(compositeGate && compositeGate.ok === true);
const allTasksOk = taskRows.length > 0 && taskRows.every(row => row.status === 'MERGED' || row.status === 'CONVERGED');
const converged = allTasksOk && compositeOk;
const finalStatus = converged ? 'CONVERGED' : taskRows.some(row => row.status === 'BLOCKED') || !compositeOk ? 'BLOCKED' : 'EXHAUSTED';

const deliveryBranch = integrationWanted ? integrationBranch : (taskRows[0] && taskRows[0].branch) || '';
const deliveryPath = integrationWanted ? integrationPath : (taskRows[0] && taskRows[0].worktreePath) || '';

const nextActions = converged
  ? integrationWanted
    ? [
        `Review the integration branch \`${integrationBranch}\` at ${integrationPath} (it is verified and NOT pushed).`,
        `When you decide it is ready, ask the session to run merger Mode D to push the branch and open one pull request against ${base}.`
      ]
    : [
        `Review the task branch \`${deliveryBranch}\` at ${deliveryPath} (it is verified and NOT pushed).`,
        `When you decide it is ready, ask the session to run merger Mode D to push the branch and open a pull request against ${base}.`
      ]
  : [`Resolve the reported block, then re-run — nothing was pushed and no pull request exists.`];

report(
  `finished: ${finalStatus} — ${taskRows.filter(row => row.status === 'MERGED' || row.status === 'CONVERGED').length}/${taskRows.length} task(s) delivered on ${deliveryBranch || 'no branch'}; never pushed`
);

return {
  status: finalStatus,
  converged,
  maxRounds,
  maxMergeAttempts,
  taskTimeoutMs,
  runTimeoutMs,
  finalizeChangelogSync,
  preMergeHook,
  base,
  baseSource,
  tasks: taskRows,
  delivery: {
    mode: integrationWanted ? 'integration-branch' : 'task-branch',
    branch: deliveryBranch,
    base,
    worktreePath: deliveryPath,
    verified: converged,
    compositeGatePhases: compositeGate && Array.isArray(compositeGate.phases) ? compositeGate.phases : []
  },
  root,
  rootBranch: (prep && prep.rootBranch) || '',
  touchedFiles: Array.from(touchedFiles),
  deferredTasks: taskRows.filter(row => row.status === 'DEFERRED').map(row => row.id),
  abortedTasks,
  planIssues,
  ledger,
  nextActions,
  summary: converged
    ? `${taskRows.length} task(s) converged and verified on ${deliveryBranch} (${integrationWanted ? 'integration branch' : 'task branch'}), base ${base}. Nothing was pushed and no pull request was opened — merge/PR ownership stays with the operator.`
    : `Run ended ${finalStatus} after ${ledger.length} recorded stage(s); the branch ${deliveryBranch || '(none)'} is left in place at ${deliveryPath || '(none)'} with the failing evidence above. Nothing was pushed.`,
  suggestions
};
