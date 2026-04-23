#### Abstract Message


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#abstract-message


A general message as defined by JSON-RPC. The language server protocol always uses “2.0” as the `jsonrpc` version.


[](#message)


    interface Message {
    	jsonrpc: string;
    }