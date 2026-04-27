#### Goto Type Definition Request


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#goto-type-definition-request


> _Since version 3.6.0_


The go to type definition request is sent from the client to the server to resolve the type definition location of a symbol at a given text document position.


The result type [`LocationLink`](0036-locationlink.md)[] got introduced with version 3.14.0 and depends on the corresponding client capability `textDocument.typeDefinition.linkSupport`.


_Client Capability_ :


  * property name (optional): `textDocument.typeDefinition`
  * property type: `TypeDefinitionClientCapabilities` defined as follows:


    export interface TypeDefinitionClientCapabilities {
    	/**
    	 * Whether implementation supports dynamic registration. If this is set to
    	 * `true` the client supports the new `TypeDefinitionRegistrationOptions`
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


  * property name (optional): `typeDefinitionProvider`
  * property type: `boolean | TypeDefinitionOptions | TypeDefinitionRegistrationOptions` where `TypeDefinitionOptions` is defined as follows:


    export interface TypeDefinitionOptions extends WorkDoneProgressOptions {
    }
    


_Registration Options_ : `TypeDefinitionRegistrationOptions` defined as follows:


    export interface TypeDefinitionRegistrationOptions extends
    	TextDocumentRegistrationOptions, TypeDefinitionOptions,
    	StaticRegistrationOptions {
    }
    


_Request_ :


  * method: `textDocument/typeDefinition`
  * params: `TypeDefinitionParams` defined as follows:


    export interface TypeDefinitionParams extends TextDocumentPositionParams,
    	WorkDoneProgressParams, PartialResultParams {
    }
    


_Response_ :


  * result: [`Location`](0035-location.md) | [`Location`](0035-location.md)[] | [`LocationLink`](0036-locationlink.md)[] | `null`
  * partial result: [`Location`](0035-location.md)[] | [`LocationLink`](0036-locationlink.md)[]
  * error: code and message set in case an exception happens during the definition request.