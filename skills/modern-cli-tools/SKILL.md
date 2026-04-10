---
name: modern-cli-tools
description: Reference manual for modern CLI tools (fd, rg, eza). Use when you encounter errors or need advanced syntax for replacing find, grep, or ls.
---

# Modern CLI Tools Reference

**Status**: Skill Reference Guide

You have been instructed to use modern, Rust-based CLI tools (`fd`, `rg`, `eza`) instead of legacy tools (`find`, `grep`, `ls`). If you are running into errors or need to perform complex queries, use the examples below.

## 1. File Discovery: `fd` (Replaces `find`)

`fd` respects `.gitignore` and ignores hidden files/directories by default. It uses regex for pattern matching.

**Common Scenarios:**
- **Find by name**: `fd "pattern"` (searches for "pattern" anywhere in the path)
- **Find by exact extension**: `fd -e md` (finds all .md files)
- **Search hidden files (like `.github`)**: `fd -H "pattern"`
- **Search ignored files (override `.gitignore`)**: `fd -I "pattern"`
- **Search BOTH hidden and ignored (closest to `find` default)**: `fd -HI "pattern"`
- **Execute command on results**: `fd -e txt -x rm {}` (deletes all .txt files)
- **Exclude a directory**: `fd "pattern" -E "node_modules"`

## 2. Text Search: `ripgrep` / `rg` (Replaces `grep`)

`rg` respects `.gitignore` and skips hidden files by default.

**Common Scenarios:**
- **Basic search**: `rg "search term"`
- **Search specific file types**: `rg -t js "console.log"` (searches only JS files)
- **Search hidden files/directories**: `rg --hidden "search term"`
- **Search ignored files (override `.gitignore`)**: `rg -u "search term"`
- **Search EVERYTHING (hidden + ignored)**: `rg -uu "search term"`
- **Show only filenames with matches**: `rg -l "search term"`
- **Show context lines**: `rg -C 2 "search term"` (2 lines before and after)

## 3. Listing Directories: `eza` (Replaces `ls`)

`eza` is a modern replacement for `ls`.

**Common Scenarios:**
- **Standard detailed list**: `eza -la`
- **List directory tree**: `eza --tree`
- **List tree with limits**: `eza --tree --level=2`
- **Sort by modification time**: `eza -la --sort=modified`
