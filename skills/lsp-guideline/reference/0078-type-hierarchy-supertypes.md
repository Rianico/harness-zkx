#### Type Hierarchy Supertypes()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#type-hierarchy-supertypesleftwards_arrow_with_hook


> _Since version 3.17.0_


The request is sent from the client to the server to resolve the supertypes for a given type hierarchy item. Will return `null` if the server couldn’t infer a valid type from `item` in the params. The request doesn’t define its own client and server capabilities. It is only issued if a server registers for the [`textDocument/prepareTypeHierarchy` request](#textDocument_prepareTypeHierarchy).


_Request_ :


  * method: ‘typeHierarchy/supertypes’
  * params: `TypeHierarchySupertypesParams` defined as follows:


[](#typeHierarchySupertypesParams)


    export interface TypeHierarchySupertypesParams extends
    	WorkDoneProgressParams, PartialResultParams {
    	item: TypeHierarchyItem;
    }
    


_Response_ :


  * result: `TypeHierarchyItem[] | null`
  * partial result: `TypeHierarchyItem[]`
  * error: code and message set in case an exception happens during the ‘typeHierarchy/supertypes’ request