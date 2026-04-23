#### Completion Item Resolve Request ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#completion-item-resolve-request-leftwards_arrow_with_hook


The request is sent from the client to the server to resolve additional information for a given completion item.


_Request_ :


  * method: `completionItem/resolve`
  * params: `CompletionItem`


_Response_ :


  * result: `CompletionItem`
  * error: code and message set in case an exception happens during the completion resolve request.