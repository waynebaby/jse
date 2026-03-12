/// Parser converts JSON values into AST nodes.

/// Parser for converting JSON to AST nodes
pub struct Parser {
  env : Env
}

/// Create a new parser with the given environment
pub fn parser_new(env : Env) -> Parser {
  { env }
}

/// Parse a JSON value into an AST node
pub fn Parser::parse(self : Parser, value : JseValue) -> Result[AstNodeEnum, AstError] {
  match value {
    JseValue::NullValue | JseValue::BoolValue(_) | JseValue::NumberValue(_) => {
      Ok(AstNodeEnum::Literal(literal_new(value, self.env)))
    }

    JseValue::StringValue(s) => {
      // Strings starting with $ are symbols (but not $$ escaped strings)
      if s.has_prefix("$") && !s.has_prefix("$$") && s != "$*" {
        Ok(AstNodeEnum::Symbol(symbol_new(s, self.env)))
      } else {
        Ok(AstNodeEnum::Literal(literal_new(value, self.env)))
      }
    }

    JseValue::ArrayValue(arr) => {
      Parser::parse_array(self, arr)
    }

    JseValue::ObjectValue(obj) => {
      Parser::parse_object(self, obj)
    }
  }
}

fn Parser::parse_array(self : Parser, arr : Array[JseValue]) -> Result[AstNodeEnum, AstError] {
  let elements = Array::new()
  let mut elements2 = elements
  for elem in arr {
    match Parser::parse(self, elem) {
      Ok(node) => elements2 = array_push(elements2, node)
      Err(e) => return Err(e)
    }
  }
  Ok(AstNodeEnum::Array(array_new(elements2, self.env)))
}

fn Parser::parse_object(self : Parser, obj : Map[String, JseValue]) -> Result[AstNodeEnum, AstError] {
  // Check for object expression (single key starting with $)
  match get_s_expr_key(obj) {
    Some(sym) => {
      let value = match obj.get(sym) {
        Some(v) => v
        None => JseValue::NullValue
      }

      // Extract metadata (non-operator keys)
      let metadata = Map::new()
      let mut metadata2 = metadata
      let keys = obj.keys()
      for key in keys {
        if key != sym {
          match obj.get(key) {
            Some(v) => metadata2 = map_put(metadata2, key, v)
            None => ()
          }
        }
      }

      match Parser::parse(self, value) {
        Ok(node) => Ok(AstNodeEnum::ObjectExpression(object_expression_new(sym, node, metadata2, self.env)))
        Err(e) => Err(e)
      }
    }
    None => {
      // Regular object
      let dict = Map::new()
      let mut dict2 = dict
      let keys = obj.keys()
      for key in keys {
        match obj.get(key) {
          Some(v) => {
            match Parser::parse(self, v) {
              Ok(node) => dict2 = map_put(dict2, key, node)
              Err(e) => return Err(e)
            }
          }
          None => ()
        }
      }
      Ok(AstNodeEnum::Object(object_new(dict2, self.env)))
    }
  }
}

/// Get the S-expression key from an object
/// Returns Some(key) if object has a single key starting with $
/// (other keys are treated as metadata)
fn get_s_expr_key(obj : Map[String, JseValue]) -> String? {
  let keys = obj.keys()
  let keys_arr = keys.to_array()

  // Find the first key starting with $
  let mut found : String? = None
  for key in keys_arr {
    if key.has_prefix("$") && !key.has_prefix("$$") {
      match found {
        None => found = Some(key)
        Some(_) => return None  // Multiple $ keys - not an expression
      }
    }
  }

  found
}
