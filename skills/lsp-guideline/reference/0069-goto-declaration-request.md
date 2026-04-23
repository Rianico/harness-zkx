#### Goto Declaration Request ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#goto-declaration-request-leftwards_arrow_with_hook


> _Since version 3.14.0_


The go to declaration request is sent from the client to the server to resolve the declaration location of a symbol at a given text document position.


The result type [`LocationLink`](0036-locationlink.md)[] got introduced with version 3.14.0 and depends on the corresponding client capability `textDocument.declaration.linkSupport`.


_Client Capability_ :


  * property name (optional): `textDocument.declaration`
  * property type: `DeclarationClientCapabilities` defined as follows:


[](#declarationClientCapabilities)


    export interface DeclarationClientCapabilities {
    	/**
    	 * Whether declaration supports dynamic registration. If this is set to
    	 * `true` the client supports the new `DeclarationRegistrationOptions`
    	 * return value for the corresponding server capability as well.
    	 */
    	dynamicRegistration?: boolean;
    
    	/**
    	 * The client supports additional metadata in the form of declaration links.
    	 */
    	linkSupport?: boolean;
    }
    


_Server Capability_ :


  * property name (optional): `declarationProvider`
  * property type: `boolean | DeclarationOptions | DeclarationRegistrationOptions` where `DeclarationOptions` is defined as follows:


[](#declarationOptions)


    export interface DeclarationOptions extends WorkDoneProgressOptions {
    }
    


_Registration Options_ : `DeclarationRegistrationOptions` defined as follows:


[](#declarationRegistrationOptions)


    export interface DeclarationRegistrationOptions extends DeclarationOptions,
    	TextDocumentRegistrationOptions, StaticRegistrationOptions {
    }
    


_Request_ :


  * method: `textDocument/declaration`
  * params: `DeclarationParams` defined as follows:


[](#declarationParams)


    export interface DeclarationParams extends TextDocumentPositionParams,
    	WorkDoneProgressParams, PartialResultParams {
    }
    


_Response_ :


  * result: [`Location`](0035-location.md) | [`Location`](0035-location.md)[] | [`LocationLink`](0036-locationlink.md)[] |`null`
  * partial result: [`Location`](0035-location.md)[] | [`LocationLink`](0036-locationlink.md)[]
  * error: code and message set in case an exception happens during the declaration request.