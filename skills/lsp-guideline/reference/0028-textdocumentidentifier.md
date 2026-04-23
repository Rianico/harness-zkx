#### TextDocumentIdentifier


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textdocumentidentifier


Text documents are identified using a URI. On the protocol level, URIs are passed as strings. The corresponding JSON structure looks like this:


    interface TextDocumentIdentifier {
    	/**
    	 * The text document's URI.
    	 */
    	uri: DocumentUri;
    }