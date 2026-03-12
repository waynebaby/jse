/// Basic tests for JSE engine (internal tests)

test "number expression" {
  let engine = with_env()
  let expr = jse_number(42)
  match Engine::execute(engine, expr) {
    Ok(v) => {
      match v {
        JseValue::NumberValue(n) => inspect(n, content="42")
        _ => abort("Expected NumberValue")
      }
    }
    Err(e) => abort(e)
  }
}

test "string expression" {
  let engine = with_env()
  let expr = jse_string("hello")
  match Engine::execute(engine, expr) {
    Ok(v) => {
      match v {
        JseValue::StringValue(s) => inspect(s, content="hello")
        _ => abort("Expected StringValue")
      }
    }
    Err(e) => abort(e)
  }
}

test "boolean expression true" {
  let engine = with_env()
  let expr = jse_bool(true)
  match Engine::execute(engine, expr) {
    Ok(v) => {
      match v {
        JseValue::BoolValue(b) => inspect(b, content="true")
        _ => abort("Expected BoolValue")
      }
    }
    Err(e) => abort(e)
  }
}

test "boolean expression false" {
  let engine = with_env()
  let expr = jse_bool(false)
  match Engine::execute(engine, expr) {
    Ok(v) => {
      match v {
        JseValue::BoolValue(b) => inspect(b, content="false")
        _ => abort("Expected BoolValue")
      }
    }
    Err(e) => abort(e)
  }
}

test "null expression" {
  let engine = with_env()
  let expr = jse_null()
  match Engine::execute(engine, expr) {
    Ok(v) => {
      match v {
        JseValue::NullValue => inspect("null", content="null")
        _ => abort("Expected NullValue")
      }
    }
    Err(e) => abort(e)
  }
}

test "array expression" {
  let engine = with_env()
  let arr = Array::new()
  let mut arr2 = array_push(arr, jse_number(1))
  arr2 = array_push(arr2, jse_number(2))
  arr2 = array_push(arr2, jse_number(3))
  let expr = jse_array(arr2)
  match Engine::execute(engine, expr) {
    Ok(v) => {
      match v {
        JseValue::ArrayValue(result) => inspect(result.length(), content="3")
        _ => abort("Expected ArrayValue")
      }
    }
    Err(e) => abort(e)
  }
}

test "object expression" {
  let engine = with_env()
  let obj = Map::new()
  let mut obj2 = map_put(obj, "a", jse_number(1))
  obj2 = map_put(obj2, "b", jse_string("x"))
  let expr = jse_object(obj2)
  match Engine::execute(engine, expr) {
    Ok(v) => {
      match v {
        JseValue::ObjectValue(result) => inspect(result.length(), content="2")
        _ => abort("Expected ObjectValue")
      }
    }
    Err(e) => abort(e)
  }
}
