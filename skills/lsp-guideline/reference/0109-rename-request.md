#### Rename Request ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#rename-request-leftwards_arrow_with_hook


The rename request is sent from the client to the server to ask the server to compute a workspace change so that the client can perform a workspace-wide rename of a symbol.


_Client Capability_ :


  * property name (optional): `textDocument.rename`
  * property type: `RenameClientCapabilities` defined as follows:


[](#prepareSupportDefaultBehavior)


    export namespace PrepareSupportDefaultBehavior {
    	/**
    	 * The client's default behavior is to select the identifier
    	 * according to the language's syntax rule.
    	 */
    	 export const Identifier: 1 = 1;
    }
    
    export type PrepareSupportDefaultBehavior = 1;
    


[](#renameClientCapabilities)


    export interface RenameClientCapabilities {
    	/**
    	 * Whether rename supports dynamic registration.
    	 */
    	dynamicRegistration?: boolean;
    
    	/**
    	 * Client supports testing for validity of rename operations
    	 * before execution.
    	 *
    	 * @since version 3.12.0
    	 */
    	prepareSupport?: boolean;
    
    	/**
    	 * Client supports the default behavior result
    	 * (`{ defaultBehavior: boolean }`).
    	 *
    	 * The value indicates the default behavior used by the
    	 * client.
    	 *
    	 * @since version 3.16.0
    	 */
    	prepareSupportDefaultBehavior?: PrepareSupportDefaultBehavior;
    
    	/**
    	 * Whether the client honors the change annotations in
    	 * text edits and resource operations returned via the
    	 * rename request's workspace edit by for example presenting
    	 * the workspace edit in the user interface and asking
    	 * for confirmation.
    	 *
    	 * @since 3.16.0
    	 */
    	honorsChangeAnnotations?: boolean;
    }
    


_Server Capability_ :


  * property name (optional): `renameProvider`
  * property type: `boolean | RenameOptions` where `RenameOptions` is defined as follows:


`RenameOptions` may only be specified if the client states that it supports `prepareSupport` in its initial `initialize` request.


[](#renameOptions)


    export interface RenameOptions extends WorkDoneProgressOptions {
    	/**
    	 * Renames should be checked and tested before being executed.
    	 */
    	prepareProvider?: boolean;
    }
    


_Registration Options_ : `RenameRegistrationOptions` defined as follows:


[](#renameRegistrationOptions)


    export interface RenameRegistrationOptions extends
    	TextDocumentRegistrationOptions, RenameOptions {
    }
    


_Request_ :


  * method: `textDocument/rename`
  * params: `RenameParams` defined as follows


[](#renameParams)


    interface RenameParams extends TextDocumentPositionParams,
    	WorkDoneProgressParams {
    	/**
    	 * The new name of the symbol. If the given name is not valid the
    	 * request must return a [ResponseError](#ResponseError) with an
    	 * appropriate message set.
    	 */
    	newName: string;
    }
    


_Response_ :


  * result: [`WorkspaceEdit`](0041-workspaceedit.md) | `null` describing the modification to the workspace. `null` should be treated the same was as [`WorkspaceEdit`](0041-workspaceedit.md) with no changes (no change was required).
  * error: code and message set in case when rename could not be performed for any reason. Examples include: there is nothing at given `position` to rename (like a space), given symbol does not support renaming by the server or the code is invalid (e.g. does not compile).