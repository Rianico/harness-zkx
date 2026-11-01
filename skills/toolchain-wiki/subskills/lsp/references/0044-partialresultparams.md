#### PartialResultParams


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#partialresultparams


A parameter literal used to pass a partial result token.


    export interface PartialResultParams {
    	/**
    	 * An optional token that a server can use to report partial results (e.g.
    	 * streaming) to the client.
    	 */
    	partialResultToken?: ProgressToken;
    }