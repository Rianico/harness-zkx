#### DidCloseNotebookDocument Notification ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#didclosenotebookdocument-notification-arrow_right


The close notification is sent from the client to the server when a notebook document is closed. It is only sent by a client if the server requested the synchronization mode `notebook` in its `notebookDocumentSync` capability.


_Notification_ :


[](#notebookDocument_didClose)


  * method: `notebookDocument/didClose`
  * params: `DidCloseNotebookDocumentParams` defined as follows:


[](#didCloseNotebookDocumentParams)


    /**
     * The params sent in a close notebook document notification.
     *
     * @since 3.17.0
     */
    export interface DidCloseNotebookDocumentParams {
    
    	/**
    	 * The notebook document that got closed.
    	 */
    	notebookDocument: NotebookDocumentIdentifier;
    
    	/**
    	 * The text documents that represent the content
    	 * of a notebook cell that got closed.
    	 */
    	cellTextDocuments: TextDocumentIdentifier[];
    }
    


[](#notebookDocumentIdentifier)


    /**
     * A literal to identify a notebook document in the client.
     *
     * @since 3.17.0
     */
    export interface NotebookDocumentIdentifier {
    	/**
    	 * The notebook document's URI.
    	 */
    	uri: URI;
    }