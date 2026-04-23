#### Cancellation Support ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#cancellation-support-arrow_right-arrow_left


The base protocol offers support for request cancellation. To cancel a request, a notification message with the following properties is sent:


_Notification_ :


  * method: ‘$/cancelRequest’  
  * params: `CancelParams` defined as follows:


    interface CancelParams {
    	/**
    	 * The request id to cancel.
    	 */
    	id: integer | string;
    }
    


A request that got canceled still needs to return from the server and send a response back. It can not be left open / hanging. This is in line with the JSON-RPC protocol that requires that every request sends a response back. In addition it allows for returning partial results on cancel. If the request returns an error response on cancellation it is advised to set the error code to `ErrorCodes.RequestCancelled`.