#### Prepare Type Hierarchy Request ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#prepare-type-hierarchy-request-leftwards_arrow_with_hook


> _Since version 3.17.0_


The type hierarchy request is sent from the client to the server to return a type hierarchy for the language element of given text document positions. Will return `null` if the server couldn’t infer a valid type from the position. The type hierarchy requests are executed in two steps:


  1. first a type hierarchy item is prepared for the given text document position.
  2. for a type hierarchy item the supertype or subtype type hierarchy items are resolved.


_Client Capability_ :


  * property name (optional): `textDocument.typeHierarchy`
  * property type: `TypeHierarchyClientCapabilities` defined as follows:


[](#typeHierarchyClientCapabilities)


    type TypeHierarchyClientCapabilities = {
    	/**
    	 * Whether implementation supports dynamic registration. If this is set to
    	 * `true` the client supports the new `(TextDocumentRegistrationOptions &
    	 * StaticRegistrationOptions)` return value for the corresponding server
    	 * capability as well.
    	 */
    	dynamicRegistration?: boolean;
    };
    


_Server Capability_ :


  * property name (optional): `typeHierarchyProvider`
  * property type: `boolean | TypeHierarchyOptions | TypeHierarchyRegistrationOptions` where `TypeHierarchyOptions` is defined as follows:


[](#typeHierarchyOptions)


    export interface TypeHierarchyOptions extends WorkDoneProgressOptions {
    }
    


_Registration Options_ : `TypeHierarchyRegistrationOptions` defined as follows:


[](#typeHierarchyRegistrationOptions)


    export interface TypeHierarchyRegistrationOptions extends
    	TextDocumentRegistrationOptions, TypeHierarchyOptions,
    	StaticRegistrationOptions {
    }
    


_Request_ :


  * method: ‘textDocument/prepareTypeHierarchy’
  * params: `TypeHierarchyPrepareParams` defined as follows:


[](#typeHierarchyPrepareParams)


    export interface TypeHierarchyPrepareParams extends TextDocumentPositionParams,
    	WorkDoneProgressParams {
    }
    


_Response_ :


  * result: `TypeHierarchyItem[] | null` defined as follows:


[](#typeHierarchyItem)


    export interface TypeHierarchyItem {
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
    	 * [`range`](#TypeHierarchyItem.range).
    	 */
    	selectionRange: Range;
    
    	/**
    	 * A data entry field that is preserved between a type hierarchy prepare and
    	 * supertypes or subtypes requests. It could also be used to identify the
    	 * type hierarchy in the server, helping improve the performance on
    	 * resolving supertypes and subtypes.
    	 */
    	data?: LSPAny;
    }
    


  * error: code and message set in case an exception happens during the ‘textDocument/prepareTypeHierarchy’ request