import os
import json
import pandas as pd
from typing import TypedDict, Optional
import pandas as pd
from langgraph.graph import StateGraph, END
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import faiss as FAISS
from langchain_core.messages import HumanMessage
from langchain.prompts import PromptTemplate
from hashlib import md5
from IPython.display import Image, display

AZURE_OPENAI_CONFIG = {
    "deployment_name": "gpt-4o",
    "embedding_deployment": "text-embedding-ada-002",
    "api_key": "EzqbdX8l2m0PzedkWSxkjESB5wGGDseac0Aq8SmfthOIqZ6jweNQJQQJ99BCACYeBjFXJ3w3AAABACOG5ZKu",
    "api_base": "https://qmig-open-ai.openai.azure.com/",
    "api_version": "2023-08-01-preview"
}

DATA_FOLDER = 'C:/QProjects/TestData_AI/New_data'
DDL_FOLDER = 'C:/QProjects/TestData_AI/ddls'
OUTPUT_FOLDER = "generated_test_data_new_data"
NUM_RECORDS = 100

# ================================
# STATE MODEL
# ================================

class GenerationState(TypedDict, total=False):
    tables: Optional[dict[str, pd.DataFrame]] = None
    ddls: Optional[dict[str, str]] = None
    foreign_keys: Optional[dict[str, list]] = None
    vectorstores: Optional[dict] = None
    generated: Optional[dict] = None

# ================================
# INITIALIZE AZURE OPENAI MODELS
# ================================
llm = AzureChatOpenAI(
    deployment_name=AZURE_OPENAI_CONFIG["deployment_name"],
    azure_endpoint=AZURE_OPENAI_CONFIG["api_base"],  # <-- updated
    api_key=AZURE_OPENAI_CONFIG["api_key"],
    api_version=AZURE_OPENAI_CONFIG["api_version"],
    temperature=0,
)

embedding_model = AzureOpenAIEmbeddings(
    deployment=AZURE_OPENAI_CONFIG["embedding_deployment"],
    azure_endpoint=AZURE_OPENAI_CONFIG["api_base"],  # <-- updated
    api_key=AZURE_OPENAI_CONFIG["api_key"],
    api_version=AZURE_OPENAI_CONFIG["api_version"],
)

# ================================
# LANGGRAPH AGENT NODES
# ================================
def load_csvs_node(state: GenerationState) -> GenerationState:
    print("Running load_csvs_node...")

    tables = {}
    if not os.path.exists(DATA_FOLDER):
        raise ValueError(f"DATA_FOLDER does not exist: {DATA_FOLDER}")
    
    files = os.listdir(DATA_FOLDER)
    print("Files in CSV folder:", files)

    for file in files:
        if file.endswith(".csv"):
            table_name = file.replace(".csv", "")
            path = os.path.join(DATA_FOLDER, file)
            df = pd.read_csv(path)
            print(f"Loaded {file} with shape {df.shape}")
            if not df.empty:
                tables[table_name] = df

    if not tables:
        raise ValueError("No non-empty CSV files found to load.")

    print("Returning updated state with tables:", list(tables.keys()))
    state["tables"] = tables
    return state

def load_ddls_node(state: GenerationState) -> GenerationState:
    ddls = {}
    for file in os.listdir(DDL_FOLDER):
        if file.endswith(".sql"):
            table_name = file.replace(".sql", "")
            with open(os.path.join(DDL_FOLDER, file), "r") as f:
                ddls[table_name] = f.read()
    state["ddls"] = ddls
    return state

def infer_foreign_keys_node(state: GenerationState) -> GenerationState:
    tables = state.tables
    fk_map = {}
    primary_keys = {}
    for table, df in tables.items():
        for col in df.columns:
            if col.endswith("_id"):
                primary_keys.setdefault(col, []).append(table)

    for table, df in tables.items():
        fk_map[table] = {}
        for col in df.columns:
            if col in primary_keys and table not in primary_keys[col]:
                fk_map[table][col] = df[col].dropna().astype(str).unique().tolist()
    state['foreign_keys'] = fk_map
    return state

