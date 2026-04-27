#### Code Action Resolve Request


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#code-action-resolve-request


> _Since version 3.16.0_


The request is sent from the client to the server to resolve additional information for a given code action. This is usually used to compute the `edit` property of a code action to avoid its unnecessary computation during the `textDocument/codeAction` request.


Consider the client announcing the `edit` property as a property that can be resolved lazily using the client capability


    textDocument.codeAction.resolveSupport = { properties: ['edit'] };
    


then a code action


    {
        "title": "Do Foo"
    }
    


needs to be resolved using the `codeAction/resolve` request before it can be applied.


_Client Capability_ :


  * property name (optional): `textDocument.codeAction.resolveSupport`
  * property type: `{ properties: string[]; }`


_Request_ :


  * method: `codeAction/resolve`
  * params: `CodeAction`


_Response_ :


  * result: `CodeAction`
  * error: code and message set in case an exception happens during the code action resolve request.