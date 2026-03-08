package io.github.marchliu.jse.functors;

import io.github.marchliu.jse.Env;
import io.github.marchliu.jse.Functor;
import io.github.marchliu.jse.Parser;
import io.github.marchliu.jse.ast.AstNode;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * SQL extension functors for JSE.
 *
 * <p>Demonstrates local scope: ONLY exports $query globally.
 * Local operators ($pattern, $and, $*) are ONLY available inside $query's local scope.</p>
 */
public final class SqlFunctors {

    private SqlFunctors() {}

    /** Query field list for SQL SELECT. */
    public static final String QUERY_FIELDS = "subject, predicate, object, meta";

    /**
     * $pattern functor - Generate SQL WHERE condition for a triple pattern.
     * This is the LOCAL version used inside $query.
     * Form: [$pattern, subject, predicate, object]
     */
    public static final Functor PATTERN = (env, args) -> {
        if (args.length < 3) {
            throw new IllegalArgumentException("$pattern requires (subject, predicate, object)");
        }

        Object subj = args[0];
        Object pred = args[1];
        Object obj = args[2];

        if (!(subj instanceof String s && pred instanceof String p && obj instanceof String o)) {
            throw new IllegalArgumentException("$pattern requires string arguments");
        }

        List<String> triple = patternToTriple(s, p, o);
        return tripleToSqlCondition(triple);
    };

    /**
     * SQL-specific AND: joins conditions with " and ".
     * This is LOCAL-ONLY for $query, different from logical $and in UtilsFunctors.
     */
    public static final Functor SQL_AND = (env, args) -> {
        StringBuilder result = new StringBuilder();
        for (Object arg : args) {
            Env envImpl = (Env) env;
            Object evaluated = envImpl.eval(arg);
            String sql = (String) evaluated;
            if (result.length() > 0) {
                result.append(" and ");
            }
            result.append(sql);
        }
        return result.toString();
    };

    /**
     * Wildcard helper for local scope.
     */
    public static final Functor WILDCARD = (env, args) -> "*";

    /**
     * Local operators map - NOT exported globally.
     * Only available inside $query's local scope.
     */
    private static final Map<String, Functor> LOCAL_SQL_FUNCTORS;

    static {
        LOCAL_SQL_FUNCTORS = new LinkedHashMap<>();
        LOCAL_SQL_FUNCTORS.put("$pattern", PATTERN);
        LOCAL_SQL_FUNCTORS.put("$and", SQL_AND);
        LOCAL_SQL_FUNCTORS.put("$*", WILDCARD);
    }

    /**
     * $query functor - Generate SQL for multi-pattern query with LOCAL environment.
     * Form: {$query: condition}
     * where condition is an AST expression with local operators ($pattern, $and, $*)
     */
    public static final Functor QUERY = (env, args) -> {
        if (args.length < 1) {
            throw new IllegalArgumentException("$query expects a condition expression");
        }

        // Create LOCAL environment with parent
        Env local = new Env((Env) env);

        // Load LOCAL operators into local scope
        local.load(LOCAL_SQL_FUNCTORS);

        // Parse and evaluate in LOCAL environment
        Parser parser = new Parser(local);
        Object parsed = parser.parse(args[0]);
        AstNode condition = (AstNode) parsed;
        Object where = condition.apply(local);

        String whereStr = (String) where;
        return "select " + QUERY_FIELDS + " \n" +
                "from statement \n" +
                "where \n" +
                "    " + whereStr + " \n" +
                "offset 0\n" +
                "limit 100 \n";
    };

    /**
     * Convert $pattern arguments to PostgreSQL jsonb containment triple.
     * <ul>
     *   <li>["*", "author of", "*"] -> ["author of"]</li>
     *   <li>["Liu Xin", "author of", "*"] -> ["Liu Xin", "author of", "*"]</li>
     * </ul>
     */
    public static List<String> patternToTriple(String subject, String predicate, String object) {
        List<String> pattern = new ArrayList<>(3);
        if (!"*".equals(subject) && !"$*".equals(subject)) {
            pattern.add(subject);
        }
        if (!"*".equals(predicate) && !"$*".equals(predicate)) {
            pattern.add(predicate);
        }
        if (!"*".equals(object) && !"$*".equals(object)) {
            pattern.add(object);
        }
        return pattern;
    }

    /**
     * Build SQL WHERE clause for a triple pattern.
     */
    public static String tripleToSqlCondition(List<String> triple) {
        String json = toJson(triple);
        String escaped = json.replace("'", "''");
        return "meta @> '" + escaped + "'";
    }

    /**
     * Convert triple list to JSON string.
     */
    private static String toJson(List<String> triple) {
        StringBuilder sb = new StringBuilder();
        sb.append("{\"triple\":[");
        for (int i = 0; i < triple.size(); i++) {
            if (i > 0) {
                sb.append(',');
            }
            sb.append('"').append(escapeJson(triple.get(i))).append('"');
        }
        sb.append("]}");
        return sb.toString();
    }

    /**
     * Escape string for JSON.
     */
    private static String escapeJson(String value) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '\\' -> sb.append("\\\\");
                case '"' -> sb.append("\\\"");
                case '\b' -> sb.append("\\b");
                case '\f' -> sb.append("\\f");
                case '\n' -> sb.append("\\n");
                case '\r' -> sb.append("\\r");
                case '\t' -> sb.append("\\t");
                default -> {
                    if (c < 0x20) {
                        sb.append(String.format("\\u%04x", (int) c));
                    } else {
                        sb.append(c);
                    }
                }
            }
        }
        return sb.toString();
    }

    /**
     * SQL module functors - ONLY exports $query.
     * The local operators ($pattern, $and, $*) are NOT globally available.
     */
    public static final Map<String, Functor> SQL_FUNCTORS;

    static {
        SQL_FUNCTORS = new LinkedHashMap<>();
        SQL_FUNCTORS.put("$query", QUERY);
    }
}
