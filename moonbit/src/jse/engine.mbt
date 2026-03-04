/// Minimal JSON Structural Expression (JSE) engine in MoonBit.
///
/// Supported features:
/// - literals: Null / Bool / Number / String / Array / Object
/// - logical operators: $and / $or / $not
/// - $quote, $expr
/// - $pattern, $query (SQL generation, same shape as other runtimes)

fn is_symbol(s : String) -> Bool {
  s.has_prefix("$") && !s.has_prefix("$$")
}

fn get_s_expr_key(obj : Map[String, Json]) -> String? {
  let mut found : String? = None
  for entry in obj {
    let (k, _) = entry
    if is_symbol(k) {
      match found {
        Some(_) => return None
        None => found = Some(k)
      }
    }
  }
  found
}

/// Evaluate a JSE expression with no external environment.
pub fn eval(expr : Json) -> Json {
  match expr {
    Null | True | False | Number(_, ..) | String(_) => expr

    Array(arr) => {
      let out = Array::new()
      for v in arr {
        out.push(eval(v))
      }
      Json::array(out)
    }

    Object(obj) => {
      match get_s_expr_key(obj) {
        Some(sym) => {
          let tail = obj.get(sym).unwrap()
          let args = Array::new()
          match tail {
            Array(arr) => for v in arr { args.push(v) }
            _ => args.push(tail)
          }
          eval_s_expr(sym, args)
        }
        None => Json::object(obj)
      }
    }
  }
}

fn to_bool(v : Json) -> Bool {
  match v {
    True => true
    False | Null => false
    _ => true
  }
}

fn eval_s_expr(sym : String, args : Array[Json]) -> Json {
  if sym == "$quote" {
    match args.get(0) {
      Some(v) => v
      None => "".to_json()
    }
  } else {
    let evaled = Array::new()
    for a in args {
      evaled.push(eval(a))
    }

    match sym {
      "$and" => {
        let mut res = true
        for v in evaled {
          if !to_bool(v) {
            res = false
            break
          }
        }
        res.to_json()
      }

      "$or" => {
        let mut res = false
        for v in evaled {
          if to_bool(v) {
            res = true
            break
          }
        }
        res.to_json()
      }

      "$not" => {
        let b = match evaled.get(0) {
          Some(v) => to_bool(v)
          None => false
        }
        (!b).to_json()
      }

      "$expr" => {
        match evaled.get(0) {
          Some(String(cond)) => build_select(cond).to_json()
          Some(v) => v
          None => "".to_json()
        }
      }

      "$pattern" => {
        let cond = eval_pattern(evaled)
        cond.to_json()
      }

      "$query" => {
        let sql = eval_query(args)
        sql.to_json()
      }

      _ => "".to_json()
    }
  }
}

const QUERY_FIELDS : String = "subject, predicate, object, meta"

fn build_select(cond : String) -> String {
  "select \n    subject, predicate, object, meta \nfrom statement as s \nwhere \{cond} \noffset 0\nlimit 100 \n"
}

fn pattern_to_triple(subject : String, predicate : String, object : String) -> Array[String] {
  let triple = Array::new()
  if subject == "$*" && object == "$*" {
    triple.push(predicate)
  } else {
    triple.push(subject)
    triple.push(predicate)
    triple.push(object)
  }
  triple
}

fn triple_to_sql_condition(triple : Array[String]) -> String {
  let json = {
    "triple": triple.map(String::to_json),
  }
  let s = json.to_string()
  "meta @> '\{s}'"
}

fn eval_pattern(args : Array[Json]) -> String {
  let subject = match args.get(0) {
    Some(String(s)) => s
    _ => "$*"
  }
  let predicate = match args.get(1) {
    Some(String(s)) => s
    _ => ""
  }
  let object = match args.get(2) {
    Some(String(s)) => s
    _ => "$*"
  }
  let triple = pattern_to_triple(subject, predicate, object)
  triple_to_sql_condition(triple)
}

fn eval_query(args : Array[Json]) -> String {
  let patterns = match args.get(1) {
    Some(Array(arr)) => arr
    _ => Array::new()
  }
  let conds = Array::new()
  for p in patterns {
    match p {
      Array(arr) => {
        let cond = eval_pattern(arr)
        conds.push(cond)
      }
      _ => ()
    }
  }
  let where_clause = conds.join(" and \n    ")
  "select \{QUERY_FIELDS} \nfrom statement \nwhere \n    \{where_clause} \noffset 0\nlimit 100 \n"
}


