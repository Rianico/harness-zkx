#### Prepare Call Hierarchy Request ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#prepare-call-hierarchy-request-leftwards_arrow_with_hook


> _Since version 3.16.0_


The call hierarchy request is sent from the client to the server to return a call hierarchy for the language element of given text document positions. The call hierarchy requests are executed in two steps:


  1. first a call hierarchy item is resolved for the given text document position
  2. for a call hierarchy item the incoming or outgoing call hierarchy items are resolved.


_Client Capability_ :


  * property name (optional): `textDocument.callHierarchy`
  * property type: `CallHierarchyClientCapabilities` defined as follows:


[](#callHierarchyClientCapabilities)


    interface CallHierarchyClientCapabilities {
    	/**
    	 * Whether implementation supports dynamic registration. If this is set to
    	 * `true` the client supports the new `(TextDocumentRegistrationOptions &
    	 * StaticRegistrationOptions)` return value for the corresponding server
    	 * capability as well.
    	 */
    	dynamicRegistration?: boolean;
    }
    


_Server Capability_ :


  * property name (optional): `callHierarchyProvider`
  * property type: `boolean | CallHierarchyOptions | CallHierarchyRegistrationOptions` where `CallHierarchyOptions` is defined as follows:


[](#callHierarchyOptions)


    export interface CallHierarchyOptions extends WorkDoneProgressOptions {
    }
    


_Registration Options_ : `CallHierarchyRegistrationOptions` defined as follows:


[](#callHierarchyRegistrationOptions)


    export interface CallHierarchyRegistrationOptions extends
    	TextDocumentRegistrationOptions, CallHierarchyOptions,
    	StaticRegistrationOptions {
    }
    


_Request_ :


  * method: `textDocument/prepareCallHierarchy`
  * params: `CallHierarchyPrepareParams` defined as follows:


[](#callHierarchyPrepareParams)


    export interface CallHierarchyPrepareParams extends TextDocumentPositionParams,
    	WorkDoneProgressParams {
    }
    


_Response_ :


  * result: `CallHierarchyItem[] | null` defined as follows:


[](#callHierarchyItem)


    export interface CallHierarchyItem {
    	/**
    	 * The name of this item.
    	 */
    	name: string;
    
    	/**
    	 * The kind of this item.
    	 */
    	kind: SymbolKind;
    
    	/**
    	 * Tags for this item.
    	 */
    	tags?: SymbolTag[];
    
    	/**
    	 * More detail for this item, e.g. the signature of a function.
    	 */
    	detail?: string;
    
    	/**
    	 * The resource identifier of this item.
    	 */
    	uri: DocumentUri;
    
    	/**
    	 * The range enclosing this symbol not including leading/trailing whitespace
    	 * but everything else, e.g. comments and code.
    	 */
    	range: Range;
    
    	/**
    	 * The range that should be selected and revealed when this symbol is being
    	 * picked, e.g. the name of a function. Must be contained by the
    	 * [`range`](#CallHierarchyItem.range).
    	 */
    	selectionRange: Range;
    
    	/**
    	 * A data entry field that is preserved between a call hierarchy prepare and
    	 * incoming calls or outgoing calls requests.
    	 */
    	data?: LSPAny;
    }
    


  * error: code and message set in case an exception happens during the ‘textDocument/prepareCallHierarchy’ request