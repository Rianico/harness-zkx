#### Renaming a document


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#renaming-a-document


Document renames should be signaled to a server sending a document close notification with the document’s old name followed by an open notification using the document’s new name. Major reason is that besides the name other attributes can change as well like the language that is associated with the document. In addition the new document could not be of interest for the server anymore.


Servers can participate in a document rename by subscribing for the [`workspace/didRenameFiles`](#workspace_didRenameFiles) notification or the [`workspace/willRenameFiles`](#workspace_willRenameFiles) request.


The final structure of the `TextDocumentSyncClientCapabilities` and the `TextDocumentSyncOptions` server options look like this


    export interface TextDocumentSyncClientCapabilities {
    	/**
    	 * Whether text document synchronization supports dynamic registration.
    	 */
    	dynamicRegistration?: boolean;
    
    	/**
    	 * The client supports sending will save notifications.
    	 */
    	willSave?: boolean;
    
    	/**
    	 * The client supports sending a will save request and
    	 * waits for a response providing text edits which will
    	 * be applied to the document before it is saved.
    	 */
    	willSaveWaitUntil?: boolean;
    
    	/**
    	 * The client supports did save notifications.
    	 */
    	didSave?: boolean;
    }
    


    export interface TextDocumentSyncOptions {
    	/**
    	 * Open and close notifications are sent to the server. If omitted open
    	 * close notification should not be sent.
    	 */
    	openClose?: boolean;
    	/**
    	 * Change notifications are sent to the server. See
    	 * TextDocumentSyncKind.None, TextDocumentSyncKind.Full and
    	 * TextDocumentSyncKind.Incremental. If omitted it defaults to
    	 * TextDocumentSyncKind.None.
    	 */
    	change?: TextDocumentSyncKind;
    	/**
    	 * If present will save notifications are sent to the server. If omitted
    	 * the notification should not be sent.
    	 */
    	willSave?: boolean;
    	/**
    	 * If present will save wait until requests are sent to the server. If
    	 * omitted the request should not be sent.
    	 */
    	willSaveWaitUntil?: boolean;
    	/**
    	 * If present save notifications are sent to the server. If omitted the
    	 * notification should not be sent.
    	 */
    	save?: boolean | SaveOptions;
    }