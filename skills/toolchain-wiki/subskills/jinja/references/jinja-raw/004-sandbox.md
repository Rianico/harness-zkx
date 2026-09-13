# Sandbox

The Jinja sandbox can be used to render untrusted templates. Access to attributes, method calls, operators, mutating data structures, and string formatting can be intercepted and prohibited.

``` pycon
>>> from jinja2.sandbox import SandboxedEnvironment
>>> env = SandboxedEnvironment()
>>> func = lambda: "Hello, Sandbox!"
>>> env.from_string("{{ func() }}").render(func=func)
'Hello, Sandbox!'
>>> env.from_string("{{ func.__code__.co_code }}").render(func=func)
Traceback (most recent call last):
  ...
SecurityError: access to attribute '__code__' of 'function' object is unsafe.
```

A sandboxed environment can be useful, for example, to allow users of an internal reporting system to create custom emails. You would document what data is available in the templates, then the user would write a template using that information. Your code would generate the report data and pass it to the user’s sandboxed template to render.

## Security Considerations

The sandbox alone is not a solution for perfect security. Keep these things in mind when using the sandbox.

Templates can still raise errors when compiled or rendered. Your code should attempt to catch errors instead of crashing.

It is possible to construct a relatively small template that renders to a very large amount of output, which could correspond to a high use of CPU or memory. You should run your application with limits on resources such as CPU and memory to mitigate this.

Jinja only renders text, it does not understand, for example, JavaScript code. Depending on how the rendered template will be used, you may need to do other postprocessing to restrict the output.

Pass only the data that is relevant to the template. Avoid passing global data, or objects with methods that have side effects. By default the sandbox prevents private and internal attribute access. You can override `is_safe_attribute()` to further restrict attributes access. Decorate methods with `unsafe()` to prevent calling them from templates when passing objects as data. Use `ImmutableSandboxedEnvironment` to prevent modifying lists and dictionaries.

## API

`classjinja2.sandbox.SandboxedEnvironment([options])`

The sandboxed environment. It works like the regular environment but tells the compiler to generate sandboxed code. Additionally subclasses of this environment may override the methods that tell the runtime what attributes or functions are safe to access.

If the template tries to access insecure code a `SecurityError` is raised. However also other exceptions may occur during the rendering so the caller has to ensure that all exceptions are caught.

Parameters:
- **args** (Any)

- **kwargs** (Any)

`default_binop_table:Dict[str,Callable[[Any,Any],Any]]={'%':<built-infunctionmod>,'*':<built-infunctionmul>,'**':<built-infunctionpow>,'+':<built-infunctionadd>,'-':<built-infunctionsub>,'/':<built-infunctiontruediv>,'//':<built-infunctionfloordiv>}`

default callback table for the binary operators. A copy of this is available on each instance of a sandboxed environment as `binop_table`

`default_unop_table:Dict[str,Callable[[Any],Any]]={'+':<built-infunctionpos>,'-':<built-infunctionneg>}`

default callback table for the unary operators. A copy of this is available on each instance of a sandboxed environment as `unop_table`

`intercepted_binops:FrozenSet[str]=frozenset({})`

a set of binary operators that should be intercepted. Each operator that is added to this set (empty by default) is delegated to the `call_binop()` method that will perform the operator. The default operator callback is specified by `binop_table`.

The following binary operators are interceptable: `//`, `%`, `+`, `*`, `-`, `/`, and `**`

The default operation form the operator table corresponds to the builtin function. Intercepted calls are always slower than the native operator call, so make sure only to intercept the ones you are interested in.

Changelog

Added in version 2.6.

`intercepted_unops:FrozenSet[str]=frozenset({})`

a set of unary operators that should be intercepted. Each operator that is added to this set (empty by default) is delegated to the `call_unop()` method that will perform the operator. The default operator callback is specified by `unop_table`.

The following unary operators are interceptable: `+`, `-`

The default operation form the operator table corresponds to the builtin function. Intercepted calls are always slower than the native operator call, so make sure only to intercept the ones you are interested in.

Changelog

Added in version 2.6.

`is_safe_attribute(obj,attr,value)`