def build_vectorstores_node(state: GenerationState) -> GenerationState:
    vectorstores = {}
    for table, df in state.tables.items():
        docs = df.astype(str).apply(lambda row: ", ".join(row), axis=1).tolist()
        vectorstores[table] = FAISS.from_texts(docs, embedding_model)
    state['vectorstores'] = vectorstores
    return state

def find_parent_table(fk_col: str, fk_map: dict[str, dict[str, list]]) -> str:
    for table, mappings in fk_map.items():
        if fk_col in mappings:
            return table
    return None

def generate_test_data_node(state: GenerationState) -> GenerationState:
    def is_duplicate(new_row, existing_rows):
        new_hash = md5(json.dumps(new_row, sort_keys=True).encode()).hexdigest()
        return new_hash in existing_rows

    generated_data = {}
    tables = list(state.tables.keys())
    fk_map = state.foreign_keys

    prompt_template = PromptTemplate.from_template("""
You are a test data generator. Generate ONE realistic, non-duplicate row for the table `{table_name}`.

DDL Definition:
{ddl}

Sample Data Context:
{examples}

Foreign Key Constraints (if any):
{fk_values}

Guidelines:
- Follow the DDL strictly (types, nullability, constraints)
- Use realistic names, emails, products, descriptions, prices, timestamps, etc.
- Avoid duplicates (no exact same rows)
- Sometimes leave nullable fields blank
- Respect relationships and existing FK values
- Ensure unique constraints (like emails, phone numbers, user_ids) are followed

Return ONLY a valid JSON object, without extra commentary or markdown.
""")

    for table in tables:
        df = state.tables[table]
        table_rows = []
        existing_hashes = set()

        for _ in range(NUM_RECORDS):
            retries = 5
            for _ in range(retries):
                sample_contexts = state.vectorstores[table].similarity_search("generate", k=3)
                context = "\n".join([doc.page_content for doc in sample_contexts])

                fk_values = fk_map.get(table, {}).copy()
                for fk_col in fk_values:
                    parent_table = find_parent_table(fk_col, fk_map)
                    if parent_table in generated_data:
                        parent_values = generated_data[parent_table][fk_col].dropna().unique().tolist()
                        if parent_values:
                            fk_values[fk_col] = parent_values

                ddl_text = state.ddls.get(table, "")
                prompt = prompt_template.format(
                    table_name=table,
                    ddl=ddl_text,
                    examples=context,
                    fk_values=json.dumps(fk_values)
                )

                response = llm([HumanMessage(content=prompt)])
                try:
                    new_row = json.loads(response.content.strip())
                    if not is_duplicate(new_row, existing_hashes):
                        existing_hashes.add(md5(json.dumps(new_row, sort_keys=True).encode()).hexdigest())
                        table_rows.append(new_row)
                        break
                except json.JSONDecodeError:
                    continue

        generated_data[table] = pd.DataFrame(table_rows)
    state["generated"] = generated_data
    return state

def save_outputs_node(state: GenerationState) -> GenerationState:
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    for table, df in state.generated.items():
        output_path = os.path.join(OUTPUT_FOLDER, f"{table}_generated.csv")
        df.to_csv(output_path, index=False)
    return state

# ================================
# BUILD LANGGRAPH FLOW
# ================================
workflow = StateGraph(GenerationState)
workflow.add_node("load_csvs", load_csvs_node)
workflow.add_node("load_ddls", load_ddls_node)
workflow.add_node("infer_foreign_keys", infer_foreign_keys_node)
workflow.add_node("build_vectorstores", build_vectorstores_node)
workflow.add_node("generate_data", generate_test_data_node)
workflow.add_node("save_data", save_outputs_node)

workflow.set_entry_point("load_csvs")
workflow.add_edge("load_csvs", "load_ddls")
workflow.add_edge("load_ddls", "infer_foreign_keys")
workflow.add_edge("infer_foreign_keys", "build_vectorstores")
workflow.add_edge("build_vectorstores", "generate_data")
workflow.add_edge("generate_data", "save_data")
workflow.add_edge("save_data", END)

# ================================
# RUN WORKFLOW
# ================================
flow = workflow.compile()
# display(Image(flow.get_graph().draw_mermaid_png()))
print("STARTING...")
final_state = flow.invoke(GenerationState())
