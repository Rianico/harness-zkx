#### Response Message


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#response-message


A Response Message sent as a result of a request. If a request doesn’t provide a result value the receiver of a request still needs to return a response message to conform to the JSON-RPC specification. The result property of the ResponseMessage should be set to `null` in this case to signal a successful request.


    interface ResponseMessage extends Message {
    	/**
    	 * The request id.
    	 */
    	id: integer | string | null;
    
    	/**
    	 * The result of a request. This member is REQUIRED on success.
    	 * This member MUST NOT exist if there was an error invoking the method.
    	 */
    	result?: LSPAny;
    
    	/**
    	 * The error object in case a request fails.
    	 */
    	error?: ResponseError;
    }
    


    interface ResponseError {
    	/**
    	 * A number indicating the error type that occurred.
    	 */
    	code: integer;
    
    	/**
    	 * A string providing a short description of the error.
    	 */
    	message: string;
    
    	/**
    	 * A primitive or structured value that contains additional
    	 * information about the error. Can be omitted.
    	 */
    	data?: LSPAny;
    }
    


    export namespace ErrorCodes {
    	// Defined by JSON-RPC
    	export const ParseError: integer = -32700;
    	export const InvalidRequest: integer = -32600;
    	export const MethodNotFound: integer = -32601;
    	export const InvalidParams: integer = -32602;
    	export const InternalError: integer = -32603;
    
    	/**
    	 * This is the start range of JSON-RPC reserved error codes.
    	 * It doesn't denote a real error code. No LSP error codes should
    	 * be defined between the start and end range. For backwards
    	 * compatibility the `ServerNotInitialized` and the `UnknownErrorCode`
    	 * are left in the range.
    	 *
    	 * @since 3.16.0
    	 */
    	export const jsonrpcReservedErrorRangeStart: integer = -32099;
    	/** @deprecated use jsonrpcReservedErrorRangeStart */
    	export const serverErrorStart: integer = jsonrpcReservedErrorRangeStart;
    
    	/**
    	 * Error code indicating that a server received a notification or
    	 * request before the server received the `initialize` request.
    	 */
    	export const ServerNotInitialized: integer = -32002;
    	export const UnknownErrorCode: integer = -32001;
    
    	/**
    	 * This is the end range of JSON-RPC reserved error codes.
    	 * It doesn't denote a real error code.
    	 *
    	 * @since 3.16.0
    	 */
    	export const jsonrpcReservedErrorRangeEnd = -32000;
    	/** @deprecated use jsonrpcReservedErrorRangeEnd */
    	export const serverErrorEnd: integer = jsonrpcReservedErrorRangeEnd;
    
    	/**
    	 * This is the start range of LSP reserved error codes.
    	 * It doesn't denote a real error code.
    	 *
    	 * @since 3.16.0
    	 */
    	export const lspReservedErrorRangeStart: integer = -32899;
    
    	/**
    	 * A request failed but it was syntactically correct, e.g the
    	 * method name was known and the parameters were valid. The error
    	 * message should contain human readable information about why
    	 * the request failed.
    	 *
    	 * @since 3.17.0
    	 */
    	export const RequestFailed: integer = -32803;
    
    	/**
    	 * The server cancelled the request. This error code should
    	 * only be used for requests that explicitly support being
    	 * server cancellable.
    	 *
    	 * @since 3.17.0
    	 */
    	export const ServerCancelled: integer = -32802;
    
    	/**
    	 * The server detected that the content of a document got
    	 * modified outside normal conditions. A server should
    	 * NOT send this error code if it detects a content change
    	 * in its unprocessed messages. The result even computed
    	 * on an older state might still be useful for the client.
    	 *
    	 * If a client decides that a result is not of any use anymore
    	 * the client should cancel the request.
    	 */
    	export const ContentModified: integer = -32801;
    
    	/**
    	 * The client has canceled a request and a server has detected
    	 * the cancel.
    	 */
    	export const RequestCancelled: integer = -32800;
    
    	/**
    	 * This is the end range of LSP reserved error codes.
    	 * It doesn't denote a real error code.
    	 *
    	 * @since 3.16.0
    	 */
    	export const lspReservedErrorRangeEnd: integer = -32800;
    }