#### Code Lens Refresh Request ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#code-lens-refresh-request-arrow_right_hook


> _Since version 3.16.0_


The `workspace/codeLens/refresh` request is sent from the server to the client. Servers can use it to ask clients to refresh the code lenses currently shown in editors. As a result the client should ask the server to recompute the code lenses for these editors. This is useful if a server detects a configuration change which requires a re-calculation of all code lenses. Note that the client still has the freedom to delay the re-calculation of the code lenses if for example an editor is currently not visible.


_Client Capability_ :


  * property name (optional): `workspace.codeLens`
  * property type: `CodeLensWorkspaceClientCapabilities` defined as follows:


[](#codeLensWorkspaceClientCapabilities)


    export interface CodeLensWorkspaceClientCapabilities {
    	/**
    	 * Whether the client implementation supports a refresh request sent from the
    	 * server to the client.
    	 *
    	 * Note that this event is global and will force the client to refresh all
    	 * code lenses currently shown. It should be used with absolute care and is
    	 * useful for situation where a server for example detect a project wide
    	 * change that requires such a calculation.
    	 */
    	refreshSupport?: boolean;
    }
    


_Request_ :


  * method: `workspace/codeLens/refresh`
  * params: none


_Response_ :


  * result: void
  * error: code and message set in case an exception happens during the ‘workspace/codeLens/refresh’ request