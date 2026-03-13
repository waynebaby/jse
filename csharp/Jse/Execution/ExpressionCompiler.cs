using System.Collections.Concurrent;
using System.Linq.Expressions;
using Jse.Ast;
using Jse.Runtime;

namespace Jse.Execution;

public sealed class ExpressionCompiler
{
    private readonly ConcurrentDictionary<string, Func<object?>> _cache = new(StringComparer.Ordinal);

    public Func<object?> Compile(JseNode ast, Environment env)
    {
        var key = BuildCacheKey(ast);
        return _cache.GetOrAdd(key, _ => BuildDelegate(ast, env));
    }

    private static Func<object?> BuildDelegate(JseNode ast, Environment env)
    {
        var body = BuildExpression(ast, env);
        var lambda = Expression.Lambda<Func<object?>>(Expression.Convert(body, typeof(object)));
        return lambda.Compile();
    }

    private static Expression BuildExpression(JseNode node, Environment env)
    {
        return node switch
        {
            JseLiteral literal => Expression.Constant(literal.Value, typeof(object)),
            JseSymbol symbol => Expression.Constant($"${symbol.Name}", typeof(object)),
            JseCall call => BuildCall(call, env),
            _ => throw new InvalidOperationException($"Unsupported AST node: {node.GetType().Name}")
        };
    }

    private static Expression BuildCall(JseCall call, Environment env)
    {
        if (string.Equals(call.Operator, "quote", StringComparison.Ordinal))
        {
            if (call.Args.Count != 1)
            {
                throw new InvalidOperationException("$quote requires exactly 1 argument.");
            }

            var quoted = QuoteNode(call.Args[0]);
            return Expression.Constant(quoted, typeof(object));
        }

        var op = env.Operators.Resolve(call.Operator);
        var args = call.Args
            .Select(arg => Expression.Convert(BuildExpression(arg, env), typeof(object)))
            .ToArray();

        var arrayExpr = Expression.NewArrayInit(typeof(object), args);
        return Expression.Invoke(Expression.Constant(op), arrayExpr);
    }

    private static object? QuoteNode(JseNode node)
    {
        return node switch
        {
            JseLiteral literal => literal.Value,
            JseSymbol symbol => $"${symbol.Name}",
            JseCall call => new object?[]
            {
                $"${call.Operator}"
            }.Concat(call.Args.Select(QuoteNode)).ToList(),
            _ => throw new InvalidOperationException($"Unsupported quoted AST node: {node.GetType().Name}")
        };
    }

    private static string BuildCacheKey(JseNode ast) => SerializeNode(ast);

    private static string SerializeNode(JseNode node)
    {
        return node switch
        {
            JseLiteral literal => $"lit:{SerializeValue(literal.Value)}",
            JseSymbol symbol => $"sym:{symbol.Name}",
            JseCall call => $"call:{call.Operator}({string.Join(',', call.Args.Select(SerializeNode))})",
            _ => throw new InvalidOperationException($"Unsupported AST node: {node.GetType().Name}")
        };
    }

    private static string SerializeValue(object? value)
    {
        return value switch
        {
            null => "null",
            string s => $"\"{s}\"",
            bool b => b ? "true" : "false",
            IEnumerable<object?> list => $"[{string.Join(',', list.Select(SerializeValue))}]",
            IDictionary<string, object?> dict => $"{{{string.Join(',', dict.OrderBy(k => k.Key).Select(kv => $"{kv.Key}:{SerializeValue(kv.Value)}"))}}}",
            _ => value.ToString() ?? string.Empty
        };
    }
}
