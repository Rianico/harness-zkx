### Server lifecycle


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#server-lifecycle


The current protocol specification defines that the lifecycle of a server is managed by the client (e.g. a tool like VS Code or Emacs). It is up to the client to decide when to start (process-wise) and when to shutdown a server.