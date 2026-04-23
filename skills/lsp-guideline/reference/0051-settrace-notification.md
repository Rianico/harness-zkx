#### SetTrace Notification ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#settrace-notification-arrow_right


A notification that should be used by the client to modify the trace setting of the server.


_Notification_ :


  * method: ‘$/setTrace’
  * params: `SetTraceParams` defined as follows:


    interface SetTraceParams {
    	/**
    	 * The new value that should be assigned to the trace setting.
    	 */
    	value: TraceValue;
    }