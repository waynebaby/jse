package jse

import (
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
)

// Value is the generic JSON value type used by the engine.
type Value = interface{}

// Env defines the environment for JSE execution.
// Implement this interface to provide custom symbol resolution.
type Env interface {
	// Resolve returns (value, true) if the symbol is bound, or (nil, false) otherwise.
	Resolve(symbol string) (Value, bool)
}

// ExpressionEnv is a minimal environment that does not resolve any symbols.
type ExpressionEnv struct{}

func (ExpressionEnv) Resolve(string) (Value, bool) { return nil, false }

// Engine executes JSE expressions.
type Engine struct {
	env Env
}

// NewEngine constructs a new Engine with the given environment.
func NewEngine(env Env) *Engine {
	return &Engine{env: env}
}

// Execute evaluates a JSE expression.
func (e *Engine) Execute(expr Value) (Value, error) {
	switch v := expr.(type) {
	case nil, bool, float64, float32, int, int32, int64, uint, uint32, uint64:
		return expr, nil
	case string:
		return unescapeSymbol(v), nil
	case []interface{}:
		if len(v) == 0 {
			return v, nil
		}
		if sym, ok := v[0].(string); ok && isSymbol(sym) {
			return e.evalSExpr(sym, v[1:])
		}
		out := make([]interface{}, len(v))
		for i, el := range v {
			ev, err := e.Execute(el)
			if err != nil {
				return nil, err
			}
			out[i] = ev
		}
		return out, nil
	case map[string]interface{}:
		if sym, ok := getSExprKey(v); ok {
			tail, ok := v[sym]
			if !ok {
				tail = nil
			}
			var args []interface{}
			if sym == "$expr" {
				args = []interface{}{tail}
			} else if arr, ok := tail.([]interface{}); ok {
				args = arr
			} else {
				args = []interface{}{tail}
			}
			return e.evalSExpr(sym, args)
		}
		result := make(map[string]interface{}, len(v))
		for k, val := range v {
			key := unescapeSymbol(k)
			ev, err := e.Execute(val)
			if err != nil {
				return nil, err
			}
			result[key] = ev
		}
		return result, nil
	default:
		// Unknown concrete type: pass through as-is.
		return expr, nil
	}
}

func isSymbol(s string) bool {
	return strings.HasPrefix(s, "$") && !strings.HasPrefix(s, "$$")
}

func unescapeSymbol(s string) string {
	if strings.HasPrefix(s, "$$") {
		return s[1:]
	}
	return s
}

func getSExprKey(obj map[string]interface{}) (string, bool) {
	var found string
	for k := range obj {
		if strings.HasPrefix(k, "$") && !strings.HasPrefix(k, "$$") {
			if found != "" {
				return "", false
			}
			found = k
		}
	}
	if found == "" {
		return "", false
	}
	return found, true
}

func (e *Engine) evalSExpr(symbol string, args []interface{}) (Value, error) {
	// $quote: do not evaluate the argument
	if symbol == "$quote" {
		if len(args) == 0 {
			return nil, nil
		}
		return args[0], nil
	}

	evaluated := make([]interface{}, len(args))
	for i, a := range args {
		ev, err := e.Execute(a)
		if err != nil {
			return nil, err
		}
		evaluated[i] = ev
	}

	switch symbol {
	case "$and":
		return evalAnd(evaluated), nil
	case "$or":
		return evalOr(evaluated), nil
	case "$not":
		return evalNot(evaluated), nil
	case "$expr":
		if len(evaluated) == 0 {
			return nil, nil
		}
		return evaluated[0], nil
	case "$pattern":
		return evalPattern(evaluated)
	case "$query":
		return evalQuery(evaluated)
	default:
		if v, ok := e.env.Resolve(symbol); ok {
			return v, nil
		}
		return nil, fmt.Errorf("unknown symbol: %s", symbol)
	}
}

func evalAnd(values []interface{}) bool {
	for _, v := range values {
		if !toBool(v) {
			return false
		}
	}
	return true
}

func evalOr(values []interface{}) bool {
	for _, v := range values {
		if toBool(v) {
			return true
		}
	}
	return false
}

func evalNot(values []interface{}) bool {
	if len(values) == 0 {
		return true
	}
	return !toBool(values[0])
}

func toBool(v interface{}) bool {
	switch b := v.(type) {
	case bool:
		return b
	case nil:
		return false
	default:
		return true
	}
}

// --- SQL helpers mirroring other language implementations ---

// QueryFields is the SELECT field list used by $pattern / $query.
const QueryFields = "subject, predicate, object, meta"

// PatternToTriple converts $pattern arguments into a triple slice.
//
//   ["$pattern", "$*", "author of", "$*"] -> ["author of"]
//   ["$pattern", "Liu Xin", "author of", "$*"] -> ["Liu Xin", "author of", "$*"]
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

func evalPattern(evaluated []interface{}) (string, error) {
	if len(evaluated) < 3 {
		return "", fmt.Errorf("$pattern requires (subject, predicate, object)")
	}
	subj, ok1 := evaluated[0].(string)
	pred, ok2 := evaluated[1].(string)
	obj, ok3 := evaluated[2].(string)
	if !ok1 || !ok2 || !ok3 {
		return "", fmt.Errorf("$pattern requires string arguments")
	}
	triple := PatternToTriple(subj, pred, obj)
	cond, err := TripleToSQLCondition(triple)
	if err != nil {
		return "", err
	}
	sql := fmt.Sprintf(
		"select \n    subject, predicate, object, meta \nfrom statement as s \nwhere %s \noffset 0\nlimit 100 \n",
		cond,
	)
	return sql, nil
}

func evalQuery(evaluated []interface{}) (string, error) {
	if len(evaluated) < 2 {
		return "", fmt.Errorf("$query expects [op, patterns array]")
	}
	list, ok := evaluated[1].([]interface{})
	if !ok {
		return "", fmt.Errorf("$query expects [op, patterns array]")
	}
	re, err := regexp.Compile(`(?is)where\s+(.+?)\s+offset`)
	if err != nil {
		return "", err
	}
	var conditions []string
	for _, item := range list {
		sql, ok := item.(string)
		if !ok {
			return "", fmt.Errorf("pattern must evaluate to SQL string")
		}
		m := re.FindStringSubmatch(sql)
		if len(m) >= 2 {
			conditions = append(conditions, fmt.Sprintf("(%s)", strings.TrimSpace(m[1])))
		} else {
			conditions = append(conditions, sql)
		}
	}
	where := strings.Join(conditions, " and \n    ")
	sql := fmt.Sprintf(
		"select %s \nfrom statement \nwhere \n    %s \noffset 0\nlimit 100 \n",
		QueryFields,
		where,
	)
	return sql, nil
}

