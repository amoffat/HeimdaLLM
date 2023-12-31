safe_date_functions = {
    "age",
    "clock_timestamp",
    "current_date",
    "current_time",
    "current_timestamp",
    "date_bin",
    "date_part",
    "date_trunc",
    "extract",
    "isfinite",
    "justify_days",
    "justify_hours",
    "justify_interval",
    "localtime",
    "localtimestamp",
    "make_date",
    "make_interval",
    "make_time",
    "make_timestamp",
    "make_timestamptz",
    "now",
    "timeofday",
    "to_timestamp",
}

safe_string_functions = {
    "ascii",
    "btrim",
    "char_length",
    "character_length",
    "chr",
    "concat",
    "concat_ws",
    "convert",
    "convert_from",
    "convert_to",
    "decode",
    "encode",
    "format",
    "initcap",
    "left",
    "length",
    "lpad",
    "ltrim",
    "md5",
    "octet_length",
    "overlay",
    "pg_client_encoding",
    "quote_ident",
    "quote_literal",
    "quote_nullable",
    "regexp_matches",
    "regexp_replace",
    "regexp_split_to_array",
    "regexp_split_to_table",
    "repeat",
    "replace",
    "reverse",
    "right",
    "rpad",
    "rtrim",
    "split_part",
    "strpos",
    "substr",
    "substring",
    "to_ascii",
    "to_hex",
    "translate",
    "trim",
    "upper",
    "lower",
    "unaccent",
}

safe_math_functions = {
    "abs",
    "acos",
    "acosd",
    "acosh",
    "asin",
    "asind",
    "asinh",
    "atan",
    "atan2",
    "atan2d",
    "atand",
    "atanh",
    "cbrt",
    "ceil",
    "ceiling",
    "cos",
    "cosd",
    "cosh",
    "cot",
    "cotd",
    "degrees",
    "div",
    "exp",
    "factorial",
    "floor",
    "gcd",
    "lcm",
    "ln",
    "log",
    "log10",
    "min_scale",
    "mod",
    "pi",
    "power",
    "radians",
    "round",
    "scale",
    "sign",
    "sin",
    "sind",
    "sinh",
    "sqrt",
    "tan",
    "tand",
    "tanh",
    "trim_scale",
    "trunc",
    "width_bucket",
}

safe_text_search_functions = {
    "phraseto_tsquery",
    "plainto_tsquery",
    "to_tsquery",
    "to_tsvector",
    "ts_delete",
    "ts_filter",
    "ts_headline",
    "ts_rank_cd",
    "ts_rank",
    "ts_rewrite",
    "ts_stat",
    "ts_token_type",
    "tsquery_phrase",
    "tsvector_to_array",
    "websearch_to_tsquery",
}


safe_misc_functions = {
    "bit_count",
    "if",
    "ifnull",
    "nullif",
    "to_char",
    "to_date",
    "to_number",
    "to_timestamp",
}

safe_json_functions = {
    "json_array",
    "json_array_append",
    "json_array_insert",
    "json_contains",
    "json_contains_path",
    "json_depth",
    "json_extract",
    "json_insert",
    "json_keys",
    "json_length",
    "json_merge",
    "json_merge_patch",
    "json_merge_preserve",
    "json_object",
    "json_overlaps",
    "json_pretty",
    "json_quote",
    "json_remove",
    "json_replace",
    "json_schema_valid",
    "json_schema_validation_report",
    "json_search",
    "json_set",
    "json_type",
    "json_unquote",
    "json_valid",
    "json_value",
}

safe_agg_functions = {
    "avg",
    "bit_and",
    "bit_or",
    "bool_and",
    "bool_or",
    "count",
    "every",
    "max",
    "min",
    "sum",
    "corr",
    "covar_pop",
    "covar_samp",
    "regr_avgx",
    "regr_avgy",
    "regr_count",
    "regr_intercept",
    "regr_r2",
    "regr_slope",
    "regr_sxx",
    "regr_sxy",
    "regr_syy",
    "stddev",
    "stddev_pop",
    "stddev_samp",
    "variance",
    "var_pop",
    "var_samp",
    "array_agg",
    "json_agg",
    "jsonb_agg",
    "json_object_agg",
    "jsonb_object_agg",
    "string_agg",
    "xmlagg",
}

safe_enum_functions = {
    "enum_first",
    "enum_last",
    "enum_range",
}

safe_trgm_functions = {
    "similarity",
    "show_trgm",
    "word_similarity",
    "strict_word_similarity",
}

safe_functions = (
    safe_date_functions
    | safe_text_search_functions
    | safe_string_functions
    | safe_math_functions
    | safe_misc_functions
    | safe_json_functions
    | safe_agg_functions
    | safe_enum_functions
    | safe_trgm_functions
)

# https://www.postgresql.org/docs/current/sql-keywords-appendix.html
# these are only the explicitly reserved keywords, not the unreserved keywords.
# TODO figure out how to handle unreserved keywords.
reserved_keywords = {
    "all",
    "analyse",
    "analyze",
    "and",
    "any",
    "array",
    "as",
    "asc",
    "asymmetric",
    "authorization",
    "binary",
    "both",
    "case",
    "cast",
    "check",
    "collate",
    "column",
    "concurrently",
    "constraint",
    "create",
    "cross",
    "current_catalog",
    "current_date",
    "current_role",
    "current_schema",
    "current_time",
    "current_timestamp",
    "current_user",
    "default",
    "deferrable",
    "desc",
    "distinct",
    "do",
    "else",
    "end",
    "except",
    "false",
    "fetch",
    "for",
    "foreign",
    "freeze",
    "from",
    "full",
    "grant",
    "group",
    "having",
    "ilike",
    "in",
    "initially",
    "inner",
    "intersect",
    "into",
    "is",
    "isnull",
    "join",
    "lateral",
    "leading",
    "left",
    "like",
    "limit",
    "localtime",
    "localtimestamp",
    "natural",
    "not",
    "notnull",
    "null",
    "offset",
    "on",
    "only",
    "or",
    "order",
    "outer",
    "overlaps",
    "placing",
    "primary",
    "references",
    "returning",
    "right",
    "select",
    "session_user",
    "similar",
    "some",
    "symmetric",
    "table",
    "tablesample",
    "then",
    "trailing",
    "true",
    "union",
    "unique",
    "user",
    "using",
    "variadic",
    "when",
    "where",
    "window",
    "with",
}
