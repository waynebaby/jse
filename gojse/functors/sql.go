package functors

import (
	"encoding/json"
	"fmt"
	"strings"
)

// SQLFunctors contains SQL-related operators.
// NOTE: ONLY exports $query - the local operators ($pattern, $and, $*)
// are NOT globally available. They only exist within $query's local scope.
var SQLFunctors = map[string]Functor{
	"$query": query,
}

// QueryFields is the SELECT field list used by $query.
const QueryFields = "subject, predicate, object, meta"

// envHelper encapsulates environment operations needed by SQL functors.
type envHelper interface {
	EvalJSON(v interface{}) (interface{}, error)
	Load(functors map[string]Functor)
}

// parserHelper is the interface for parsing JSON into AST.
type parserHelper interface {
	Parse(v interface{}) (node interface{}, err error)
}

// nodeHelper is the interface for applying an AST node.
type nodeHelper interface {
	Apply(env interface{}) (interface{}, error)
}

// pattern generates SQL WHERE condition for a triple pattern.
// This is the LOCAL version used inside $query.
func pattern(env interface{}, args []interface{}) (interface{}, error) {
	if len(args) < 3 {
		return "", fmt.Errorf("$pattern requires (subject, predicate, object)")
	}
	subj, ok1 := args[0].(string)
	pred, ok2 := args[1].(string)
	obj, ok3 := args[2].(string)
	if !ok1 || !ok2 || !ok3 {
		return "", fmt.Errorf("$pattern requires string arguments")
	}
	triple := PatternToTriple(subj, pred, obj)
	cond, err := TripleToSQLCondition(triple)
	if err != nil {
		return "", err
	}
	// Return just the WHERE condition, not a full SELECT
	return cond, nil
}

// sqlAnd is SQL-specific AND: joins conditions with " and ".
// This is LOCAL-ONLY for $query, different from logical $and in utils.go.
func sqlAnd(env interface{}, args []interface{}) (interface{}, error) {
	envImpl, ok := env.(envHelper)
	if !ok {
		return "", fmt.Errorf("env does not implement EvalJSON")
	}

	var tokens []string
	for _, arg := range args {
		result, err := envImpl.EvalJSON(arg)
		if err != nil {
			return "", fmt.Errorf("failed to evaluate $and argument: %w", err)
		}
		sql, ok := result.(string)
		if !ok {
			return "", fmt.Errorf("$and arguments must evaluate to strings")
		}
		tokens = append(tokens, sql)
	}
	return strings.Join(tokens, " and "), nil
}

// wildcard is the wildcard helper for local scope.
func wildcard(env interface{}, args []interface{}) (interface{}, error) {
	return "*", nil
}

// localSQLFunctors returns local operators for $query scope only.
func localSQLFunctors() map[string]Functor {
	return map[string]Functor{
		"$pattern": pattern,
		"$and":     sqlAnd,
		"$*":       wildcard,
	}
}

// query generates SQL for multi-pattern query with LOCAL environment.
// Form: {"$query": condition}
// where condition is an AST expression with local operators ($pattern, $and, $*)
func query(env interface{}, args []interface{}) (interface{}, error) {
	if len(args) < 1 {
		return "", fmt.Errorf("$query expects a condition expression")
	}

	// Type assert to get the helper interfaces
	envHelper, ok := env.(envHelper)
	if !ok {
		return "", fmt.Errorf("env does not implement required interface")
	}

	// Create local evaluation context that has access to local functors
	localEnv := &localEvalContext{
		parent: envHelper,
		local:  localSQLFunctors(),
	}

	// Evaluate the condition in the local environment
	result, err := localEnv.EvalJSON(args[0])
	if err != nil {
		return "", fmt.Errorf("failed to evaluate query condition: %w", err)
	}

	whereStr, ok := result.(string)
	if !ok {
		return "", fmt.Errorf("query condition must evaluate to string, got %T", result)
	}

	sql := fmt.Sprintf(
		"select %s \nfrom statement \nwhere \n    %s \noffset 0\nlimit 100 \n",
		QueryFields,
		whereStr,
	)
	return sql, nil
}

