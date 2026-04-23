#### Goto Definition Request ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#goto-definition-request-leftwards_arrow_with_hook


The go to definition request is sent from the client to the server to resolve the definition location of a symbol at a given text document position.


The result type [`LocationLink`](0036-locationlink.md)[] got introduced with version 3.14.0 and depends on the corresponding client capability `textDocument.definition.linkSupport`.


_Client Capability_ :


  * property name (optional): `textDocument.definition`
  * property type: `DefinitionClientCapabilities` defined as follows:


[](#definitionClientCapabilities)


    export interface DefinitionClientCapabilities {
    	/**
    	 * Whether definition supports dynamic registration.
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


  * property name (optional): `definitionProvider`
  * property type: `boolean | DefinitionOptions` where `DefinitionOptions` is defined as follows:


[](#definitionOptions)


    export interface DefinitionOptions extends WorkDoneProgressOptions {
    }
    


_Registration Options_ : `DefinitionRegistrationOptions` defined as follows:


[](#definitionRegistrationOptions)


    export interface DefinitionRegistrationOptions extends
    	TextDocumentRegistrationOptions, DefinitionOptions {
    }
    


_Request_ :


  * method: `textDocument/definition`
  * params: `DefinitionParams` defined as follows:


[](#definitionParams)


    export interface DefinitionParams extends TextDocumentPositionParams,
    	WorkDoneProgressParams, PartialResultParams {
    }
    


_Response_ :


  * result: [`Location`](0035-location.md) | [`Location`](0035-location.md)[] | [`LocationLink`](0036-locationlink.md)[] | `null`
  * partial result: [`Location`](0035-location.md)[] | [`LocationLink`](0036-locationlink.md)[]
  * error: code and message set in case an exception happens during the definition request.