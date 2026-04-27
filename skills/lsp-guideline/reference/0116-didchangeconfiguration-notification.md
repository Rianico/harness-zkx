#### DidChangeConfiguration Notification


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#didchangeconfiguration-notification


A notification sent from the client to the server to signal the change of configuration settings.


_Client Capability_ :


  * property path (optional): `workspace.didChangeConfiguration`
  * property type: `DidChangeConfigurationClientCapabilities` defined as follows:


    export interface DidChangeConfigurationClientCapabilities {
    	/**
    	 * Did change configuration notification supports dynamic registration.
    	 *
    	 * @since 3.6.0 to support the new pull model.
    	 */
    	dynamicRegistration?: boolean;
    }
    


_Notification_ :


  * method: ‘workspace/didChangeConfiguration’,
  * params: `DidChangeConfigurationParams` defined as follows:


    interface DidChangeConfigurationParams {
    	/**
    	 * The actual changed settings
    	 */
    	settings: LSPAny;
    }