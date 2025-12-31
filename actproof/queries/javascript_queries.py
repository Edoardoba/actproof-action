"""
Tree-sitter queries per JavaScript/TypeScript per identificare client AI
"""

# Query per identificare import di librerie AI in JS/TS
AI_LIBRARY_IMPORT_QUERY = """
(import_statement
  source: (string) @source
  (#match? @source "@openai|@anthropic-ai|@cohere|langchain|@huggingface")
)
"""

# Query per identificare require di librerie AI
AI_LIBRARY_REQUIRE_QUERY = """
(call_expression
  function: (identifier) @func
  arguments: (arguments (string) @source)
  (#eq? @func "require")
  (#match? @source "@openai|@anthropic|openai|anthropic")
)
"""

# Query per identificare chiamate API AI
AI_API_CALL_QUERY = """
(call_expression
  function: (member_expression
    object: (_) @obj
    property: (property_identifier) @method
  )
  (#match? @method "createChatCompletion|createCompletion|createEmbedding|messages.create")
)
"""

JAVASCRIPT_QUERIES = {
    "ai_library_import": AI_LIBRARY_IMPORT_QUERY,
    "ai_library_require": AI_LIBRARY_REQUIRE_QUERY,
    "ai_api_call": AI_API_CALL_QUERY,
}
