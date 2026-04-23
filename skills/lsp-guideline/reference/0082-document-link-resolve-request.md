#### Document Link Resolve Request ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#document-link-resolve-request-leftwards_arrow_with_hook


The document link resolve request is sent from the client to the server to resolve the target of a given document link.


_Request_ :


  * method: `documentLink/resolve`
  * params: `DocumentLink`


_Response_ :


  * result: `DocumentLink`
  * error: code and message set in case an exception happens during the document link resolve request.