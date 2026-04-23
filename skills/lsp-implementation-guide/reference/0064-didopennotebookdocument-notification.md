#### DidOpenNotebookDocument Notification ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#didopennotebookdocument-notification-arrow_right


The open notification is sent from the client to the server when a notebook document is opened. It is only sent by a client if the server requested the synchronization mode `notebook` in its `notebookDocumentSync` capability.


_Notification_ :


  * method: `notebookDocument/didOpen`
  * params: `DidOpenNotebookDocumentParams` defined as follows:


[](#didOpenNotebookDocumentParams)


    /**
     * The params sent in an open notebook document notification.
     *
     * @since 3.17.0
     */
    export interface DidOpenNotebookDocumentParams {
    
    	/**
    	 * The notebook document that got opened.
    	 */
    	notebookDocument: NotebookDocument;
    
    	/**
    	 * The text documents that represent the content
    	 * of a notebook cell.
    	 */
    	cellTextDocuments: TextDocumentItem[];
    }