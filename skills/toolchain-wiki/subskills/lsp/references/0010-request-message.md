#### Request Message


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#request-message


A request message to describe a request between the client and the server. Every processed request must send a response back to the sender of the request.


    interface RequestMessage extends Message {
    
    	/**
    	 * The request id.
    	 */
    	id: integer | string;
    
    	/**
    	 * The method to be invoked.
    	 */
    	method: string;
    
    	/**
    	 * The method's params.
    	 */
    	params?: array | object;
    }