using System.Collections.ObjectModel;

namespace Jse.Runtime;

public sealed class OperatorRegistry
{
    private readonly Dictionary<string, Func<object?[], object?>> _operators = new(StringComparer.Ordinal);

    public OperatorRegistry Register(string name, Func<object?[], object?> implementation)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(name);
        ArgumentNullException.ThrowIfNull(implementation);

        _operators[name] = implementation;
        return this;
    }

    public Func<object?[], object?> Resolve(string name)
    {
        if (!_operators.TryGetValue(name, out var op))
        {
            throw new InvalidOperationException($"Operator '{name}' is not registered.");
        }

        return op;
    }

    public IReadOnlyDictionary<string, Func<object?[], object?>> Snapshot() =>
        new ReadOnlyDictionary<string, Func<object?[], object?>>(_operators);

    public static OperatorRegistry CreateDefault()
    {
        var registry = new OperatorRegistry();

        registry.Register("add", args => CoerceNumber(args[0]) + CoerceNumber(args[1]));
        registry.Register("eq", args => Equals(args[0], args[1]));
        registry.Register("and", args => CoerceBool(args[0]) && CoerceBool(args[1]));
        registry.Register("or", args => CoerceBool(args[0]) || CoerceBool(args[1]));
        registry.Register("cond", args => CoerceBool(args[0]) ? args[1] : args[2]);

        return registry;
    }

    private static long CoerceNumber(object? value) => value switch
    {
        int i => i,
        long l => l,
        short s => s,
        byte b => b,
        double d => checked((long)d),
        float f => checked((long)f),
        decimal m => checked((long)m),
        _ => throw new InvalidCastException($"Cannot coerce '{value}' to number.")
    };

    private static bool CoerceBool(object? value) => value switch
    {
        bool b => b,
        _ => throw new InvalidCastException($"Cannot coerce '{value}' to bool.")
    };
}
