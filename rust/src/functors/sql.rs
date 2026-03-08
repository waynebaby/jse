//! SQL extension functors for JSE.
//!
//! Following Python's functors/sql.py pattern for demonstrating local scope.
//! The SQL module ONLY exports $query, which creates a local environment
//! with local operators ($pattern, $and, $*).

use std::rc::Rc;
use std::cell::RefCell;
use serde_json::Value;
use crate::env::{Env, Functor};
use crate::ast::AstError;
use crate::ast::Parser;

pub const QUERY_FIELDS: &str = "subject, predicate, object, meta";

/// Convert $pattern arguments to PostgreSQL jsonb containment triple.
pub fn pattern_to_triple(subject: &str, predicate: &str, object: &str) -> Vec<String> {
    if subject == "*" && object == "*" {
        return vec![predicate.to_string()];
    }
    vec![
        subject.to_string(),
        predicate.to_string(),
        object.to_string(),
    ]
}

/// Build SQL WHERE clause for a triple pattern.
pub fn triple_to_sql_condition(triple: &[String]) -> String {
    let json = serde_json::json!({ "triple": triple });
    let s = json.to_string();
    let escaped = s.replace('\'', "''");
    format!("meta @> '{escaped}'")
}

/// Generate SQL WHERE condition for a triple pattern.
/// This is the LOCAL version used inside $query, which expands $* to "*".
pub fn pattern(env: &Rc<RefCell<Env>>, args: &[Value]) -> Result<Value, AstError> {
    if args.len() < 3 {
        return Err(AstError::ArityError("$pattern requires (subject, predicate, object)".to_string()));
    }

    let subj = args[0].as_str()
        .ok_or_else(|| AstError::TypeError("$pattern requires string arguments".to_string()))?;
    let pred = args[1].as_str()
        .ok_or_else(|| AstError::TypeError("$pattern requires string arguments".to_string()))?;
    let obj = args[2].as_str()
        .ok_or_else(|| AstError::TypeError("$pattern requires string arguments".to_string()))?;

    // For query's local environment, expand $* to "*" for the local scope
    let triple = pattern_to_triple(subj, pred, obj);
    let cond = triple_to_sql_condition(&triple);

    // Return just the WHERE condition, not a full SELECT
    Ok(Value::String(cond))
}

/// SQL-specific AND: joins conditions with " and ".
/// This is LOCAL-ONLY for $query, different from logical _and in utils.rs.
fn and(env: &Rc<RefCell<Env>>, args: &[Value]) -> Result<Value, AstError> {
    let mut tokens = Vec::new();
    for arg in args {
        // Parse and evaluate each argument as an expression
        let parser = Parser::new(Rc::clone(env));
        let ast = parser.parse(arg)?;
        let result = ast.apply(env)?;
        let sql = result.as_str()
            .ok_or_else(|| AstError::TypeError("$and arguments must evaluate to strings".to_string()))?;
        tokens.push(sql.to_string());
    }
    Ok(Value::String(tokens.join(" and ")))
}

/// Wildcard helper for local scope.
fn wildcard(_env: &Rc<RefCell<Env>>, _args: &[Value]) -> Result<Value, AstError> {
    Ok(Value::String("*".to_string()))
}

/// Local operators for $query scope only.
fn local_sql_functors() -> std::collections::HashMap<&'static str, Functor> {
    let mut m = std::collections::HashMap::new();
    m.insert("$pattern", pattern as Functor);
    m.insert("$and", and as Functor);
    m.insert("$*", wildcard as Functor);
    m
}

/// Generate SQL for multi-pattern query with LOCAL environment.
/// Form: [$query, condition]
/// where condition is an AST expression with local operators ($pattern, $and, $*)
pub fn query(env: &Rc<RefCell<Env>>, args: &[Value]) -> Result<Value, AstError> {
    if args.len() < 1 {
        return Err(AstError::ArityError("$query expects a condition expression".to_string()));
    }

    // Create LOCAL environment with parent
    let local = Rc::new(RefCell::new(Env::new_with_parent(Some(Rc::clone(env)))));

    // Load LOCAL operators into local scope
    local.borrow_mut().load(&local_sql_functors());

    // Create parser with LOCAL environment
    let parser = Parser::new(Rc::clone(&local));

    // Parse and evaluate in LOCAL environment
    let ast = parser.parse(&args[0])?;
    let where_clause = ast.apply(&local)?;

    // Extract the string value from the result
    let where_str = where_clause.as_str()
        .ok_or_else(|| AstError::TypeError("Query condition must evaluate to string".to_string()))?;

    // Generate SQL
    let sql = format!(
        "select {} \nfrom statement \nwhere \n    {} \noffset 0\nlimit 100 \n",
        QUERY_FIELDS,
        where_str
    );

    Ok(Value::String(sql))
}

/// SQL module functors - ONLY exports $query.
/// The local operators ($pattern, $and, $*) are NOT globally available.
/// They only exist within the local scope created by $query.
pub fn sql_functors() -> std::collections::HashMap<&'static str, Functor> {
    let mut m = std::collections::HashMap::new();
    m.insert("$query", query as Functor);
    m
}
