/// Logic tests for JSE engine (internal tests)

fn make_array3(a : JseValue, b : JseValue, c : JseValue) -> Array[JseValue] {
  let arr = Array::new()
  let mut arr2 = array_push(arr, a)
  arr2 = array_push(arr2, b)
  array_push(arr2, c)
}

fn make_array2(a : JseValue, b : JseValue) -> Array[JseValue] {
  let arr = Array::new()
  let arr2 = array_push(arr, a)
  array_push(arr2, b)
}

test "and basic - all true" {
  let engine = with_default_env()
  let expr = jse_array(make_array3(
    jse_string("$and"),
    jse_bool(true),
    jse_bool(true)
  ))
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

test "and basic - with false" {
  let engine = with_default_env()
  let expr = jse_array(make_array3(
    jse_string("$and"),
    jse_bool(true),
    jse_bool(false)
  ))
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

test "or basic - with true" {
  let engine = with_default_env()
  let expr = jse_array(make_array3(
    jse_string("$or"),
    jse_bool(false),
    jse_bool(true)
  ))
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

test "or basic - all false" {
  let engine = with_default_env()
  let expr = jse_array(make_array3(
    jse_string("$or"),
    jse_bool(false),
    jse_bool(false)
  ))
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

test "not basic - true to false" {
  let engine = with_default_env()
  let expr = jse_array(make_array2(
    jse_string("$not"),
    jse_bool(true)
  ))
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

test "not basic - false to true" {
  let engine = with_default_env()
  let expr = jse_array(make_array2(
    jse_string("$not"),
    jse_bool(false)
  ))
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

test "eq basic - equal" {
  let engine = with_default_env()
  let expr = jse_array(make_array3(
    jse_string("$eq"),
    jse_number(1),
    jse_number(1)
  ))
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

test "eq basic - not equal" {
  let engine = with_default_env()
  let expr = jse_array(make_array3(
    jse_string("$eq"),
    jse_number(1),
    jse_number(2)
  ))
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

test "nested logic - or with and" {
  let engine = with_default_env()
  // ["$or", ["$and", true, true], false]
  let inner_and = jse_array(make_array3(
    jse_string("$and"),
    jse_bool(true),
    jse_bool(true)
  ))
  let expr = jse_array(make_array3(
    jse_string("$or"),
    inner_and,
    jse_bool(false)
  ))
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
