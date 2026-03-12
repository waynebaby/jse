//! JSE execution engine with AST-based architecture.
//!
//! Following Python's engine.py pattern:
//! - Engine uses Parser to convert JSON to AST
//! - AST nodes are evaluated via env.eval() -> ast.apply()
//! - Supports static scoping through closure environments

use std::rc::Rc;
use std::cell::RefCell;
use serde_json::Value;
use crate::ast::{Parser, AstError};
use crate::env::Env;

/// JSE execution error.
#[derive(Debug, thiserror::Error)]
pub enum JseError {
    #[error("AST error: {0}")]
    AstError(#[from] AstError),

    #[error("{0}")]
    Message(String),
}

impl JseError {
    pub fn msg(s: impl Into<String>) -> Self {
        JseError::Message(s.into())
    }
}

/// JSE execution engine with AST-based execution.
///
/// The engine parses JSON expressions into AST nodes, then evaluates
/// them using the environment's eval() method (which delegates to
/// each AST node's apply() method).
///
/// This architecture enables:
/// - Static scoping (closures capture construct-time environment)
/// - Proper separation of parsing and evaluation
/// - Modular functor loading via env.load()
pub struct Engine {
    env: Rc<RefCell<Env>>,
    parser: Parser,
}

impl Engine {
    /// Create a new engine with the given environment.
    ///
    /// The environment should have functors loaded via env.load()
    /// before executing expressions.
    pub fn new(env: Rc<RefCell<Env>>) -> Self {
        let parser = Parser::new(Rc::clone(&env));
        Self { env, parser }
    }

    /// Create a new engine with minimal environment (no functors loaded).
    ///
    /// Suitable for basic JSON operations without any functors.
    /// Use this when you only need to evaluate literal values and data structures.
    pub fn with_env() -> Self {
        let env = Rc::new(RefCell::new(Env::new()));
        Self::new(env)
    }

    /// Create a new engine with default functors loaded.
    ///
    /// Includes: builtin + utils
    /// Excludes: lisp (too powerful for most business use), sql (domain-specific)
    ///
    /// This is the recommended environment for most business logic operations.
    pub fn with_default_env() -> Self {
        let env = Rc::new(RefCell::new(Env::new()));
        env.borrow_mut().load(&crate::functors::builtin::builtin_functors());
        env.borrow_mut().load(&crate::functors::utils::utils_functors());
        Self::new(env)
    }

    /// Execute a JSE expression.
    ///
    /// Parses the expression into an AST, then evaluates it using
    /// the environment's eval() method (which delegates to ast.apply()).
    pub fn execute(&self, expr: &Value) -> Result<Value, JseError> {
        // Parse into AST
        let ast = self.parser.parse(expr)?;

        // Evaluate using environment (delegates to ast.apply())
        // Note: We call apply directly to avoid borrow conflicts
        ast.apply(&self.env).map_err(JseError::from)
    }

    /// Get a reference to the environment.
    pub fn env(&self) -> &Rc<RefCell<Env>> {
        &self.env
    }
}

/// Trait for types that can provide an environment reference
pub trait AsEnv {
    fn as_env_ref(&self) -> &Rc<RefCell<Env>>;
}

impl AsEnv for Rc<RefCell<Env>> {
    fn as_env_ref(&self) -> &Rc<RefCell<Env>> {
        self
    }
}
