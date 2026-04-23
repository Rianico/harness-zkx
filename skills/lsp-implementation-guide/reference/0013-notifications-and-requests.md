#### $ Notifications and Requests


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#-notifications-and-requests


Notifications and requests whose methods start with ‘$/’ are messages which are protocol implementation dependent and might not be implementable in all clients or servers. For example if the server implementation uses a single threaded synchronous programming language then there is little a server can do to react to a `$/cancelRequest` notification. If a server or client receives notifications starting with ‘$/’ it is free to ignore the notification. If a server or client receives a request starting with ‘$/’ it must error the request with error code `MethodNotFound` (e.g. `-32601`).