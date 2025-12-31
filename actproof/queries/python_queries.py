"""
Tree-sitter queries per Python per identificare client AI e librerie ML

Updated to detect:
- Variable-based model names (not just string literals)
- Additional AI libraries (sentence-transformers, ollama, vllm, etc.)
- More model loading patterns
"""

# Query per identificare client OpenAI
OPENAI_CLIENT_QUERY = """
(call
  function: (attribute
    object: (identifier) @lib_name
    attribute: (identifier) @method_name
  )
  (#eq? @lib_name "openai")
)
"""

# Query per identificare client Anthropic
ANTHROPIC_CLIENT_QUERY = """
(call
  function: (attribute
    object: (identifier) @lib_name
  )
  (#eq? @lib_name "anthropic")
)
"""

# Query per identificare import di librerie ML (expanded)
ML_LIBRARY_IMPORT_QUERY = """
(import_statement
  name: (dotted_name) @lib_name
  (#match? @lib_name "torch|tensorflow|keras|sklearn|scikit-learn|transformers|huggingface|pytorch|sentence_transformers|sentence-transformers")
)
"""

# Query per identificare import di librerie AI (expanded with more providers)
AI_LIBRARY_IMPORT_QUERY = """
(import_statement
  name: (dotted_name) @lib_name
  (#match? @lib_name "openai|anthropic|cohere|replicate|langchain|llama_index|haystack|ollama|vllm|mlflow|together|groq|fireworks|mistralai|google.generativeai|vertexai")
)
"""

# Query per from X import Y patterns
AI_FROM_IMPORT_QUERY = """
(import_from_statement
  module_name: (dotted_name) @module
  (#match? @module "openai|anthropic|transformers|langchain|sentence_transformers|ollama|vllm|torch|tensorflow|sklearn|huggingface_hub")
)
"""

# Query per identificare chiamate a modelli
MODEL_CALL_QUERY = """
(call
  function: (attribute
    object: (_) @obj
    attribute: (identifier) @method
  )
  (#match? @method "predict|generate|forward|inference|embed|encode|decode|complete|chat")
)
"""

# Query per identificare dataset loading (supporta sia load_dataset() che obj.load_dataset())
DATASET_LOAD_QUERY = """
(call
  function: (_) @func
  arguments: (argument_list (string) @dataset_name)
  (#match? @func "load_dataset")
)
"""

# Query per identificare modelli HuggingFace con stringa
HUGGINGFACE_MODEL_QUERY = """
(call
  function: (attribute
    object: (_) @obj
    attribute: (identifier) @method
  )
  arguments: (argument_list (string) @model_name)
  (#eq? @method "from_pretrained")
)
"""

# Query per identificare from_pretrained() con qualsiasi argomento (incluse variabili)
# Questo cattura anche MODEL_NAME = "..." seguito da from_pretrained(MODEL_NAME)
FROM_PRETRAINED_ANY_QUERY = """
(call
  function: (attribute
    object: (_) @obj
    attribute: (identifier) @method
  )
  (#eq? @method "from_pretrained")
) @from_pretrained_call
"""

# Query per identificare AutoModel, AutoTokenizer, etc. (HuggingFace classes)
HUGGINGFACE_AUTO_CLASSES_QUERY = """
(call
  function: (attribute
    object: (identifier) @class_name
    attribute: (identifier) @method
  )
  (#match? @class_name "AutoModel|AutoTokenizer|AutoModelForSequenceClassification|AutoModelForCausalLM|AutoModelForTokenClassification|AutoModelForQuestionAnswering|AutoModelForMaskedLM|AutoConfig|AutoFeatureExtractor|AutoProcessor")
  (#eq? @method "from_pretrained")
) @auto_class_call
"""

# Query per HuggingFace pipeline()
HUGGINGFACE_PIPELINE_QUERY = """
(call
  function: (identifier) @func
  (#eq? @func "pipeline")
) @pipeline_call
"""

# Query per identificare training loops
TRAINING_QUERY = """
(call
  function: (attribute
    object: (_) @obj
    attribute: (identifier) @method
  )
  (#match? @method "fit|train|train_step|training_step")
)
"""

# Query per sklearn model instantiation
SKLEARN_MODEL_QUERY = """
(call
  function: (identifier) @class_name
  (#match? @class_name "RandomForest|GradientBoosting|LogisticRegression|SVC|SVR|KNeighbors|DecisionTree|AdaBoost|XGBoost|LightGBM|CatBoost|LinearRegression|Ridge|Lasso|ElasticNet|KMeans|DBSCAN|IsolationForest|PCA|StandardScaler|MinMaxScaler")
) @sklearn_model
"""

# Query per LangChain usage
LANGCHAIN_QUERY = """
(call
  function: (identifier) @class_name
  (#match? @class_name "ChatOpenAI|OpenAI|ChatAnthropic|Anthropic|LLMChain|ConversationChain|RetrievalQA|AgentExecutor")
) @langchain_call
"""

# Query per pandas data loading (potential datasets)
PANDAS_DATA_QUERY = """
(call
  function: (attribute
    object: (identifier) @lib
    attribute: (identifier) @method
  )
  (#eq? @lib "pd")
  (#match? @method "read_csv|read_json|read_parquet|read_excel|read_sql")
) @pandas_load
"""

# Query per torch DataLoader
TORCH_DATALOADER_QUERY = """
(call
  function: (attribute
    object: (_) @obj
    attribute: (identifier) @class_name
  )
  (#match? @class_name "DataLoader|Dataset")
) @torch_data
"""

# Tutte le query Python
PYTHON_QUERIES = {
    "openai_client": OPENAI_CLIENT_QUERY,
    "anthropic_client": ANTHROPIC_CLIENT_QUERY,
    "ml_library_import": ML_LIBRARY_IMPORT_QUERY,
    "ai_library_import": AI_LIBRARY_IMPORT_QUERY,
    "ai_from_import": AI_FROM_IMPORT_QUERY,
    "model_call": MODEL_CALL_QUERY,
    "huggingface_model": HUGGINGFACE_MODEL_QUERY,
    "from_pretrained_any": FROM_PRETRAINED_ANY_QUERY,
    "huggingface_auto_classes": HUGGINGFACE_AUTO_CLASSES_QUERY,
    "huggingface_pipeline": HUGGINGFACE_PIPELINE_QUERY,
    "dataset_load": DATASET_LOAD_QUERY,
    "training": TRAINING_QUERY,
    "sklearn_model": SKLEARN_MODEL_QUERY,
    "langchain": LANGCHAIN_QUERY,
    "pandas_data": PANDAS_DATA_QUERY,
    "torch_dataloader": TORCH_DATALOADER_QUERY,
}
