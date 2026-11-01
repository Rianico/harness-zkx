#### Inlay Hint Refresh Request


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#inlay-hint-refresh-request


> _Since version 3.17.0_


The `workspace/inlayHint/refresh` request is sent from the server to the client. Servers can use it to ask clients to refresh the inlay hints currently shown in editors. As a result the client should ask the server to recompute the inlay hints for these editors. This is useful if a server detects a configuration change which requires a re-calculation of all inlay hints. Note that the client still has the freedom to delay the re-calculation of the inlay hints if for example an editor is currently not visible.


_Client Capability_ :


  * property name (optional): `workspace.inlayHint`
  * property type: `InlayHintWorkspaceClientCapabilities` defined as follows:


    /**
     * Client workspace capabilities specific to inlay hints.
     *
     * @since 3.17.0
     */
    export interface InlayHintWorkspaceClientCapabilities {
    	/**
    	 * Whether the client implementation supports a refresh request sent from
    	 * the server to the client.
    	 *
    	 * Note that this event is global and will force the client to refresh all
    	 * inlay hints currently shown. It should be used with absolute care and
    	 * is useful for situation where a server for example detects a project wide
    	 * change that requires such a calculation.
    	 */
    	refreshSupport?: boolean;
    }
    


_Request_ :


  * method: `workspace/inlayHint/refresh`
  * params: none


_Response_ :


  * result: void
  * error: code and message set in case an exception happens during the ‘workspace/inlayHint/refresh’ request