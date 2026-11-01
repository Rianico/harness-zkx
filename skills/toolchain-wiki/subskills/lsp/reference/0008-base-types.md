#### Base Types


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#base-types


The protocol uses the following definitions for integers, unsigned integers, decimal numbers, objects and arrays:


    /**
     * Defines an integer number in the range of -2^31 to 2^31 - 1.
     */
    export type integer = number;
    


    /**
     * Defines an unsigned integer number in the range of 0 to 2^31 - 1.
     */
    export type uinteger = number;
    


    /**
     * Defines a decimal number. Since decimal numbers are very
     * rare in the language server specification we denote the
     * exact range with every decimal using the mathematics
     * interval notation (e.g. [0, 1] denotes all decimals d with
     * 0 <= d <= 1.
     */
    export type decimal = number;
    


    /**
     * The LSP any type
     *
     * @since 3.17.0
     */
    export type LSPAny = LSPObject | LSPArray | string | integer | uinteger |
    	decimal | boolean | null;
    


    /**
     * LSP object definition.
     *
     * @since 3.17.0
     */
    export type LSPObject = { [key: string]: LSPAny };
    


    /**
     * LSP arrays.
     *
     * @since 3.17.0
     */
    export type LSPArray = LSPAny[];