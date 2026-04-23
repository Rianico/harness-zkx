#### Notification Message


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#notification-message


A notification message. A processed notification message must not send a response back. They work like events.


    interface NotificationMessage extends Message {
    	/**
    	 * The method to be invoked.
    	 */
    	method: string;
    
    	/**
    	 * The notification's params.
    	 */
    	params?: array | object;
    }