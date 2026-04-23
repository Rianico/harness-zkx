#### Location


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#location


Represents a location inside a resource, such as a line inside a text file.


    interface Location {
    	uri: DocumentUri;
    	range: Range;
    }