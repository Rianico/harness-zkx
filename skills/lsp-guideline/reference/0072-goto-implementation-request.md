#### Goto Implementation Request ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#goto-implementation-request-leftwards_arrow_with_hook


> _Since version 3.6.0_


The go to implementation request is sent from the client to the server to resolve the implementation location of a symbol at a given text document position.


The result type [`LocationLink`](0036-locationlink.md)[] got introduced with version 3.14.0 and depends on the corresponding client capability `textDocument.implementation.linkSupport`.


_Client Capability_ :


  * property name (optional): `textDocument.implementation`
  * property type: `ImplementationClientCapabilities` defined as follows:


[](#implementationClientCapabilities)


    export interface ImplementationClientCapabilities {
    	/**
    	 * Whether implementation supports dynamic registration. If this is set to
    	 * `true` the client supports the new `ImplementationRegistrationOptions`
    	 * return value for the corresponding server capability as well.
    	 */
    	dynamicRegistration?: boolean;
    
    	/**
    	 * The client supports additional metadata in the form of definition links.
    	 *
    	 * @since 3.14.0
    	 */
    	linkSupport?: boolean;
    }
    


_Server Capability_ :


  * property name (optional): `implementationProvider`
  * property type: `boolean | ImplementationOptions | ImplementationRegistrationOptions` where `ImplementationOptions` is defined as follows:


[](#implementationOptions)


    export interface ImplementationOptions extends WorkDoneProgressOptions {
    }
    


_Registration Options_ : `ImplementationRegistrationOptions` defined as follows:


[](#implementationRegistrationOptions)


    export interface ImplementationRegistrationOptions extends
    	TextDocumentRegistrationOptions, ImplementationOptions,
    	StaticRegistrationOptions {
    }
    


_Request_ :


  * method: `textDocument/implementation`
  * params: `ImplementationParams` defined as follows:


[](#implementationParams)


    export interface ImplementationParams extends TextDocumentPositionParams,
    	WorkDoneProgressParams, PartialResultParams {
    }
    


_Response_ :


  * result: [`Location`](0035-location.md) | [`Location`](0035-location.md)[] | [`LocationLink`](0036-locationlink.md)[] | `null`
  * partial result: [`Location`](0035-location.md)[] | [`LocationLink`](0036-locationlink.md)[]
  * error: code and message set in case an exception happens during the definition request.