#### LogMessage Notification ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#logmessage-notification-arrow_left


The log message notification is sent from the server to the client to ask the client to log a particular message.


_Notification_ :


  * method: ‘window/logMessage’
  * params: `LogMessageParams` defined as follows:


[](#logMessageParams)


    interface LogMessageParams {
    	/**
    	 * The message type. See {@link MessageType}
    	 */
    	type: MessageType;
    
    	/**
    	 * The actual message
    	 */
    	message: string;
    }