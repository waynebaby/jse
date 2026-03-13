namespace Jse.Runtime;

public sealed class Environment
{
    public Environment(OperatorRegistry operators)
    {
        Operators = operators;
    }

    public OperatorRegistry Operators { get; }
}
