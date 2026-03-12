//! JSON to AST parser for JSE.
//!
//! Following Python's ast/parser.py pattern:

use std::rc::Rc;
use std::cell::RefCell;
use std::collections::HashMap;
use serde_json::{Map, Value};
use crate::env::Env;
use crate::ast::{AstError, AstNode};
use crate::ast::nodes::{LiteralNode, SymbolNode, ArrayNode, ObjectNode, ObjectExpressionNode, QuoteNode};

pub struct Parser {
    env: Rc<RefCell<Env>>,
}

impl Parser {
    pub fn new(env: Rc<RefCell<Env>>) -> Self {
        Self { env }
    }

    pub fn parse(&self, expr: &Value) -> Result<Box<dyn AstNode>, AstError> {
        match expr {
            Value::Null | Value::Bool(_) | Value::Number(_) => {
                Ok(Box::new(LiteralNode::new(expr.clone(), Rc::clone(&self.env))))
            }
            Value::String(s) => {
                if is_symbol(s) {
                    Ok(Box::new(SymbolNode::new(s.clone(), Rc::clone(&self.env))))
                } else {
                    Ok(Box::new(LiteralNode::new(
                        Value::String(unescape(s)),
                        Rc::clone(&self.env)
                    )))
                }
            }
            Value::Array(arr) => self.parse_list(arr),
            Value::Object(obj) => self.parse_dict(obj),
        }
    }

    fn parse_list(&self, lst: &[Value]) -> Result<Box<dyn AstNode>, AstError> {
        if lst.is_empty() {
            return Ok(Box::new(ArrayNode::new(vec![], Rc::clone(&self.env))));
        }

        let first = &lst[0];

        // Special case: $quote
        if let Value::String(s) = first {
            if s == "$quote" {
                let value = lst.get(1).map(|v| self.parse(v))
                    .transpose()?
                    .unwrap_or_else(|| Box::new(LiteralNode::new(Value::Null, Rc::clone(&self.env))) as Box<dyn AstNode>);
                return Ok(Box::new(QuoteNode::new(value, Rc::clone(&self.env))));
            }
        }

        // Parse all elements
        let elements: Result<Vec<_>, _> = lst.iter()
            .map(|e| self.parse(e))
            .collect();
        Ok(Box::new(ArrayNode::new(elements?, Rc::clone(&self.env))))
    }

    fn parse_dict(&self, obj: &Map<String, Value>) -> Result<Box<dyn AstNode>, AstError> {
        let symbol_keys: Vec<_> = obj.keys()
            .filter(|k| is_symbol(k))
            .collect();

        if symbol_keys.is_empty() {
            // Regular object
            let mut dict = HashMap::new();
            for (key, value) in obj {
                let parsed_key = unescape(key);
                let parsed_value = self.parse(value)?;
                dict.insert(parsed_key, parsed_value);
            }
            return Ok(Box::new(ObjectNode::new(dict, Rc::clone(&self.env))));
        }

        if symbol_keys.len() == 1 {
            let operator = symbol_keys[0];

            // Special case: $quote
            if operator == "$quote" {
                let value = obj.get(operator)
                    .map(|v| self.parse(v))
                    .transpose()?
                    .unwrap_or_else(|| Box::new(LiteralNode::new(Value::Null, Rc::clone(&self.env))) as Box<dyn AstNode>);
                return Ok(Box::new(QuoteNode::new(value, Rc::clone(&self.env))));
            }

            // Extract metadata (non-operator keys)
            let metadata: HashMap<String, Value> = obj.iter()
                .filter(|(k, _)| *k != operator)
                .map(|(k, v)| (k.clone(), v.clone()))
                .collect();

            // Object expression
            let value = self.parse(obj.get(operator).unwrap())?;
            return Ok(Box::new(ObjectExpressionNode::new(
                operator.clone(),
                value,
                metadata,
                Rc::clone(&self.env)
            )));
        }

        Err(AstError::EvalError(
            "JSE structure error: object cannot have multiple operator keys".to_string()
        ))
    }
}

fn is_symbol(s: &str) -> bool {
    if s == "$*" {
        return false;
    }
    s.starts_with('$') && !s.starts_with("$$")
}

fn unescape(s: &str) -> String {
    if s.starts_with("$$") {
        s[1..].to_string()
    } else {
        s.to_string()
    }
}
