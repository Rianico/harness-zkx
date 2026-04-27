#### Prepare Rename Request


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#prepare-rename-request


> _Since version 3.12.0_


The prepare rename request is sent from the client to the server to setup and test the validity of a rename operation at a given location.


_Request_ :


  * method: `textDocument/prepareRename`
  * params: `PrepareRenameParams` defined as follows:


    export interface PrepareRenameParams extends TextDocumentPositionParams, WorkDoneProgressParams {
    }
    


_Response_ :


  * result: `Range | { range: Range, placeholder: string } | { defaultBehavior: boolean } | null` describing a [`Range`](0026-range.md) of the string to rename and optionally a placeholder text of the string content to be renamed. If `{ defaultBehavior: boolean }` is returned (since 3.16) the rename position is valid and the client should use its default behavior to compute the rename range. If `null` is returned then it is deemed that a ‘textDocument/rename’ request is not valid at the given position.
  * error: code and message set in case the element can’t be renamed. Clients should show the information in their user interface.