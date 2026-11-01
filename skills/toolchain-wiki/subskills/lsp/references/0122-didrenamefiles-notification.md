#### DidRenameFiles Notification


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#didrenamefiles-notification


The did rename files notification is sent from the client to the server when files were renamed from within the client.


_Client Capability_ :


  * property name (optional): `workspace.fileOperations.didRename`
  * property type: `boolean`


The capability indicates that the client supports sending `workspace/didRenameFiles` notifications.


_Server Capability_ :


  * property name (optional): `workspace.fileOperations.didRename`
  * property type: `FileOperationRegistrationOptions`


The capability indicates that the server is interested in receiving `workspace/didRenameFiles` notifications.


_Notification_ :


  * method: ‘workspace/didRenameFiles’
  * params: `RenameFilesParams`