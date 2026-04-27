#### Call Hierarchy Incoming Calls


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#call-hierarchy-incoming-calls


> _Since version 3.16.0_


The request is sent from the client to the server to resolve incoming calls for a given call hierarchy item. The request doesn’t define its own client and server capabilities. It is only issued if a server registers for the [`textDocument/prepareCallHierarchy` request](#textDocument_prepareCallHierarchy).


_Request_ :


  * method: `callHierarchy/incomingCalls`
  * params: `CallHierarchyIncomingCallsParams` defined as follows:


    export interface CallHierarchyIncomingCallsParams extends
    	WorkDoneProgressParams, PartialResultParams {
    	item: CallHierarchyItem;
    }
    


_Response_ :


  * result: `CallHierarchyIncomingCall[] | null` defined as follows:


    export interface CallHierarchyIncomingCall {
    
    	/**
    	 * The item that makes the call.
    	 */
    	from: CallHierarchyItem;
    
    	/**
    	 * The ranges at which the calls appear. This is relative to the caller
    	 * denoted by [`this.from`](#CallHierarchyIncomingCall.from).
    	 */
    	fromRanges: Range[];
    }
    


  * partial result: `CallHierarchyIncomingCall[]`
  * error: code and message set in case an exception happens during the ‘callHierarchy/incomingCalls’ request