//! Environment for JSE execution with scope chaining.
//!
//! Following Python's env.py pattern:
//! - env has nullable parent field for scope chain lookup
//! - env provides register() method for def/defn
//! - env provides load() method for functor modules
//! - env.eval() delegates to ast.apply() (following jisp pattern)

use std::rc::Rc;
use std::cell::RefCell;
use std::collections::HashMap;
use serde_json::Value;
use crate::ast::{AstNode, AstError};

/// Functor type: function that takes env and arguments, returns Value
pub type Functor = fn(&Rc<RefCell<Env>>, &[Value]) -> Result<Value, AstError>;

/// Environment for JSE execution with scope chaining
pub struct Env {
    parent: Option<Rc<RefCell<Env>>>,
    bindings: HashMap<String, Value>,
    functor_map: HashMap<String, Functor>,
    /// Metadata context for functor calls
    current_meta: HashMap<String, Value>,
}

impl Env {
    /// Get this environment as an Rc<RefCell<Env>>.
    /// If this is the top-level environment, wrap it in a new Rc<RefCell>.
    /// Otherwise, return the parent Rc with this environment's bindings merged.
    /// For simplicity, we return the parent if available, or create a new wrapper.
    fn as_rc(&self) -> Rc<RefCell<Env>> {
        if let Some(parent) = &self.parent {
            Rc::clone(parent)
        } else {
            // For top-level env, we need to create a new Rc
            // This is a limitation - the caller should ideally pass the Rc in
            // But for our use case, we can work around it
            Rc::new(RefCell::new(self.clone()))
        }
    }
    /// Create a new empty environment
    pub fn new() -> Self {
        Self {
            parent: None,
            bindings: HashMap::new(),
            functor_map: HashMap::new(),
            current_meta: HashMap::new(),
        }
    }

    /// Create a new environment with a parent (for closures/scope chain)
    pub fn new_with_parent(parent: Option<Rc<RefCell<Env>>>) -> Self {
        Self {
            parent,
            bindings: HashMap::new(),
            functor_map: HashMap::new(),
            current_meta: HashMap::new(),
        }
    }

    /// Get the parent environment
    pub fn get_parent(&self) -> Option<Rc<RefCell<Env>>> {
        self.parent.as_ref().map(Rc::clone)
    }

    /// Get the current metadata context
    pub fn get_meta(&self) -> &HashMap<String, Value> {
        &self.current_meta
    }

    /// Set the current metadata context (before functor call)
    pub fn set_meta(&mut self, meta: HashMap<String, Value>) {
        self.current_meta = meta;
    }

    /// Clear the current metadata context (after functor call)
    pub fn clear_meta(&mut self) {
        self.current_meta.clear();
    }

    /// Resolve symbol to value by searching up the scope chain
    pub fn resolve(&self, symbol: &str) -> Option<Value> {
        if let Some(value) = self.bindings.get(symbol) {
            Some(value.clone())
        } else if let Some(parent) = &self.parent {
            parent.borrow().resolve(symbol)
        } else {
            None
        }
    }

    /// Register a new symbol binding (throws if exists)
    pub fn register(&mut self, name: String, value: Value) -> Result<(), AstError> {
        if self.bindings.contains_key(&name) {
            return Err(AstError::EvalError(
                format!("Symbol '{}' already exists in current scope", name)
            ));
        }
        self.bindings.insert(name, value);
        Ok(())
    }

    /// Set a symbol binding (overwrites if exists)
    pub fn set(&mut self, name: String, value: Value) {
        self.bindings.insert(name, value);
    }

    /// Check if symbol exists in scope chain
    pub fn exists(&self, name: &str) -> bool {
        self.bindings.contains_key(name) ||
        self.parent.as_ref().map_or(false, |p| p.borrow().exists(name))
    }

    /// Register a functor
    pub fn register_functor(&mut self, name: String, functor: Functor) {
        self.functor_map.insert(name, functor);
    }

    /// Load a module of functors into this environment
    pub fn load(&mut self, module: &HashMap<&'static str, Functor>) {
        for (name, functor) in module {
            self.functor_map.insert(name.to_string(), *functor);
        }
    }

    /// Evaluate an AST node in this environment.
    ///
    /// This is the core method that delegates to ast.apply(self),
    /// following the jisp pattern where env.eval() delegates to ast.apply().
    pub fn eval(&self, node: &dyn AstNode, env: &Rc<RefCell<Env>>) -> Result<Value, AstError> {
        node.apply(env)
    }

    /// Evaluate an AST node using self as the environment.
    /// This is a convenience method that creates an Rc wrapper if needed.
    pub fn eval_node(&self, node: &dyn AstNode) -> Result<Value, AstError> {
        let env = self.as_rc();
        node.apply(&env)
    }

    /// Apply a functor with AST nodes (for special forms)
    pub fn apply_functor(
        &self,
        name: &str,
        env: &Rc<RefCell<Env>>,
        args: &[&dyn AstNode]
    ) -> Result<Value, AstError> {
        let functor = self.resolve_functor(name)
            .ok_or_else(|| AstError::SymbolNotFound(name.to_string()))?;

        // Convert AST nodes to their JSON representation for special forms
        let json_args: Vec<Value> = args.iter()
            .map(|node| node.to_json())
            .collect();

        functor(env, &json_args)
    }

    /// Apply a functor with AST nodes using self as the environment.
    /// This is a convenience method that avoids passing env twice.
    pub fn apply_functor_node(&self, name: &str, args: &[&dyn AstNode]) -> Result<Value, AstError> {
        let env = self.as_rc();
        let functor = self.resolve_functor(name)
            .ok_or_else(|| AstError::SymbolNotFound(name.to_string()))?;

        let json_args: Vec<Value> = args.iter()
            .map(|node| node.to_json())
            .collect();

        functor(&env, &json_args)
    }

    /// Apply a functor with evaluated values
    pub fn apply_functor_with_values(
        &self,
        name: &str,
        env: &Rc<RefCell<Env>>,
        args: &[Value]
    ) -> Result<Value, AstError> {
        let functor = self.resolve_functor(name)
            .ok_or_else(|| AstError::SymbolNotFound(name.to_string()))?;

        functor(env, args)
    }

    /// Apply a functor with evaluated values using self as the environment.
    /// This is a convenience method that avoids passing env twice.
    pub fn apply_functor_values(&self, name: &str, args: &[Value]) -> Result<Value, AstError> {
        let env = self.as_rc();
        let functor = self.resolve_functor(name)
            .ok_or_else(|| AstError::SymbolNotFound(name.to_string()))?;

        functor(&env, args)
    }

    /// Resolve a functor from the environment chain
    pub fn resolve_functor(&self, name: &str) -> Option<Functor> {
        if let Some(&functor) = self.functor_map.get(name) {
            Some(functor)
        } else if let Some(parent) = &self.parent {
            parent.borrow().resolve_functor(name)
        } else {
            None
        }
    }
}

impl Clone for Env {
    fn clone(&self) -> Self {
        Self {
            parent: self.parent.as_ref().map(Rc::clone),
            bindings: self.bindings.clone(),
            functor_map: self.functor_map.clone(),
            current_meta: self.current_meta.clone(),
        }
    }
}

impl Default for Env {
    fn default() -> Self {
        Self::new()
    }
}
