### File Resource changes


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#file-resource-changes


> New in version 3.13. Since version 3.16 file resource changes can carry an additional property `changeAnnotation` to describe the actual change in more detail. Whether a client has support for change annotations is guarded by the client capability `workspace.workspaceEdit.changeAnnotationSupport`.


File resource changes allow servers to create, rename and delete files and folders via the client. Note that the names talk about files but the operations are supposed to work on files and folders. This is in line with other naming in the Language Server Protocol (see file watchers which can watch files and folders). The corresponding change literals look as follows:


    /**
     * Options to create a file.
     */
    export interface CreateFileOptions {
    	/**
    	 * Overwrite existing file. Overwrite wins over `ignoreIfExists`
    	 */
    	overwrite?: boolean;
    
    	/**
    	 * Ignore if exists.
    	 */
    	ignoreIfExists?: boolean;
    }
    


    /**
     * Create file operation
     */
    export interface CreateFile {
    	/**
    	 * A create
    	 */
    	kind: 'create';
    
    	/**
    	 * The resource to create.
    	 */
    	uri: DocumentUri;
    
    	/**
    	 * Additional options
    	 */
    	options?: CreateFileOptions;
    
    	/**
    	 * An optional annotation identifier describing the operation.
    	 *
    	 * @since 3.16.0
    	 */
    	annotationId?: ChangeAnnotationIdentifier;
    }
    


    /**
     * Rename file options
     */
    export interface RenameFileOptions {
    	/**
    	 * Overwrite target if existing. Overwrite wins over `ignoreIfExists`
    	 */
    	overwrite?: boolean;
    
    	/**
    	 * Ignores if target exists.
    	 */
    	ignoreIfExists?: boolean;
    }
    


    /**
     * Rename file operation
     */
    export interface RenameFile {
    	/**
    	 * A rename
    	 */
    	kind: 'rename';
    
    	/**
    	 * The old (existing) location.
    	 */
    	oldUri: DocumentUri;
    
    	/**
    	 * The new location.
    	 */
    	newUri: DocumentUri;
    
    	/**
    	 * Rename options.
    	 */
    	options?: RenameFileOptions;
    
    	/**
    	 * An optional annotation identifier describing the operation.
    	 *
    	 * @since 3.16.0
    	 */
    	annotationId?: ChangeAnnotationIdentifier;
    }
    


    /**
     * Delete file options
     */
    export interface DeleteFileOptions {
    	/**
    	 * Delete the content recursively if a folder is denoted.
    	 */
    	recursive?: boolean;
    
    	/**
    	 * Ignore the operation if the file doesn't exist.
    	 */
    	ignoreIfNotExists?: boolean;
    }
    


    /**
     * Delete file operation
     */
    export interface DeleteFile {
    	/**
    	 * A delete
    	 */
    	kind: 'delete';
    
    	/**
    	 * The file to delete.
    	 */
    	uri: DocumentUri;
    
    	/**
    	 * Delete options.
    	 */
    	options?: DeleteFileOptions;
    
    	/**
    	 * An optional annotation identifier describing the operation.
    	 *
    	 * @since 3.16.0
    	 */
    	annotationId?: ChangeAnnotationIdentifier;
    }