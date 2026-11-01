#### Workspace Symbol Resolve Request


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace-symbol-resolve-request


The request is sent from the client to the server to resolve additional information for a given workspace symbol.


_Request_ :


  * method: ‘workspaceSymbol/resolve’
  * params: `WorkspaceSymbol`


_Response_ :


  * result: `WorkspaceSymbol`
  * error: code and message set in case an exception happens during the workspace symbol resolve request.