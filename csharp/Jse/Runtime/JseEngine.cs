using System.Text.Json;
using Jse.Execution;
using Jse.Parser;

namespace Jse.Runtime;

public sealed class JseEngine
{
    private readonly JseParser _parser;
    private readonly ExpressionCompiler _compiler;
    private readonly Environment _environment;

    public JseEngine()
        : this(OperatorRegistry.CreateDefault())
    {
    }

    public JseEngine(OperatorRegistry registry)
    {
        _parser = new JseParser();
        _compiler = new ExpressionCompiler();
        _environment = new Environment(registry);
    }

    public object? Execute(string json)
    {
        using var doc = JsonDocument.Parse(json);
        return Execute(doc.RootElement);
    }

    public object? Execute(JsonElement element)
    {
        var ast = _parser.Parse(element);
        var executable = _compiler.Compile(ast, _environment);
        return executable();
    }
}
