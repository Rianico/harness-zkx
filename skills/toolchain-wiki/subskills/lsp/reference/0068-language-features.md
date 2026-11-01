### Language Features


**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#language-features


Language Features provide the actual smarts in the language server protocol. They are usually executed on a [text document, position] tuple. The main language feature categories are:


  * code comprehension features like Hover or Goto Definition.
  * coding features like diagnostics, code complete or code actions.


The language features should be computed on the [synchronized state](#textDocument_synchronization) of the document.