#### TraceValue


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#tracevalue


A `TraceValue` represents the level of verbosity with which the server systematically reports its execution trace using [$/logTrace](#logTrace) notifications. The initial trace value is set by the client at initialization and can be modified later using the [$/setTrace](#setTrace) notification.


    export type TraceValue = 'off' | 'messages' | 'verbose';