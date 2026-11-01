#### Code Lens Request


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#code-lens-request


The code lens request is sent from the client to the server to compute code lenses for a given text document.


_Client Capability_ :


  * property name (optional): `textDocument.codeLens`
  * property type: `CodeLensClientCapabilities` defined as follows:


    export interface CodeLensClientCapabilities {
    	/**
    	 * Whether code lens supports dynamic registration.
    	 */
    	dynamicRegistration?: boolean;
    }
    


_Server Capability_ :


  * property name (optional): `codeLensProvider`
  * property type: `CodeLensOptions` defined as follows:


    export interface CodeLensOptions extends WorkDoneProgressOptions {
    	/**
    	 * Code lens has a resolve provider as well.
    	 */
    	resolveProvider?: boolean;
    }
    


_Registration Options_ : `CodeLensRegistrationOptions` defined as follows:


    export interface CodeLensRegistrationOptions extends
    	TextDocumentRegistrationOptions, CodeLensOptions {
    }
    


_Request_ :


  * method: `textDocument/codeLens`
  * params: `CodeLensParams` defined as follows:


    interface CodeLensParams extends WorkDoneProgressParams, PartialResultParams {
    	/**
    	 * The document to request code lens for.
    	 */
    	textDocument: TextDocumentIdentifier;
    }
    


_Response_ :


  * result: `CodeLens[]` | `null` defined as follows:


    /**
     * A code lens represents a command that should be shown along with
     * source text, like the number of references, a way to run tests, etc.
     *
     * A code lens is _unresolved_ when no command is associated to it. For
     * performance reasons the creation of a code lens and resolving should be done
     * in two stages.
     */
    interface CodeLens {
    	/**
    	 * The range in which this code lens is valid. Should only span a single
    	 * line.
    	 */
    	range: Range;
    
    	/**
    	 * The command this code lens represents.
    	 */
    	command?: Command;
    
    	/**
    	 * A data entry field that is preserved on a code lens item between
    	 * a code lens and a code lens resolve request.
    	 */
    	data?: LSPAny;
    }
    


  * partial result: `CodeLens[]`
  * error: code and message set in case an exception happens during the code lens request.