#!/usr/bin/env -S pnpm dlx tsx
export function run(args: readonly string[]): void {
  console.log(`args: ${args.join(" ")}`);
}

run(process.argv.slice(2));
