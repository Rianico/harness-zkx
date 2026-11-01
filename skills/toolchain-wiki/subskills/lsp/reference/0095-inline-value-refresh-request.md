#### Inline Value Refresh Request


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#inline-value-refresh-request


> _Since version 3.17.0_


The `workspace/inlineValue/refresh` request is sent from the server to the client. Servers can use it to ask clients to refresh the inline values currently shown in editors. As a result the client should ask the server to recompute the inline values for these editors. This is useful if a server detects a configuration change which requires a re-calculation of all inline values. Note that the client still has the freedom to delay the re-calculation of the inline values if for example an editor is currently not visible.


_Client Capability_ :


  * property name (optional): `workspace.inlineValue`
  * property type: `InlineValueWorkspaceClientCapabilities` defined as follows:


    /**
     * Client workspace capabilities specific to inline values.
     *
     * @since 3.17.0
     */
    export interface InlineValueWorkspaceClientCapabilities {
    	/**
    	 * Whether the client implementation supports a refresh request sent from
    	 * the server to the client.
    	 *
    	 * Note that this event is global and will force the client to refresh all
    	 * inline values currently shown. It should be used with absolute care and
    	 * is useful for situation where a server for example detect a project wide
    	 * change that requires such a calculation.
    	 */
    	refreshSupport?: boolean;
    }
    


_Request_ :


  * method: `workspace/inlineValue/refresh`
  * params: none


_Response_ :


  * result: void
  * error: code and message set in case an exception happens during the ‘workspace/inlineValue/refresh’ request