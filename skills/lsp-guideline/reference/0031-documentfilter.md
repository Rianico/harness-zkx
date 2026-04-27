#### DocumentFilter


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentfilter


A document filter denotes a document through properties like `language`, `scheme` or `pattern`. An example is a filter that applies to TypeScript files on disk. Another example is a filter that applies to JSON files with name `package.json`:


    { language: 'typescript', scheme: 'file' }
    { language: 'json', pattern: '**/package.json' }
    


    export interface DocumentFilter {
    	/**
    	 * A language id, like `typescript`.
    	 */
    	language?: string;
    
    	/**
    	 * A Uri scheme, like `file` or `untitled`.
    	 */
    	scheme?: string;
    
    	/**
    	 * A glob pattern, like `*.{ts,js}`.
    	 *
    	 * Glob patterns can have the following syntax:
    	 * - `*` to match zero or more characters in a path segment
    	 * - `?` to match on one character in a path segment
    	 * - `**` to match any number of path segments, including none
    	 * - `{}` to group sub patterns into an OR expression. (e.g. `**​/*.{ts,js}`
    	 *   matches all TypeScript and JavaScript files)
    	 * - `[]` to declare a range of characters to match in a path segment
    	 *   (e.g., `example.[0-9]` to match on `example.0`, `example.1`, …)
    	 * - `[!...]` to negate a range of characters to match in a path segment
    	 *   (e.g., `example.[!0-9]` to match on `example.a`, `example.b`, but
    	 *   not `example.0`)
    	 */
    	pattern?: string;
    }
    


Please note that for a document filter to be valid at least one of the properties for `language`, `scheme`, or `pattern` must be set. To keep the type definition simple all properties are marked as optional.


A document selector is the combination of one or more document filters.


    export type DocumentSelector = DocumentFilter[];