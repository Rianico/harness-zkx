#### Code Lens Resolve Request ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#code-lens-resolve-request-leftwards_arrow_with_hook


The code lens resolve request is sent from the client to the server to resolve the command for a given code lens item.


_Request_ :


  * method: `codeLens/resolve`
  * params: `CodeLens`


_Response_ :


  * result: `CodeLens`
  * error: code and message set in case an exception happens during the code lens resolve request.