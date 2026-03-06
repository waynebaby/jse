# 解释器实现正规化设计


## Engine、ENV、Parser 和 AST
  - Parser读取JSON数据，构造AST
  - AST执行得到结果
  - AST节点包含env，env在AST节点构造时传入，大多数算子并没有自己的独立env，仅需传入上级env
  - AST有get_env方法，可以给出自己的env
  - env有可空的parent字段，维护其上级env，如果在env中查询某个name没有找到，向上寻找，直到某个env中找到这个name，或者parent为null，此时返回name error
  - env中get name时，可能返回Null，这是语言设计中允许的
  - 非根的env也可能parent env为空，例如闭包环境下不应该允许从外部获取新的kv，对于卫生宏，这个特性也是有力的保障，有时候我们可能需要在运行环境间传递整段JSE甚至编译后的中间AST，不允许向上传递env查询可以提供一定的安全保障
  - AST 在eval时第一个参数也是env，这个env对于函数调用等尤其重要，它们提供调用时的实际参数，这种构造时和调用时的作用域区别是实现静态作用域的保障
  - env提供 register 方法，可以注册新的name，这对于def和defn提供了可能
  - env的执行方法是eval，ast的执行方法是apply，在~/jobs/jisp项目中可以比较清楚的看到这个分类
  - env 可以一个一个模块的整批加载（load） functor

  ## 基本算子 builtin

  在JSON语境中，JSE 不追求彻底的复现数学上的 LISP 理论。对 JSON 特性做必要的适配

  - JSE提供不同级别的 functor 组合，最小的包仅有下列几个
  - `$quote` 用于引用未经评估的表达式，例如：`[$quote ["$a","b","c"]]` 会返回列表 `["$a", "b", "c"]`
  - `$eq` 比较两个参数是否相等
  - `$cond` 根据条件判断执行不同的分支
  - `$head` 和 `$tail` 相当于标准 LISP 的 car 和 cdr
  - `$atom?` 判断传入的参数是否是 JSON 的基本元素类型
    - 数值
    - 字符串
    - boolean
    - null
  - `$cons` 将一个元素和一个 list 合并为一个新的list，这个规则遵循 clojure 的设计而非常规 lisp ，要求必须是一个任意元素和一个list，这是为了适配 JSON 的特性。在 common lisp 和emacs中，如果对两个 atom 元素进行 cons ，会构造出一个 associate pair，但是在JSON中，map必须以字符串为 key，因此我们遵循 clojure的风格，另外

### 实用算子 utils

在 LISP 中，我们仅需处理 list，而 alist 是由 list 构造得来。对于 JSE，JSON 的 Object（即map）和 array（即 list）是原生的，因此我们出于实用目的对相关的元语作一定的扩展

- `$not` 逻辑取反
- `$list?` 判断是否是 list
- `$map?` 判断是否是 map
- `$null?` 对于原本的 LISP，不区分 false 和 null，但是在现代编程语言中是有区别的
- `$get` 通过指定 key 或 index 可以从 map 或 list 中得到元素
- `$set` 在 list 的指定位置，或者map的指定 key 设置值
- `$del` 在 list 的指定位置，或者map的指定 key 设置值
- `$conj` 遵循 clojure conj 函数的方法，第一个参数是一个 list ，构造一个新list，将第二个元素添加到list末尾。

### LISP 增强算子 lisp

  - `$apply` 算子实现 apply 行为，即将第一个元素作为functor，传入后续参数执行
  - `$eval ` 实现 eval 行为，即对 ast 递次求值
  - `$null` 判断对象是否为null
  - `$cond` 多条件判断
  - `$lambda` 定义新的函数，接受参数并返回AST表达式，lambda 携带有自己的 env
  - `$def` 在最近的 env 中注册
  - `$defn` 相当于 `(def name lambda)` 的简写
