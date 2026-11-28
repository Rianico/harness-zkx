```
balance-sizes [-h|--help] [--workspace <workspace>]
```

Balance sizes of all windows in the current workspace

**OPTIONS**

\-h, --help

Print help

\--workspace <workspace>

Act on the specified workspace instead of the focused workspace. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` environment variables.

```
close [-h|--help] [--quit-if-last-window] [--window-id <window-id>]
```

Close the focused window

Normally, you don’t need to use this command, because macOS offers its own `cmd+w` binding. You might want to use the command from CLI for scripting purposes

**OPTIONS**

\-h, --help

Print help

\--quit-if-last-window

Quit the app instead of closing if it’s the last window of the app

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

```
close-all-windows-but-current [-h|--help] [--quit-if-last-window]
```

On the focused workspace, close all windows but current

**OPTIONS**

\-h, --help

Print help

\--quit-if-last-window

Quit the apps instead of closing them if it’s their last window

```
config [-h|--help] --get <name> [--json] [--keys]
config [-h|--help] --major-keys
config [-h|--help] --all-keys
config [-h|--help] --config-path
```

Query AeroSpace config options

For now, only `mode.*` config options are supported

Under the hood, the config is represented as recursive data structure of maps, arrays, strings, and integers.

Printing without `--json` or `--keys` flag is supported only for scalar types (strings and integers) and array of scalar types. Printing other complicated objects requires `--json` or `--keys` flag.

**OPTIONS**

\-h, --help

Print help

\--get <name>

Get the value for a given key. You can inspect available keys with `--major-keys` or `--all-keys`

\--major-keys

Print major keys

\--all-keys

Print all available keys recursively

\--json

Print result in JSON format

\--keys

Print keys of the complicated object (map or array)

\--config-path

Print absolute path to the loaded config

**EXAMPLES**

- List all binding modes:
	```
	$ aerospace config --get mode --keys
	main
	service
	```
- List all key bindings for 'main' binding mode:
	```
	$ aerospace config --get mode.main.binding --keys
	alt-1
	alt-2
	...
	```
- List all key bindings for 'main' binding mode in JSON format:
	```
	$ aerospace config --get mode.main.binding --json
	{
	  "alt-w" : "workspace W",
	  "alt-y" : "workspace Y",
	  "alt-n" : "workspace N",
	  "alt-shift-e" : "move-node-to-workspace E",
	  "alt-shift-m" : "move-node-to-workspace M",
	  "alt-shift-t" : "move-node-to-workspace T",
	...
	```

```
debug-windows [-h|--help] [--window-id <window-id>]
```

Interactive command to record Accessibility API debug information to create bug reports

Use this command output to report bug reports about incorrect windows handling (e.g. some windows are floated when they shouldn’t).

The intended usage is the following:

1. Run the command to start the debug session recording
2. Focus problematic window or make the window appear.
3. Run the command one more time to stop the debug session recording and print the results

`debug-windows` command is **not stable API**. Please **don’t rely on** the command existence and output format. The only intended use case is to report bugs about incorrect windows handling.

**OPTIONS**

\-h, --help

Print help

\--window-id <window-id>

Print debug information of the specified window right away. Usage of this flag disables interactive mode.

```
echo [-h|--help] [--stderr] [--window-id <window-id>] -- <string>...
```

Print `<string>…` arguments and **interpolation variables** to stdout.

You can use this command in combination with other commands to do various things:

- You can test shell operators
- You can pipe an explicit input to some other command (e.g. [workspace](https://nikitabobko.github.io/AeroSpace/commands#workspace)) inside an [eval](https://nikitabobko.github.io/AeroSpace/commands#eval)
- You can print interpolation variables for the focused window (see [list-windows](https://nikitabobko.github.io/AeroSpace/commands#list-windows) for the list of interpolation variables)

**OPTIONS**

\-h, --help

Print help

\--stderr

Print to stderr instead of stdout

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

**ARGUMENTS**

<string>

The argument to print. Each `<string>` argument can contain **interpolation variables** similar to those in [list-windows command](https://nikitabobko.github.io/AeroSpace/commands#list-windows). You can specify multiple `<string>` arguments - each of them is printed on a separate line.

**EXAMPLES**

- Print the focused window title: `aerospace echo -- %{window-title}`

```
enable [-h|--help] toggle
enable [-h|--help] on [--fail-if-noop]
enable [-h|--help] off [--fail-if-noop]
```

Temporarily disable window management

When you disable AeroSpace, windows from currently invisible workspaces will be placed to the visible area of the screen

Key events are not intercepted when AeroSpace is disabled

**OPTIONS**

\-h, --help

Print help

\--fail-if-noop

Exit with non-zero exit code if already in the requested mode

```
eval [-h|--help] [--stdin] [--] <aerospace-shell-expr>
```

Send multiple commands to AeroSpace at once

**OPTIONS**

\-h, --help

Print help

\--stdin

Capture CLIs stdin and forward it to `<aerospace-shell-expr>`. If not supplied, stdin is ignored.

**ARGUMENTS**

<aerospace-shell-expr>

This argument is AeroSpace’s shell expression. See [https://nikitabobko.github.io/AeroSpace/guide#shell](https://nikitabobko.github.io/AeroSpace/guide#shell) for more info.

**EXAMPLES**

- Cycle between workspaces a, b, and c:  
	`aerospace eval 'echo a b c | workspace --wrap-around --stdin next'`

```
exec-and-forget <bash-script>
```

Run `/bin/bash -c '<bash-script>'`, and **don’t wait for the command termination**. **Stdout, stderr and exit code are ignored**.

For example, you can use this command to launch applications:

```toml
alt-enter = 'exec-and-forget open -n /System/Applications/Utilities/Terminal.app'
```

`<bash-script>` is passed as-is to bash without any transformations or escaping for convenience. `<bash-script>` is treated as suffix of the TOML string, it’s not even an argument in classic CLI sense

In the above example, `exec-and-forget` is percieved as String suffix and simply stripped. The remaining \` open -n /System/Applications/Utilities/Terminal.app\` is passed as-is to `/bin/bash -c '<bash-script>'`

- The command is available in config
- The command is available **neither** in CLI, **nor** in AeroSpace shell (see: [https://nikitabobko.github.io/AeroSpace/guide#shell](https://nikitabobko.github.io/AeroSpace/guide#shell))

```
false [-h|--help]
```

Return false value

The `false` utility returns with a non-zero exit code.

```
flatten-workspace-tree [-h|--help] [--workspace <workspace>]
```

Flatten the tree of the focused workspace

The command is useful when you messed up with your layout, and it’s easier to "reset" it and start again.

**OPTIONS**

\-h, --help

Print help

\--workspace <workspace>

Act on the specified workspace instead of the focused workspace. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` environment variables.

```
focus [-h|--help] [--ignore-floating] [--wrap-around]
      [--boundaries <boundary>] [--boundaries-action <action>]
      [--fail-if-fullscreen] [--fail-if-macos-native-fullscreen]
      (left|down|up|right)
focus [-h|--help] [--ignore-floating] [--wrap-around]
      [--boundaries <boundary>] [--boundaries-action <action>]
      (dfs-next|dfs-prev)
focus [-h|--help] --window-id <window-id>
focus [-h|--help] --dfs-index <dfs-index>
```

Set focus to a window.

Contrary to i3, `focus` command doesn’t have a separate argument to focus floating windows. From `focus` command perspective, floating windows are part of [the tree](https://nikitabobko.github.io/AeroSpace/guide#tree). The floating window parent container is determined as the smallest tiling container that contains the center of the floating window. The technique eliminates the need for an additional binding for floating windows. This behavior can be disabled with `--ignore-floating` flag.

`focus child|parent` isn’t supported because the necessity of this operation is under the question. [https://github.com/nikitabobko/AeroSpace/issues/5](https://github.com/nikitabobko/AeroSpace/issues/5)

**OPTIONS**

\-h, --help

Print help

\--boundaries <boundary>

Defines focus boundaries.  
`<boundary>` possible values: `(workspace|all-monitors-outer-frame)`.  
The default is: `workspace`

\--boundaries-action <action>

Defines the behavior when requested to cross the `<boundary>`.  
`<action>` possible values: `(stop|fail|wrap-around-the-workspace|wrap-around-all-monitors)`.  
The default is: `stop`

\--wrap-around

An alias for `--boundaries-action wrap-around-the-workspace`. The flag is incompatible with either `--boundaries-action` or `--boundaries`.

\--window-id <window-id>

Focus the window with specified `<window-id>`

\--dfs-index <dfs-index>

Focus window by its index, based on a depth-first search (DFS) of the window within the workspace tree. Index is 0-based.

\--ignore-floating

Don’t perceive floating windows as part of the tree. It may be useful for more reliable scripting.

\--fail-if-fullscreen

Exit with non-zero code if the current target window is fullscreen by the `fullscreen` command. Only compatible with `(left|down|up|right)`.

\--fail-if-macos-native-fullscreen

Exit with non-zero code if the current target window is in macOS native fullscreen. Only compatible with `(left|down|up|right)`.

**ARGUMENTS**

(left|down|up|right)

Set focus to the nearest window in the given direction.

(dfs-next|dfs-prev)

Set focus to the window before or after the current window in the depth-first order (top-to-bottom and left-to-right) of windows in the current workspace tree. In this mode, `--boundaries` must be `workspace` (the default) and `--boundaries-action` can be set to one of `(stop|fail|wrap-around-the-workspace)`.

```
focus-back-and-forth [-h|--help]
```

Switch between the current and previously focused elements back and forth. The element is either a window or an empty workspace.

AeroSpace stores only one previously focused window in history, which means that if you close the previous window, `focus-back-and-forth` has no window to switch focus to. In that case, the command will exit with non-zero exit code.

That’s why it may be preferred to combine `focus-back-and-forth` with `workspace-back-and-forth`:  

```
aerospace focus-back-and-forth || aerospace workspace-back-and-forth
```

Also see: [workspace-back-and-forth](https://nikitabobko.github.io/AeroSpace/commands#workspace-back-and-forth)

```
focus-monitor [-h|--help] [--wrap-around] (left|down|up|right)
focus-monitor [-h|--help] [--wrap-around] (next|prev)
focus-monitor [-h|--help] [--] <monitor-pattern>...
```

Focus monitor by relative direction, by order, or by pattern

**OPTIONS**

\-h, --help

Print help

\--wrap-around

Make it possible to wrap around focus

**ARGUMENTS**

(left|down|up|right)

Focus monitor in direction relative to the focused monitor

(next|prev)

Focus next|prev monitor in order they appear in tray icon

<monitor-pattern>…

Find the first matching monitor and focus it. Multiple monitor patterns is useful for different monitor configurations. Monitor patterns follow the same format as in `workspace-to-monitor-force-assignment` config option

```
fullscreen [-h|--help]     [--window-id <window-id>] [--no-outer-gaps]
fullscreen [-h|--help] on  [--window-id <window-id>] [--no-outer-gaps] [--fail-if-noop]
fullscreen [-h|--help] off [--window-id <window-id>] [--fail-if-noop]
```

Toggle the fullscreen mode for the focused window

Switching to a different tiling window within the same workspace while the current focused window is in fullscreen mode results in the fullscreen window exiting fullscreen mode.

**OPTIONS**

\-h, --help

Print help

\--no-outer-gaps

Remove the outer gaps when in fullscreen mode

\--fail-if-noop

Exit with non-zero exit code if already fullscreen or already not fullscreen

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

**ARGUMENTS**

on, off

`on` means enter fullscreen mode. `off` means exit fullscreen mode. Toggle between the two if not specified

```
join-with [-h|--help] [--window-id <window-id>] (left|down|up|right)
```

Put the focused window and the nearest node in the specified direction under a common parent container

**EXAMPLES**

Given this layout

```
h_tiles
├── window 1
├── window 2 (focused)
└── window 3
```

`join-with right` will result in the following layout

```
h_tiles
├── window 1
└── v_tiles
    ├── window 2 (focused)
    └── window 3
```

| Note | `join-with` is a high-level replacement for i3’s [split command](https://i3wm.org/docs/userguide.html#_splitting_containers). There is an observation that the only reason why you might want to split a node is to put several windows under a common "umbrella" parent. Unlike `split`, `join-with` can be used with [`enable-normalization-flatten-containers`](https://nikitabobko.github.io/AeroSpace/guide#normalization) |
| --- | --- |

**OPTIONS**

\-h, --help

Print help

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

```
layout [-h|--help] [--window-id <window-id>|--workspace <workspace>]
       [--root] [--fail-if-noop]
       (<target-layout>)...
```

Change layout of the focused node to the given layout

**OPTIONS**

\-h, --help

Print help

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

\--workspace <workspace>

Act on the specified workspace instead of the focused workspace. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` environment variables.

\--root

Instead of the focused window, change the layout of the workspace tiling root node. When you use this flag, `tiling` and `floating` become invalid values for `<target-layout>`.

\--fail-if-noop

Exit with non-zero exit code if already in the requested layout. When you use this flag, the command permits only one `<target-layout>` argument.

**ARGUMENTS**

<target-layout>

Possible values:

- `h_tiles|v_tiles|h_accordion|v_accordion` - Change both tiling layout and orientation in one go
- `tiles|accordion` - Change tiling layout but preserve orientation
- `horizontal|vertical` - Change orientation but preserve layout
- `tiling|floating` - Toggle between floating/tiling mode
	If several `<target-layout>` are supplied, then the first one that doesn’t describe the currently active layout is applied.

**EXAMPLES**

- Toggle between `floating` and `tiling` layouts (order of args doesn’t matter):  
	`aerospace layout floating tiling`
- Toggle orientation (order of args doesn’t matter):  
	`aerospace layout horizontal vertical`
- Toggle between `tiles` and `accordion` layouts (order of args doesn’t matter):  
	`aerospace layout tiles accordion`
- Switch to `tiles` layout. Toggle the layout orientation if already in `tiles` layout:  
	`aerospace layout tiles horizontal vertical`

```
list-apps [-h|--help] [--macos-native-hidden [no]] [--format <output-format>] [--count] [--json]
```

Print the list of running applications that appears in the Dock and may have a user interface

The command is useful to inspect list of applications to compose filter for [on-window-detected callback](https://nikitabobko.github.io/AeroSpace/guide#on-window-detected-callback)

**OPTIONS**

\-h, --help

Print help

\--macos-native-hidden \[no\]

Filter results to only print hidden applications. `[no]` inverts the condition

\--format <output-format>

Specify output format. See "Output Format" section for more details. Incompatible with `--count`

\--count

Output only the number of apps. Incompatible with: `--format`, `--json`

\--json

Output in JSON format. Can be used in combination with `--format` to specify which data to include into the json. Incompatible with `--count`

**OUTPUT FORMAT**

Output format can be configured with optional `[--format <output-format>]` option. `<output-format>` supports [string interpolation](https://en.wikipedia.org/wiki/String_interpolation).

If not specified, the default `<output-format>` is:  
`%{app-pid}%{right-padding} | %{app-bundle-id}%{right-padding} | %{app-name}`

The following variables can be used inside `<output-format>`:

%{app-bundle-id}

String. Application unique identifier. [Bundle ID](https://developer.apple.com/documentation/appstoreconnectapi/bundle_ids)

%{app-name}

String. Application name

%{app-pid}

Number. [UNIX process identifier](https://en.wikipedia.org/wiki/Process_identifier)

%{app-exec-path}

String. Application executable path

%{app-bundle-path}

String. Application bundle path

%{right-padding}

A special variable which expands with a minimum number of spaces required to form a right padding in the appropriate column

%{newline}

Unicode U+000A newline symbol `\n`

%{tab}

Unicode U+0009 tab symbol `\t`

```
list-exec-env-vars [-h|--help]
```

List environment variables that exec-\* commands and callbacks are run with

Examples of commands and callbacks:

- `aerospace exec-and-forget` command
- `exec-on-workspace-change-callback`

```
list-modes [-h|--help] [--current] [--count] [--json]
```

Print a list of modes currently specified in the configuration

See [the guide](https://nikitabobko.github.io/AeroSpace/guide#binding-modes) for documentation about binding modes

**OPTIONS**

\-h, --help

Print help

\--current

Only print the currently active mode. Incompatible with `--count`

\--count

Output only the number of modes. Incompatible with `--current`, `--json`

\--json

Output in JSON format. Incompatible with `--count`

```
list-monitors [-h|--help] [--focused [no]] [--mouse [no]] [--format <output-format>] [--count] [--json]
```

Print monitors that satisfy conditions

**OPTIONS**

\-h, --help

Print help

\--focused \[no\]

Filter results to only print the focused monitor. `[no]` inverts the condition

\--mouse \[no\]

Filter results to only print the monitor with the mouse. `[no]` inverts the condition

\--format <output-format>

Specify output format. See "Output Format" section for more details. Incompatible with `--count`

\--count

Output only the number of monitors. Incompatible with `--format`

\--json

Output in JSON format. Can be used in combination with `--format` to specify which data to include into the json. Incompatible with `--count`

**OUTPUT FORMAT**

Output format can be configured with optional `[--format <output-format>]` option. `<output-format>` supports [string interpolation](https://en.wikipedia.org/wiki/String_interpolation).

If not specified, the default `<output-format>` is:  
`%{monitor-id}%{right-padding} | %{monitor-name}`

The following variables can be used inside `<output-format>`:

%{monitor-id}

1-based Number. Sequential number of the belonging monitor

%{monitor-appkit-nsscreen-screens-id}

1-based index of the belonging monitor in `NSScreen.screens` array. Useful for integration with other tools that might be using `NSScreen.screens` ordering (like sketchybar).

%{monitor-name}

String. Name of the belonging monitor

%{monitor-is-main}

Boolean. True if the monitor is main.

%{right-padding}

A special variable which expands with a minimum number of spaces required to form a right padding in the appropriate column

%{newline}

Unicode U+000A newline symbol `\n`

%{tab}

Unicode U+0009 tab symbol `\t`

```
list-windows [-h|--help] (--workspace <workspace>...|--monitor <monitor>...)
             [--monitor <monitor>...] [--workspace <workspace>...]
             [--pid <pid>] [--app-bundle-id <app-bundle-id>] [--format <output-format>]
             [--count] [--json]
list-windows [-h|--help] --all [--format <output-format>] [--count] [--json]
list-windows [-h|--help] --focused [--format <output-format>] [--count] [--json]
```

Print windows that satisfy conditions

**OPTIONS**

\-h, --help

Print help

\--all

Alias for `--monitor all`. Please use this option **with caution**. Use it when you really need to get workspaces/windows from **all monitors**.

For multi-monitor setup `--monitor focused` is almost always a preferred option. If you’re automating something then you don’t want to mess up with workspaces/windows on a different monitor.

With great power comes great responsibility.

\--focused

Print the focused window. Please note that it is possible for no window to be in focus. In that case, error is reported.

\--workspace <workspace>…

Filter results to only print windows that belong to either of specified workspaces. `<workspace>…` is a space-separated list of workspace names.

Possible values:  

1. Workspace name
2. `focused` is a special workspace name that represents the focused workspace
3. `visible` is a special workspace name that represents all currently visible workspaces (In multi-monitor setup, there are multiple visible workspaces)

\--monitor <monitors>

Filter results to only print workspaces/windows that are attached to specified monitors. `<monitors>` is a space separated list of monitor IDs.  

Possible monitors IDs:  

1. 1-based index of a monitor as if monitors were ordered horizontally from left to right
2. `all` is a special monitor ID that represents all monitors
3. `mouse` is a special monitor ID that represents monitor with the mouse
4. `focused` is a special monitor ID that represents the focused monitor

\--pid <pid>

Filter results to only print windows that belong to the Application with specified `<pid>`

\--app-bundle-id <app-bundle-id>

Filter results to only print windows that belong to the Application with specified [Bundle ID](https://developer.apple.com/documentation/appstoreconnectapi/bundle_ids)

Deprecated (but still supported) flag name: `--app-id`

\--format <output-format>

Specify output format. See "Output Format" section for more details. Incompatible with `--count`

\--count

Output only the number of windows. Incompatible with `--format`

\--json

Output in JSON format. Can be used in combination with `--format` to specify which data to include into the json. Incompatible with `--count`

**OUTPUT FORMAT**

Output format can be configured with optional `[--format <output-format>]` option. `<output-format>` supports [string interpolation](https://en.wikipedia.org/wiki/String_interpolation).

If not specified, the default `<output-format>` is:  
`%{window-id}%{right-padding} | %{app-name}%{right-padding} | %{window-title}`

The following variables can be used inside `<output-format>`:

%{window-id}

Number. Window unique ID

%{window-title}

String. Window title

%{window-is-fullscreen}

Boolean. Is window in fullscreen by `aerospace fullscreen` command

%{window-layout}

String. An alias for `%{window-parent-container-layout}`

%{window-parent-container-layout}

String. The layout (`v_tiles`, `h_tiles`, `v_accordion`, `h_accordion`, `floating`) of the window’s parent container.

%{app-bundle-id}

String. Application unique identifier. [Bundle ID](https://developer.apple.com/documentation/appstoreconnectapi/bundle_ids)

%{app-name}

String. Application name

%{app-pid}

Number. [UNIX process identifier](https://en.wikipedia.org/wiki/Process_identifier)

%{app-exec-path}

String. Application executable path

%{app-bundle-path}

String. Application bundle path

%{workspace}

String. Name of the belonging workspace

%{workspace-is-focused}

Boolean. `true` if the workspace has focus

%{workspace-is-visible}

Boolean. `true` if the workspace is visible. A workspace can be visible but not focused in a multi-monitor setup

%{workspace-root-container-layout}

String. The layout (`v_tiles`, `h_tiles`, `v_accordion`, `h_accordion`) of the workspace the window belongs to.

%{monitor-id}

1-based Number. Sequential number of the belonging monitor.

%{monitor-appkit-nsscreen-screens-id}

1-based index of the belonging monitor in `NSScreen.screens` array. Useful for integration with other tools that might be using `NSScreen.screens` ordering (like sketchybar).

%{monitor-name}

String. Name of the belonging monitor

%{monitor-is-main}

Boolean. `true` if the monitor is main.

%{right-padding}

A special variable which expands with a minimum number of spaces required to form a right padding in the appropriate column

%{newline}

Unicode U+000A newline symbol `\n`

%{tab}

Unicode U+0009 tab symbol `\t`

```
list-workspaces [-h|--help] --monitor <monitor>... [--visible [no]] [--empty [no]] [--format <output-format>] [--count] [--json]
list-workspaces [-h|--help] --all [--format <output-format>] [--count] [--json]
list-workspaces [-h|--help] --focused [--format <output-format>] [--count] [--json]
```

Print workspaces that satisfy conditions

**OPTIONS**

\-h, --help

Print help

\--format <output-format>

Specify output format. See "Output Format" section for more details

\--all

Alias for `--monitor all`. Please use this option **with caution**. Use it when you really need to get workspaces/windows from **all monitors**.

For multi-monitor setup `--monitor focused` is almost always a preferred option. If you’re automating something then you don’t want to mess up with workspaces/windows on a different monitor.

With great power comes great responsibility.

\--focused

An alias for `--monitor focused --visible`. Always prints a single workspace

\--monitor <monitors>

Filter results to only print workspaces/windows that are attached to specified monitors. `<monitors>` is a space separated list of monitor IDs.  

Possible monitors IDs:  

1. 1-based index of a monitor as if monitors were ordered horizontally from left to right
2. `all` is a special monitor ID that represents all monitors
3. `mouse` is a special monitor ID that represents monitor with the mouse
4. `focused` is a special monitor ID that represents the focused monitor

\--visible \[no\]

Filter results to only print currently visible workspaces. `[no]` inverts the condition. Several workspaces can be visible in multi-monitor setup

\--empty \[no\]

Filter results to only print empty workspaces. `[no]` inverts the condition.

\--format <output-format>

Specify output format. See "Output Format" section for more details. Incompatible with `--count`

\--count

Output only the number of workspaces. Incompatible with `--format`

\--json

Output in JSON format. Can be used in combination with `--format` to specify which data to include into the json. Incompatible with `--count`

**OUTPUT FORMAT**

Output format can be configured with optional `[--format <output-format>]` option. `<output-format>` supports [string interpolation](https://en.wikipedia.org/wiki/String_interpolation).

If not specified, the default `<output-format>` is:  
`%{workspace}`

The following variables can be used inside `<output-format>`:

%{workspace}

String. Name of the belonging workspace

%{workspace-is-focused}

Boolean. `true` if the workspace has focus

%{workspace-is-visible}

Boolean. `true` if the workspace is visible. A workspace can be visible but not focused in a multi-monitor setup

%{workspace-root-container-layout}

String. The layout (`v_tiles`, `h_tiles`, `v_accordion`, `h_accordion`) of the workspace’s root container

%{monitor-id}

1-based Number. Sequential number of the belonging monitor

%{monitor-appkit-nsscreen-screens-id}

1-based Number. Sequential number of the belonging monitor in `NSScreen.screens`. Useful for integration with other tools that might be using `NSScreen.screens` ordering (like sketchybar).

%{monitor-name}

String. Name of the belonging monitor

%{monitor-is-main}

Boolean. `true` if the monitor is main.

%{right-padding}

A special variable which expands with a minimum number of spaces required to form a right padding in the appropriate column

%{newline}

Unicode U+000A newline symbol `\n`

%{tab}

Unicode U+0009 tab symbol `\t`

```
macos-native-fullscreen [-h|--help] [--window-id <window-id>]
macos-native-fullscreen [-h|--help] [--window-id <window-id>] [--fail-if-noop] on
macos-native-fullscreen [-h|--help] [--window-id <window-id>] [--fail-if-noop] off
```

Toggle macOS fullscreen for the focused window

**OPTIONS**

\-h, --help

Print help

\--fail-if-noop

Exit with non-zero exit code if already fullscreen or already not fullscreen

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

**ARGUMENTS**

on, off

`on` means enter fullscreen mode. `off` means exit fullscreen mode. Toggle between the two if not specified

```
macos-native-minimize [-h|--help] [--window-id <window-id>]
```

Minimize focused window

**OPTIONS**

\-h, --help

Print help

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

```
mode [-h|--help] [--] <binding-mode>
```

Activate the specified binding mode

See [the guide](https://nikitabobko.github.io/AeroSpace/guide#binding-modes) for documentation about binding modes

```
move [-h|--help] [--window-id <window-id>] [--boundaries <boundary>]
     [--boundaries-action <boundary-action>] [--fail-if-fullscreen]
     [--fail-if-macos-native-fullscreen] (left|down|up|right)
```

Move the focused window in the given direction. See the "Examples" section for more details.

Deprecated name: `move-through`

**OPTIONS**

\-h, --help

Print help

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

\--boundaries <boundary>

Defines move boundaries.  
`<boundary>` possible values: `(workspace|all-monitors-outer-frame)`.  
The default is: `workspace`

\--boundaries-action <boundary-action>

Defines the behavior when requested to move across the `<boundary>`.  
`<boundary-action>` possible values: `(stop|fail|create-implicit-container)`.  
The default is: `create-implicit-container`

\--fail-if-fullscreen

Exit with non-zero code if the target window is fullscreen by the `fullscreen` command.

\--fail-if-macos-native-fullscreen

Exit with non-zero code if the target window is in macOS native fullscreen.

**EXAMPLES**

1. Given this layout
	```
	h_tiles
	├── window 1 (focused)
	└── window 2
	```
	`move right` will result in the following layout
	```
	h_tiles
	├── window 2
	└── window 1 (focused)
	```
2. Given this layout
	```
	h_tiles
	├── window 1
	├── window 2 (focused)
	└── v_tiles
	    ├── window 3
	    └── window 4
	```
	`move right` will result in the following layout
	```
	h_tiles
	├── window 1
	└── v_tiles
	    ├── window 3
	    ├── window 2 (focused)
	    └── window 4
	```
3. Given this layout
	```
	h_tiles
	├── window 1
	└── v_tiles
	    ├── window 3
	    ├── window 2 (focused)
	    └── window 4
	```
	`move left` will result in the following layout
	```
	h_tiles
	├── window 1
	├── window 2 (focused)
	└── v_tiles
	    ├── window 3
	    └── window 4
	```
4. **Implicit container example**
	In some cases, `move` needs to implicitly create a container to fulfill your command.
	Given this layout
	```
	h_tiles
	├── window 1
	├── window 2 (focused)
	└── window 3
	```
	`move up` will result in the following layout
	```
	v_tiles
	├── window 2 (focused)
	└── h_tiles
	    ├── window 1
	    └── window 3
	```
	`v_tiles` is an implicitly created container.
	**Remark**: If `--boundaries` is set to `all-monitors-outer-frame` and there is a monitor in the `up` direction, the implicit container isn’t created.
	Instead, `window 2` would be moved to the monitor above the current.

```
move-mouse [-h|--help] [--fail-if-noop] <mouse-position>
```

Move mouse to the requested position

**OPTIONS**

\-h, --help

Print help

\--fail-if-noop

Exit with non-zero exit code if mouse is already at the requested position. The flag is compatible only with `window-lazy-center` and `monitor-lazy-center` arguments.

**ARGUMENTS**

<mouse-position>

Position to move mouse to. Possible values:

- `monitor-lazy-center`. Move mouse to the center of the focused monitor, **unless** it is already within the monitor boundaries.
- `monitor-force-center`. Move mouse to the center of the focused monitor.
- `window-lazy-center`. Move mouse to the center of the focused window, **unless** it is already within the window boundaries. Exit with non-zero code if no window is focused.
- `window-force-center`. Move mouse to the center of the focused window. Exit with non-zero code if no window is focused.

**EXAMPLES**

- Try to move mouse to the center of the window. If there is no window in focus, move mouse to the center of the monitor:  
	`aerospace move-mouse window-lazy-center || aerospace move-mouse monitor-lazy-center`

```
move-node-to-monitor [-h|--help] [--window-id <window-id>] [--focus-follows-window]
                     [--wrap-around] (left|down|up|right|next|prev)
move-node-to-monitor [-h|--help] [--window-id <window-id>] [--focus-follows-window]
                     [--fail-if-noop] [--] <monitor-pattern>...
```

Move window to monitor targeted by relative direction, by order, or by pattern

**OPTIONS**

\-h, --help

Print help

\--wrap-around

Make it possible to wrap around the movement

\--focus-follows-window

Make sure that the window in question receives focus after moving. This flag is a shortcut for manually running `aerospace-workspace` / `aerospace-focus` after `move-node-to-monitor` successful execution.

\--fail-if-noop

Exit with non-zero code if moving window to monitor it already belongs to

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

**ARGUMENTS**

(left|down|up|right)

Move window to monitor in direction relative to the focused monitor

(next|prev)

Move window to next|prev monitor in order they appear in tray icon

<monitor-pattern>…

Find the first matching monitor and move the window there. Multiple monitor patterns is useful for different monitor configurations. Monitor patterns follow the same format as in `workspace-to-monitor-force-assignment` config option

```
move-node-to-workspace [-h|--help] [--focus-follows-window] [--wrap-around]
                       [--stdin|--no-stdin]
                       (next|prev)
move-node-to-workspace [-h|--help] [--focus-follows-window] [--fail-if-noop]
                       [--window-id <window-id>] [--] <workspace-name>
```

Move the focused window to the specified workspace

`(next|prev)` is identical to `workspace (next|prev)`

**OPTIONS**

\-h, --help

Print help

\--wrap-around

Make it possible to jump between first and last workspaces using (next|prev)

\--fail-if-noop

Exit with non-zero code if move window to workspace it already belongs to

\--focus-follows-window

Make sure that the window in question receives focus after moving. This flag is a shortcut for manually running `aerospace-workspace` / `aerospace-focus` after `move-node-to-workspace` successful execution.

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

\--stdin

Read the list of workspaces from stdin. Incompatible with `--no-stdin`

\--no-stdin

Ignore the list of workspaces from stdin, even if provided. Incompatible with `--stdin`

**ARGUMENTS**

(next|prev)

Move window to next or prev workspace

<workspace-name>

Specifies workspace name where to move window to

```
move-workspace-to-monitor [-h|--help] [--workspace <workspace>] [--wrap-around] (left|down|up|right)
move-workspace-to-monitor [-h|--help] [--workspace <workspace>] [--wrap-around] (next|prev)
move-workspace-to-monitor [-h|--help] [--workspace <workspace>] [--] <monitor-pattern>...
```

Move workspace to monitor targeted by relative direction, by order, or by pattern. Focus follows the focused workspace, so the workspace stays focused.

The command fails for workspaces [that have monitor force assignment](https://nikitabobko.github.io/AeroSpace/guide#assign-workspaces-to-monitors).

**OPTIONS**

\-h, --help

Print help

\--wrap-around

Allows to move workspace between first and last monitors

\--workspace <workspace>

Act on the specified workspace instead of the focused workspace. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` environment variables.

**ARGUMENTS**

(left|down|up|right)

Move workspace to monitor in direction relative to the focused monitor

(next|prev)

Move the workspace to next or prev monitor. 'next' or 'prev' monitor is calculated relative to the monitor `<workspace>` currently belongs to.

<monitor-pattern>

Find the first matching monitor and move the workspace there. Multiple monitor patterns is useful for different monitor configurations. Monitor patterns follow the same format as in `workspace-to-monitor-force-assignment` config option

```
reload-config [-h|--help] [--no-gui] [--dry-run] [--warnings-as-errors]
```

Reload currently active config

If the config contains errors they will be printed to stdout, and GUI will open to show the errors.

By default, warnings are written to stderr and do not open the diagnostics window. With `--warnings-as-errors`, warnings are treated like errors: written to stdout, shown in the diagnostics window, and the exit code is non-zero.

**OPTIONS**

\-h, --help

Print help.

\--no-gui

Don’t open GUI to show error. Only use stdout to report errors.

\--dry-run

Validate the config and show errors (if any) but don’t reload the config.

\--warnings-as-errors

Treat warnings as errors: print them to stdout, open the GUI diagnostics window, and return a non-zero exit code.

**EXIT CODES**

0

Success. The config contains no errors.

non-zero exit code

Failure. The config contains errors.

```
resize [-h|--help] [--window-id <window-id>] (smart|smart-opposite|width|height) [+|-]<number>
```

Resize the focused window

The dimension to resize is chosen by the first argument

- `width` changes width
- `height` changes height
- `smart` changes width if the parent has horizontal orientation, and it changes height if the parent has vertical orientation
- `smart-opposite` resizes the opposite axis of smart

Second argument controls how much the size changes

- If the `<number>` is prefixed with `+` then the dimension is increased
- If the `<number>` is prefixed with `-` then the dimension is decreased
- If the `<number>` is prefixed with neither `+` nor `-` then the command changes the absolute value of the dimension

**OPTIONS**

\-h, --help

Print help

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

```
run-callback [-h|--help] [--for-every-window|--window-id <window-id>] on-window-detected
run-callback [-h|--help] (on-focus-changed|on-focused-monitor-changed)
```

Run AeroSpace config callbacks on demand

The command lets you manually re-run callbacks that AeroSpace normally invokes in response to events:

- `on-window-detected` - callbacks defined by `on-window-detected` config option. By default the callbacks are run for the focused window only. Pass `--for-every-window` to apply the callbacks to every currently known window (useful right after `reload-config` to retroactively apply new rules to already open windows), or pass `--window-id` to target a specific window.
- `on-focus-changed` - runs commands listed under the `on-focus-changed` config key.
- `on-focused-monitor-changed` - runs commands listed under the `on-focused-monitor-changed` config key.

The command forwards stdout and stderr of all commands run in the callback. That opens up one more usecase - you can use this command to see the output of your callbacks.

**OPTIONS**

\-h, --help

Print help

\--for-every-window

Run `on-window-detected` callbacks for every window. Only valid with `on-window-detected`. Mutually exclusive with `--window-id`.

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

Only valid with `on-window-detected`. Mutually exclusive with `--for-every-window`.

**ARGUMENTS**

<callback>

One of: `on-window-detected`, `on-focus-changed`, `on-focused-monitor-changed`

**EXIT CODES**

The command forwards the exit code of the callback.

```
split [-h|--help] [--window-id <window-id>] (horizontal|vertical|opposite)
```

`split` command exists solely for compatibility with i3. Unless you’re hardcore i3 user who knows what they are doing, it’s recommended to use `join-with`

**If the parent of focused window contains more than one child**, then the command

1. Creates a new tiling container
2. Replaces the focused window with the container
3. Puts the focused window into the container as its only child

The argument configures orientation of the newly created container. `opposite` means opposite orientation compared to the parent container.

**If the parent of the focused window contains only a single child** (the window itself), then `split` command changes the orientation of the parent container

| Important | `split` command has no effect if `enable-normalization-flatten-containers` is turned on. Consider using `join-with` if you want to keep `enable-normalization-flatten-containers` enabled |
| --- | --- |

**OPTIONS**

\-h, --help

Print help

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

```
subscribe [-h|--help] [--all] [--no-send-initial] [<event>...]
```

This command connects to the AeroSpace server and receives real-time event notifications as JSON lines. The connection remains open until terminated (e.g., via Ctrl+C).

On connect, the current state is sent immediately (focus-changed with current window/workspace, mode-changed with current mode, etc.).

**OPTIONS**

**ARGUMENTS**

The following events can be subscribed to:

focus-changed

Fired when window focus changes. Includes `windowId`, `workspace`.

focused-monitor-changed

Fired when the focused monitor changes. Includes `workspace`, `monitorId`.

focused-workspace-changed

Fired when the focused workspace changes. Includes `workspace`, `prevWorkspace`.

mode-changed

Fired when the binding mode changes. Includes `mode`.

window-detected

Fired when a new window is detected. Includes `windowId`, `workspace`, `appBundleId`, `appName`.

binding-triggered

Fired when a keyboard binding is triggered. Includes `binding`, `mode`.

**OUTPUT FORMAT**

Events are output as JSON lines (one JSON object per line):

```
{"_event":"focused-monitor-changed","monitorId":1,"workspace":"M"}
{"_event":"focused-workspace-changed","prevWorkspace":"M","workspace":"M"}
{"_event":"mode-changed","mode":"main"}
{"_event":"focus-changed","windowId":28218,"workspace":"M"}
```

```
swap [-h|--help] [--window-id <window-id>] [--swap-focus]
     [--wrap-around] (left|down|up|right|dfs-next|dfs-prev)
```

Swaps the focused window with another window.

The operation is equivalent to dragging a window with the mouse.

**OPTIONS**

\-h, --help

Print help

\--window-id <window-id>

Act on the specified window instead of the focused window. The flag takes precedence over `AEROSPACE_WINDOW_ID` and `AEROSPACE_WORKSPACE` [environment variables](https://nikitabobko.github.io/AeroSpace/guide#environment-variables).

\--swap-focus

Swap focus away from the currently focused window. By default, this command does not change the focused window.

\--wrap-around

Wrap around if the window is at the edge of the workspace (for `(left|down|up|right)`) or the start/end of the depth first order (for `(dfs-next|dfs-prev)`).

**ARGUMENTS**

(left|down|up|right)

Swaps the focused window with the nearest window in the given direction.

(dfs-next|dfs-prev)

Swaps the focused window with the next or previous window in the depth-first order (top-to-bottom and left-to-right) of windows in the current workspace tree.

```
test [-h|--help] <lhs> = <rhs>
test [-h|--help] <lhs> ~= <rhs>
```

Condition evaluation utility

The `test` utility evaluates the expression and, if it evaluates to true, returns a zero (true) exit status; otherwise it returns 1 (false).

The utility is inspired by the builtin `/bin/test` utility.

`<lhs> = <rhs>`

Tests that `<lhs>` equals to `<rhs>`

`<lhs> ~= <rhs>`

Tests that `<lhs>` contains case insensitive `<rhs>` regex. The command fails if `<lhs>` is not a string

**EXAMPLES**

Test if the application ID equals to Chrome: `aerospace test %{app-bundle-id} = com.google.Chrome`

Test if the application name contains "chrome" (case insensitive): `aerospace test %{app-name} ~= chrome`

**ARGUMENTS**

<lhs>

The left hand side of the expression. The left hand side must be one of the interpolation variables (see below).

<rhs>

An integer, a boolean (`true` / `false`), a regex, or just a plain string. The way the expression is interpreted depends on the type of `<lhs>` and the infix operator.

**INTERPOLATION VARIABLES**

%{window-id}

Number. Window unique ID

%{window-title}

String. Window title

%{window-is-fullscreen}

Boolean. Is window in fullscreen by `aerospace fullscreen` command

%{window-layout}

String. An alias for `%{window-parent-container-layout}`

%{window-parent-container-layout}

String. The layout (`v_tiles`, `h_tiles`, `v_accordion`, `h_accordion`, `floating`) of the window’s parent container.

%{app-bundle-id}

String. Application unique identifier. [Bundle ID](https://developer.apple.com/documentation/appstoreconnectapi/bundle_ids)

%{app-name}

String. Application name

%{app-pid}

Number. [UNIX process identifier](https://en.wikipedia.org/wiki/Process_identifier)

%{app-exec-path}

String. Application executable path

%{app-bundle-path}

String. Application bundle path

%{workspace}

String. Name of the belonging workspace

%{workspace-is-focused}

Boolean. `true` if the workspace has focus

%{workspace-is-visible}

Boolean. `true` if the workspace is visible. A workspace can be visible but not focused in a multi-monitor setup

%{workspace-root-container-layout}

String. The layout (`v_tiles`, `h_tiles`, `v_accordion`, `h_accordion`) of the workspace the window belongs to.

%{monitor-id}

1-based Number. Sequential number of the belonging monitor.

%{monitor-appkit-nsscreen-screens-id}

1-based index of the belonging monitor in `NSScreen.screens` array. Useful for integration with other tools that might be using `NSScreen.screens` ordering (like sketchybar).

%{monitor-name}

String. Name of the belonging monitor

%{monitor-is-main}

Boolean. `true` if the monitor is main.

**EXIT CODES**

0

The expression has evaluated to `true`.

1

The expression has evaluated to `false`.

\>1

An error occurred. For instance, when `<rhs>` type doesn’t match `<lhs>` type, or if the `test` subcommand couldn’t be parsed.

```
test-not [-h|--help] <lhs> = <rhs>
test-not [-h|--help] <lhs> ~= <rhs>
```

Negative condition evaluation utility

The subcommand works exactly the same as the `test` subcommand, except the result (exit code) is negated. Please refer to the `test` subcomman documentation for more information.

```
summon-workspace [-h|--help] [--fail-if-noop] [--] <workspace>
```

Move the requested workspace to the focused monitor. The moved workspace becomes focused. The behavior is identical to Xmonad.

The command makes sense only in multi-monitor setup. In single monitor setup the command is identical to `workspace` command.

**OPTIONS**

\-h, --help

Print help

\--fail-if-noop

Exit with non-zero exit code if the workspace is already visible on the focused monitor.

**ARGUMENTS**

<workspace>

The workspace to operate on.

```
trigger-binding [-h|--help] --mode <mode-id> [--] <binding>
```

Trigger AeroSpace binding as if it was pressed by user

You can use aerospace-config command to inspect available bindings:  
`aerospace config --get mode.main.binding --keys`

**OPTIONS**

\-h, --help

Print help

\--mode <mode-id>

Mode to search `<binding>` in

**ARGUMENTS**

<binding>

Binding to trigger

**EXAMPLES**

- Run alphabetically first binding from config (useless and synthetic example):  
	`aerospace trigger-binding --mode main "$(aerospace config --get mode.main.binding --keys | head -1)"`
- Trigger `alt-tab` binding:  
	`aerospace trigger-binding --mode main alt-tab`

```
true [-h|--help]
```

Return true value

The `true` utility returns with an exit code of zero.

The utility might return with a non-zero exit in case of errors (e.g. unexpected CLI arguments)

**OPTIONS**

\-h, --help

Print help

**EXIT CODES**

0

No errors have occurred.

\>0

An error occurred. For instance, unexpected CLI arguments.

```
volume [-h|--help] (up|down) [--no-gui]
volume [-h|--help] (mute-toggle|mute-off|mute-on) [--no-gui]
volume [-h|--help] set <number> [--no-gui]
```

Manipulate volume

**OPTIONS**

\-h, --help

Print help

\--no-gui

Don’t show volume GUI indicator

**ARGUMENTS**

(up|down)

Increase or decrease the volume

(mute-toggle|mute-on|mute-off)

Toggle/On/Off mute

set <number>

Set volume to the exact value on scale from 0 to 100

```
workspace [-h|--help] [--auto-back-and-forth] [--fail-if-noop] [--] <workspace-name>
workspace [-h|--help] [--wrap-around] [--stdin|--no-stdin] (next|prev)
```

**1\. <workspace-name> syntax**

Focus the specified workspace

**2\. (next|prev) syntax**

Focuses next or previous workspace in **the list**.

- If `--stdin` is specified, then **the list** is taken from stdin
- Otherwise, **the list** is defined as all workspaces (even empty ones) on focused monitor in alphabetical order

**OPTIONS**

\-h, --help

Print help

\--wrap-around

Make it possible to jump between first and last workspaces using `(next|prev)`

\--auto-back-and-forth

Automatic `back-and-forth` when switching to already focused workspace. Incompatible with `--fail-if-noop`

\--fail-if-noop

Exit with non-zero exit code if switch to the already focused workspace. Incompatible with `--auto-back-and-forth`

\--stdin

Read the list of workspaces from stdin. Incompatible with `--no-stdin`

\--no-stdin

Ignore the list of workspaces from stdin, even if provided. Incompatible with `--stdin`

**ARGUMENTS**

<workspace-name>

Workspace name to focus.

**EXAMPLES**

- Go to the next non empty workspace on the focused monitor:  
	`aerospace list-workspaces --monitor focused --empty no | aerospace workspace --stdin next`

```
workspace-back-and-forth [-h|--help]
```

Switch between the focused workspace and previously focused workspace back and forth

Unlike `focus-back-and-forth`, `workspace-back-and-forth` always succeeds. Because unlike windows, workspaces can not be "closed". Workspaces are name-addressable objects. They are created and destroyed on the fly.

Also see: [focus-back-and-forth](https://nikitabobko.github.io/AeroSpace/commands#focus-back-and-forth)
