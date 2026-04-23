#### Exit Notification ()


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#exit-notification-arrow_right


A notification to ask the server to exit its process. The server should exit with `success` code 0 if the shutdown request has been received before; otherwise with `error` code 1.


_Notification_ :


  * method: ‘exit’
  * params: none