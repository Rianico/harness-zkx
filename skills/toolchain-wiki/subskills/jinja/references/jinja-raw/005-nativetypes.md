# Native Python Types

The default `Environment` renders templates to strings. With `NativeEnvironment`, rendering a template produces a native Python type. This is useful if you are using Jinja outside the context of creating text files. For example, your code may have an intermediate step where users may use templates to define values that will then be passed to a traditional string environment.

## Examples

Adding two values results in an integer, not a string with a number:

    >>> env = NativeEnvironment()
    >>> t = env.from_string('{{ x + y }}')
    >>> result = t.render(x=4, y=2)
    >>> print(result)
    6
    >>> print(type(result))
    int

Rendering list syntax produces a list:

    >>> t = env.from_string('[{% for item in data %}{{ item + 1 }},{% endfor %}]')
    >>> result = t.render(data=range(5))
    >>> print(result)
    [1, 2, 3, 4, 5]
    >>> print(type(result))
    list

Rendering something that doesn’t look like a Python literal produces a string:

    >>> t = env.from_string('{{ x }} * {{ y }}')
    >>> result = t.render(x=4, y=2)
    >>> print(result)
    4 * 2
    >>> print(type(result))
    str

Rendering a Python object produces that object as long as it is the only node:

    >>> class Foo:
    ...     def __init__(self, value):
    ...         self.value = value
    ...
    >>> result = env.from_string('{{ x }}').render(x=Foo(15))
    >>> print(type(result).__name__)
    Foo
    >>> print(result.value)
    15

## Sandboxed Native Environment

You can combine `SandboxedEnvironment` and `NativeEnvironment` to get both behaviors.

``` python
class SandboxedNativeEnvironment(SandboxedEnvironment, NativeEnvironment):
    pass
```

## API

`classjinja2.nativetypes.NativeEnvironment([options])`

An environment that renders templates to native Python types.

Parameters:
- **block_start_string** (str)

- **block_end_string** (str)

- **variable_start_string** (str)

- **variable_end_string** (str)

- **comment_start_string** (str)

- **comment_end_string** (str)

- **line_statement_prefix** (str \| None)

- **line_comment_prefix** (str \| None)

- **trim_blocks** (bool)

- **lstrip_blocks** (bool)

- **newline_sequence** (te.Literal\['\n', '\r\n', '\r'\])

- **keep_trailing_newline** (bool)

- **extensions** (Sequence\[str \| Type\[Extension\]\])

- **optimized** (bool)

- **undefined** (Type\[Undefined\])

- **finalize** (Callable\[\[...\], Any\] \| None)

- **autoescape** (bool \| Callable\[\[str \| None\], bool\])

- **loader** (BaseLoader \| None)

- **cache_size** (int)

- **auto_reload** (bool)

- **bytecode_cache** (BytecodeCache \| None)

- **enable_async** (bool)

`classjinja2.nativetypes.NativeTemplate([options])`

Parameters:
- **source** (str \| Template)

- **block_start_string** (str)

- **block_end_string** (str)

- **variable_start_string** (str)

- **variable_end_string** (str)

- **comment_start_string** (str)

- **comment_end_string** (str)

- **line_statement_prefix** (str \| None)

- **line_comment_prefix** (str \| None)

- **trim_blocks** (bool)

- **lstrip_blocks** (bool)

- **newline_sequence** (te.Literal\['\n', '\r\n', '\r'\])

- **keep_trailing_newline** (bool)

- **extensions** (Sequence\[str \| Type\[Extension\]\])

- **optimized** (bool)

- **undefined** (Type\[Undefined\])

- **finalize** (Callable\[\[...\], Any\] \| None)

- **autoescape** (bool \| Callable\[\[str \| None\], bool\])

- **enable_async** (bool)

Return type:
Any

`render(*args,**kwargs)`

Render the template to produce a native Python type. If the result is a single node, its value is returned. Otherwise, the nodes are concatenated as strings. If the result can be parsed with `ast.literal_eval()`, the parsed value is returned. Otherwise, the string is returned.

Parameters:
- **args** (Any)

- **kwargs** (Any)

Return type:
Any