The sandboxed environment will call this method to check if the attribute of an object is safe to access. Per default all attributes starting with an underscore are considered private as well as the special attributes of internal python objects as returned by the `is_internal_attribute()` function.

Parameters:
- **obj** (Any)

- **attr** (str)

- **value** (Any)

Return type:
bool

`is_safe_callable(obj)`

Check if an object is safely callable. By default callables are considered safe unless decorated with `unsafe()`.

This also recognizes the Django convention of setting `func.alters_data = True`.

Parameters:
**obj** (Any)

Return type:
bool

`call_binop(context,operator,left,right)`

For intercepted binary operator calls (`intercepted_binops()`) this function is executed instead of the builtin operator. This can be used to fine tune the behavior of certain operators.

Changelog

Added in version 2.6.

Parameters:
- **context** (Context)

- **operator** (str)

- **left** (Any)

- **right** (Any)

Return type:
Any

`call_unop(context,operator,arg)`

For intercepted unary operator calls (`intercepted_unops()`) this function is executed instead of the builtin operator. This can be used to fine tune the behavior of certain operators.

Changelog

Added in version 2.6.

Parameters:
- **context** (Context)

- **operator** (str)

- **arg** (Any)

Return type:
Any

`classjinja2.sandbox.ImmutableSandboxedEnvironment([options])`

Works exactly like the regular `SandboxedEnvironment` but does not permit modifications on the builtin mutable objects `list`, `set`, and `dict` by using the `modifies_known_mutable()` function.

Parameters:
- **args** (Any)

- **kwargs** (Any)

`exceptionjinja2.sandbox.SecurityError(message=None)`

Raised if a template tries to do something insecure if the sandbox is enabled.

Parameters:
**message** (str \| None)

Return type:
None

`jinja2.sandbox.unsafe(f)`

Marks a function or method as unsafe.

Parameters:
**f** (F)

Return type:
F

`jinja2.sandbox.is_internal_attribute(obj,attr)`

Test if the attribute given is an internal python attribute. For example this function returns `True` for the `func_code` attribute of python objects. This is useful if the environment method `is_safe_attribute()` is overridden.

    >>> from jinja2.sandbox import is_internal_attribute
    >>> is_internal_attribute(str, "mro")
    True
    >>> is_internal_attribute(str, "upper")
    False

Parameters:
- **obj** (Any)

- **attr** (str)

Return type:
bool

`jinja2.sandbox.modifies_known_mutable(obj,attr)`

This function checks if an attribute on a builtin mutable object (list, dict, set or deque) or the corresponding ABCs would modify it if called.

    >>> modifies_known_mutable({}, "clear")
    True
    >>> modifies_known_mutable({}, "keys")
    False
    >>> modifies_known_mutable([], "append")
    True
    >>> modifies_known_mutable([], "index")
    False

If called with an unsupported object, `False` is returned.

    >>> modifies_known_mutable("foo", "upper")
    False

Parameters:
- **obj** (Any)

- **attr** (str)

Return type:
bool

## Operator Intercepting

For performance, Jinja outputs operators directly when compiling. This means it’s not possible to intercept operator behavior by overriding `SandboxEnvironment.call` by default, because operator special methods are handled by the Python interpreter, and might not correspond with exactly one method depending on the operator’s use.

The sandbox can instruct the compiler to output a function to intercept certain operators instead. Override `SandboxedEnvironment.intercepted_binops` and `SandboxedEnvironment.intercepted_unops` with the operator symbols you want to intercept. The compiler will replace the symbols with calls to `SandboxedEnvironment.call_binop()` and `SandboxedEnvironment.call_unop()` instead. The default implementation of those methods will use `SandboxedEnvironment.binop_table` and `SandboxedEnvironment.unop_table` to translate operator symbols into `operator` functions.

For example, the power (`**`) operator can be disabled:

``` python
from jinja2.sandbox import SandboxedEnvironment

class MyEnvironment(SandboxedEnvironment):
    intercepted_binops = frozenset(["**"])

    def call_binop(self, context, operator, left, right):
        if operator == "**":
            return self.undefined("The power (**) operator is unavailable.")

        return super().call_binop(self, context, operator, left, right)
```
