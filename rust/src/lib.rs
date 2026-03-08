//! JSE (JSON Structural Expression) interpreter for Rust.
//!
//! See [JSE spec](https://github.com/MarchLiu/jse) and [README](https://github.com/MarchLiu/jse#readme).

pub mod ast;
pub mod engine;
pub mod env;
pub mod functors;

pub use engine::{Engine, AsEnv, JseError};
pub use env::{Env, Functor};
pub use serde_json::Value as JseValue;
pub use functors::sql::{pattern_to_triple, triple_to_sql_condition, QUERY_FIELDS};

// Re-export commonly used AST types
pub use ast::{AstError, Parser, AstNode};

// Re-export functor module functions for easy loading
pub use functors::builtin::builtin_functors;
pub use functors::lisp::lisp_functors;
pub use functors::utils::utils_functors;
pub use functors::sql::sql_functors;
