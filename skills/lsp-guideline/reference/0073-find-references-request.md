#### Find References Request


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#find-references-request


The references request is sent from the client to the server to resolve project-wide references for the symbol denoted by the given text document position.


_Client Capability_ :


  * property name (optional): `textDocument.references`
  * property type: `ReferenceClientCapabilities` defined as follows:


    export interface ReferenceClientCapabilities {
    	/**
    	 * Whether references supports dynamic registration.
    	 */
    	dynamicRegistration?: boolean;
    }
    


_Server Capability_ :


  * property name (optional): `referencesProvider`
  * property type: `boolean | ReferenceOptions` where `ReferenceOptions` is defined as follows:


    export interface ReferenceOptions extends WorkDoneProgressOptions {
    }
    


_Registration Options_ : `ReferenceRegistrationOptions` defined as follows:


    export interface ReferenceRegistrationOptions extends
    	TextDocumentRegistrationOptions, ReferenceOptions {
    }
    


_Request_ :


  * method: `textDocument/references`
  * params: `ReferenceParams` defined as follows:


    export interface ReferenceParams extends TextDocumentPositionParams,
    	WorkDoneProgressParams, PartialResultParams {
    	context: ReferenceContext;
    }
    


    export interface ReferenceContext {
    	/**
    	 * Include the declaration of the current symbol.
    	 */
    	includeDeclaration: boolean;
    }
    


_Response_ :


  * result: [`Location`](0035-location.md)[] | `null`
  * partial result: [`Location`](0035-location.md)[]
  * error: code and message set in case an exception happens during the reference request.