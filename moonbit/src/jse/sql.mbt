/// SQL extension functors for JSE.
///
/// Demonstrates local scope: ONLY exports $query globally.
/// Local operators ($pattern, $and, $*) are ONLY available inside $query's local scope.

/// Query fields constant
const QUERY_FIELDS : String = "subject, predicate, object, meta"

/// SQL functors map - ONLY exports $query
pub fn sql_functors() -> Map[String, Functor] {
  let m = Map::new()
  map_put(m, "$query", query)
}

/// Local operators for $query scope only
fn local_sql_functors() -> Map[String, Functor] {
  let m = Map::new()
  let mut m2 = map_put(m, "$pattern", pattern)
  m2 = map_put(m2, "$and", sql_and)
  m2 = map_put(m2, "$*", wildcard)
  m2
}

/// SQL-specific AND: joins conditions with " and ".
/// LOCAL-ONLY for $query, different from logical $and in utils.mbt.
fn sql_and(env : Env, args : Array[JseValue]) -> Result[JseValue, String] {
  let tokens = Array::new()
  let mut tokens2 = tokens
  for arg in args {
    match eval_json(env, arg) {
      Ok(result) => {
        tokens2 = array_push(tokens2, result)
      }
      Err(e) => { return Err(e) }
    }
  }

  // Convert all tokens to strings and join
  let strings = Array::new()
  let mut strings2 = strings
  for token in tokens2 {
    match token {
      JseValue::StringValue(s) => strings2 = array_push(strings2, s)
      _ => return Err("$and arguments must evaluate to strings")
    }
  }

  let joined = strings2.join(" and ")
  Ok(JseValue::StringValue(joined))
}

/// Wildcard helper for local scope
fn wildcard(_env : Env, _args : Array[JseValue]) -> Result[JseValue, String] {
  Ok(JseValue::StringValue("*"))
}

/// $pattern functor - Generate SQL WHERE condition for a triple pattern.
/// This is the LOCAL version used inside $query.
fn pattern(_env : Env, args : Array[JseValue]) -> Result[JseValue, String] {
  if args.length() < 3 {
    return Err("$pattern requires (subject, predicate, object)")
  }

  let subject = match args[0] {
    JseValue::StringValue(s) => s
    _ => return Err("$pattern requires string arguments")
  }
  let predicate = match args[1] {
    JseValue::StringValue(s) => s
    _ => return Err("$pattern requires string arguments")
  }
  let object = match args[2] {
    JseValue::StringValue(s) => s
    _ => return Err("$pattern requires string arguments")
  }

  let triple = pattern_to_triple(subject, predicate, object)
  match triple_to_sql_condition(triple) {
    Ok(cond) => {
      Ok(JseValue::StringValue(cond))
    }
    Err(e) => Err(e)
  }
}

/// Convert AstError to String
fn ast_error_to_string(err : AstError) -> String {
  match err {
    AstError::SymbolNotFound(s) => "Symbol not found: " + s
    AstError::TypeError(s) => "Type error: " + s
    AstError::ArityError(s) => "Arity error: " + s
    AstError::EvalError(s) => "Eval error: " + s
  }
}

/// Build SQL SELECT statement
fn build_sql(where_str : String) -> String {
  "select " + QUERY_FIELDS + " \nfrom statement \nwhere \n    " + where_str + " \noffset 0\nlimit 100 \n"
}

/// $query functor - Generate SQL for multi-pattern query with LOCAL environment.
/// Form: {$query: condition}
/// where condition is an AST expression with local operators ($pattern, $and, $*)
fn query(env : Env, args : Array[JseValue]) -> Result[JseValue, String] {
  if args.length() < 1 {
    return Err("$query expects a condition expression")
  }

  // Create LOCAL environment with parent
  let local_env = new_with_parent(env)

  // Load LOCAL operators into local scope
  load(local_env, local_sql_functors())

  // Parse and evaluate in LOCAL environment
  let parser = parser_new(local_env)
  match Parser::parse(parser, args[0]) {
    Ok(ast_node) => {
      match ast_node {
        AstNodeEnum::Quote(quote_node) => {
          // $quote returns its content unevaluated
          // We need to evaluate it in the local environment
          let quoted_value = quote_to_json(quote_node)
          match eval_json(local_env, quoted_value) {
            Ok(result) => {
              match result {
                JseValue::StringValue(where_str) => {
                  let sql = build_sql(where_str)
                  Ok(JseValue::StringValue(sql))
                }
                _ => Err("query condition must evaluate to string")
              }
            }
            Err(e) => Err(e)
          }
        }
        _ => {
          // Apply the ast_node in local environment
          match ast_node_enum_apply(ast_node, local_env) {
            Ok(where_val) => {
              match where_val {
                JseValue::StringValue(where_str) => {
                  let sql = build_sql(where_str)
                  Ok(JseValue::StringValue(sql))
                }
                _ => Err("query condition must evaluate to string")
              }
            }
            Err(e) => Err(ast_error_to_string(e))
          }
        }
      }
    }
    Err(e) => Err(ast_error_to_string(e))
  }
}

/// Convert pattern arguments to triple
fn pattern_to_triple(subject : String, predicate : String, object : String) -> Array[String] {
  if subject == "$*" && object == "$*" {
    let arr = Array::new()
    arr.push(predicate)
    arr
  } else if subject == "*" && object == "*" {
    let arr = Array::new()
    arr.push(predicate)
    arr
  } else {
    let arr = Array::new()
    arr.push(subject)
    arr.push(predicate)
    arr.push(object)
    arr
  }
}

/// Build SQL condition from triple
fn triple_to_sql_condition(triple : Array[String]) -> Result[String, String] {
  let doc = Map::new()
  let mut doc2 = doc
  let arr = Array::new()
  let mut arr2 = arr
  for s in triple {
    arr2 = array_push(arr2, JseValue::StringValue(s))
  }
  doc2 = map_put(doc2, "triple", JseValue::ArrayValue(arr2))

  // Convert to JSON string
  let json_str = match json_to_string(JseValue::ObjectValue(doc2)) {
    Ok(s) => s
    Err(e) => return Err(e)
  }

  // Escape single quotes by replacing ' with ''
  let escaped = json_str.replace(old = "'", new = "''")
  Ok("meta @> '" + escaped + "'")
}

/// Simple JSON to string conversion
fn json_to_string(value : JseValue) -> Result[String, String] {
  match value {
    JseValue::NullValue => Ok("null")
    JseValue::BoolValue(true) => Ok("true")
    JseValue::BoolValue(false) => Ok("false")
    JseValue::NumberValue(n) => Ok(n.to_string())
    JseValue::StringValue(s) => Ok("\"" + s + "\"")
    JseValue::ArrayValue(arr) => {
      let mut result = "["
      let mut first = true
      for elem in arr {
        if !first {
          result = result + ","
        }
        first = false
        match json_to_string(elem) {
          Ok(s) => result = result + s
          Err(e) => return Err(e)
        }
      }
      result = result + "]"
      Ok(result)
    }
    JseValue::ObjectValue(obj) => {
      let mut result = "{"
      let mut first = true
      let keys = obj.keys()
      for key in keys {
        if !first {
          result = result + ","
        }
        first = false
        match obj.get(key) {
          Some(v) => {
            match json_to_string(v) {
              Ok(s) => result = result + "\"" + key + "\":" + s
              Err(e) => return Err(e)
            }
          }
          None => ()
        }
      }
      result = result + "}"
      Ok(result)
    }
  }
}