// localEvalContext provides evaluation with local functors available.
// This simulates local scope by checking local functors first.
type localEvalContext struct {
	parent envHelper
	local  map[string]Functor
}

// EvalJSON evaluates JSON with local functors taking precedence.
func (c *localEvalContext) EvalJSON(v interface{}) (interface{}, error) {
	// Handle object expressions like {"$op": ...} or {"$quote": ...}
	if m, ok := v.(map[string]interface{}); ok && len(m) == 1 {
		for key, arg := range m {
			if key == "$quote" {
				// $quote returns its argument unevaluated
				// But we need to continue evaluating if the result is another expression
				return c.continueEval(arg)
			}
			if fn, hasLocal := c.local[key]; hasLocal {
				// Use local functor
				return c.applyFunctor(fn, arg)
			}
		}
	}

	// Handle arrays like ["$op", ...]
	if arr, ok := v.([]interface{}); ok && len(arr) > 0 {
		if key, ok := arr[0].(string); ok {
			if key == "$quote" && len(arr) > 1 {
				// $quote returns its argument unevaluated
				// But we need to continue evaluating if the result is another expression
				return c.continueEval(arr[1])
			}
			if fn, hasLocal := c.local[key]; hasLocal {
				// Use local functor with rest of array as args
				args := arr[1:]
				if len(args) == 1 {
					// Single argument - might be another expression
					return c.applyFunctor(fn, args[0])
				}
				return fn(c, args)
			}
		}
	}

	// Delegate to parent environment for everything else
	return c.parent.EvalJSON(v)
}

// continueEval continues evaluating the value until we get a non-expression result.
// This is needed after $quote to handle nested expressions.
func (c *localEvalContext) continueEval(v interface{}) (interface{}, error) {
	// If v is an expression, evaluate it and continue
	if m, ok := v.(map[string]interface{}); ok && len(m) == 1 {
		for key, arg := range m {
			if fn, hasLocal := c.local[key]; hasLocal {
				result, err := c.applyFunctor(fn, arg)
				if err != nil {
					return nil, err
				}
				// Continue evaluating if result is another expression
				return c.continueEval(result)
			}
		}
	}
	if arr, ok := v.([]interface{}); ok && len(arr) > 0 {
		if key, ok := arr[0].(string); ok {
			if fn, hasLocal := c.local[key]; hasLocal {
				args := arr[1:]
				var result interface{}
				var err error
				if len(args) == 1 {
					result, err = c.applyFunctor(fn, args[0])
				} else {
					result, err = fn(c, args)
				}
				if err != nil {
					return nil, err
				}
				// Continue evaluating if result is another expression
				return c.continueEval(result)
			}
		}
	}
	// Not an expression, return as-is
	return v, nil
}

// applyFunctor applies a functor with the given argument.
func (c *localEvalContext) applyFunctor(fn Functor, arg interface{}) (interface{}, error) {
	// Convert arg to args array form
	var args []interface{}
	if arr, ok := arg.([]interface{}); ok {
		args = arr
	} else {
		args = []interface{}{arg}
	}
	return fn(c, args)
}

// Load loads functors (for interface compatibility).
func (c *localEvalContext) Load(functors map[string]Functor) {
	// Merge into local functors, with local taking precedence
	for name, fn := range functors {
		if _, exists := c.local[name]; !exists {
			c.local[name] = fn
		}
	}
}

// PatternToTriple converts $pattern arguments into a triple slice.
func PatternToTriple(subject, predicate, object string) []string {
	if subject == "$*" && object == "$*" {
		return []string{predicate}
	}
	return []string{subject, predicate, object}
}

// TripleToSQLCondition builds a jsonb containment predicate.
func TripleToSQLCondition(triple []string) (string, error) {
	doc := map[string][]string{"triple": triple}
	data, err := json.Marshal(doc)
	if err != nil {
		return "", err
	}
	s := string(data)
	escaped := strings.ReplaceAll(s, "'", "''")
	return fmt.Sprintf("meta @> '%s'", escaped), nil
}
