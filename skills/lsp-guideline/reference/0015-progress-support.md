#### Progress Support ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#progress-support-arrow_right-arrow_left


> _Since version 3.15.0_


The base protocol offers also support to report progress in a generic fashion. This mechanism can be used to report any kind of progress including [work done progress](#workDoneProgress) (usually used to report progress in the user interface using a progress bar) and partial result progress to support streaming of results.


A progress notification has the following properties:


_Notification_ :


  * method: ‘$/progress’
  * params: `ProgressParams` defined as follows:


    type ProgressToken = integer | string;
    


    interface ProgressParams<T> {
    	/**
    	 * The progress token provided by the client or server.
    	 */
    	token: ProgressToken;
    
    	/**
    	 * The progress data.
    	 */
    	value: T;
    }
    


Progress is reported against a token. The token is different than the request ID which allows to report progress out of band and also for notification.