#!/usr/bin/env node
/**
 * install-agents.mjs — align the ship-tasks role definitions with their canonical copies.
 *
 * Canonical: <skill-dir>/references/agents/*.md  (locked by <skill-dir>/references/agents.lock.json)
 * Target:    <repo>/.pi/agents/*.md   (project-scoped agent definitions, gitignored)
 *
 * Modes:
 *   (none)         install missing targets, verify present ones; drift fails loud
 *   --check        no writes; report what needs install/refresh (preflight)
 *   --refresh      overwrite drifted targets with the compiled canonical copy (explicit, logged)
 *   --update-lock  recompute agents.lock.json from canonical files and included templates
 *
 * Exit: 0 aligned | 2 action needed | 3 lock stale | 1 error
 * Never silently overwrites a drifted file — drift means someone edited the installed
 * role, and that edit has to be seen before it is discarded.
 */
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const skillDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const canonicalDir = join(skillDir, "references", "agents");
const lockPath = join(skillDir, "references", "agents.lock.json");

const modes = new Set(process.argv.slice(2));
const checkOnly = modes.has("--check");
const refresh = modes.has("--refresh");
const updateLock = modes.has("--update-lock");
if (checkOnly && refresh) fail("--check and --refresh are mutually exclusive");
if (updateLock && (checkOnly || refresh)) fail("--update-lock is a standalone mode");

function fail(message, code = 1) {
  console.error(`install-agents: ${message}`);
  process.exit(code);
}

function repoRoot() {
  try {
    return execFileSync("git", ["rev-parse", "--show-toplevel"], { encoding: "utf8" }).trim();
  } catch {
    return process.cwd();
  }
}

function sha256Buffer(buf) {
  return createHash("sha256").update(buf).digest("hex");
}

function sha256File(path) {
  return sha256Buffer(readFileSync(path));
}

function sha256String(str) {
  return sha256Buffer(Buffer.from(str, "utf8"));
}

function expandIncludes(filePath, collectedIncludes = new Set(), seen = new Set()) {
  const realPath = resolve(filePath);
  if (seen.has(realPath)) {
    fail(`circular @include detected: ${realPath}`);
  }
  seen.add(realPath);
  const dir = dirname(realPath);
  let content = readFileSync(realPath, "utf8");

  content = content.replace(/<!--\s*@include\s+([^\s]+)\s*-->/g, (_, relPath) => {
    const includePath = resolve(dir, relPath);
    if (!existsSync(includePath)) {
      fail(`included file not found: ${includePath} (referenced in ${realPath})`);
    }
    collectedIncludes.add(includePath);
    return expandIncludes(includePath, collectedIncludes, new Set(seen)).trim();
  });

  return content;
}

if (!existsSync(canonicalDir)) fail(`canonical agents directory missing: ${canonicalDir}`);

const canonical = readdirSync(canonicalDir)
  .filter((name) => name.endsWith(".md"))
  .sort();
if (canonical.length === 0) fail(`no canonical agent definitions in ${canonicalDir}`);

const canonicalHashes = Object.fromEntries(canonical.map((name) => [name, sha256File(join(canonicalDir, name))]));

// Pre-expand to discover all include dependencies and compiled contents
const allIncludes = new Set();
const compiledContents = {};
for (const name of canonical) {
  compiledContents[name] = expandIncludes(join(canonicalDir, name), allIncludes);
}

const compiledHashes = Object.fromEntries(
  canonical.map((name) => [name, sha256String(compiledContents[name])]),
);

const includeHashes = Object.fromEntries(
  Array.from(allIncludes)
    .sort()
    .map((absPath) => [relative(skillDir, absPath), sha256File(absPath)]),
);

if (updateLock) {
  const lockData = {
    version: 1,
    agents: canonicalHashes,
    includes: includeHashes,
    compiled: compiledHashes,
  };
  writeFileSync(lockPath, `${JSON.stringify(lockData, null, 2)}\n`);
  console.log(`install-agents: lock updated (${canonical.length} agents, ${Object.keys(includeHashes).length} includes) -> ${lockPath}`);
  process.exit(0);
}

if (!existsSync(lockPath)) fail(`lock file missing: ${lockPath} (run --update-lock)`);
const lock = JSON.parse(readFileSync(lockPath, "utf8"));
const locked = lock?.agents ?? {};
const lockedIncludes = lock?.includes ?? {};

const tamperedCanonical = canonical.filter((name) => locked[name] !== canonicalHashes[name]);
const tamperedIncludes = Object.keys(includeHashes).filter((relPath) => lockedIncludes[relPath] !== includeHashes[relPath]);

if ((tamperedCanonical.length > 0 || tamperedIncludes.length > 0) && !updateLock) {
  console.error("install-agents: canonical or included files do not match agents.lock.json:");
  for (const name of tamperedCanonical) console.error(`  - canonical role: ${name}`);
  for (const relPath of tamperedIncludes) console.error(`  - included template: ${relPath}`);
  process.exit(3);
}

const targetDir = join(repoRoot(), ".pi", "agents");
const plan = { installed: [], aligned: [], drifted: [], refreshed: [] };

for (const name of canonical) {
  const target = join(targetDir, name);
  const expected = compiledHashes[name];
  const compiledContent = compiledContents[name];

  if (!existsSync(target)) {
    plan.installed.push(name);
    if (!checkOnly) {
      mkdirSync(targetDir, { recursive: true });
      writeFileSync(target, compiledContent, "utf8");
    }
    continue;
  }
  if (sha256File(target) === expected) {
    plan.aligned.push(name);
    continue;
  }
  plan.drifted.push(name);
  if (refresh && !checkOnly) {
    writeFileSync(target, compiledContent, "utf8");
    plan.refreshed.push(name);
  }
}

const known = new Set(canonical);
const extra = existsSync(targetDir)
  ? readdirSync(targetDir)
      .filter((name) => name.endsWith(".md") && !known.has(name))
      .sort()
  : [];

const verb = checkOnly ? "would install" : "installed";
console.log(`install-agents: ${targetDir}`);
console.log(`  ${verb}: ${plan.installed.length ? plan.installed.join(", ") : "-"}`);
console.log(`  aligned: ${plan.aligned.length ? plan.aligned.join(", ") : "-"}`);
console.log(`  drifted: ${plan.drifted.length ? plan.drifted.join(", ") : "-"}`);
if (plan.refreshed.length) console.log(`  refreshed: ${plan.refreshed.join(", ")}`);
if (extra.length) console.log(`  extra (not managed here): ${extra.join(", ")}`);

if (plan.drifted.length > 0 && !refresh) {
  console.error(
    "install-agents: drifted role files were NOT overwritten. Review the diff, then re-run with --refresh to restore the canonical copy.",
  );
  process.exit(2);
}
if (checkOnly && (plan.installed.length > 0 || plan.drifted.length > 0)) process.exit(2);
console.log("install-agents: roles aligned.");
