# Compare Policies Tool Fix

## Issue
The `compare_policies` tool was throwing an error:
```
Error: Too many arguments to single-input tool compare_policies. 
Consider using StructuredTool instead. 
Args: [[110.0, 109.0], 'general']
```

## Root Cause
The tool was defined using the old `Tool` wrapper with a lambda function that expected a string argument to be parsed with `eval()`. However, the Gemini function calling API was trying to pass structured arguments directly (a list and a string).

## Solution
Converted `compare_policies` (and `summarize_document` for consistency) to use `StructuredTool` with Pydantic schemas, matching the pattern already used for `count_documents` and `list_documents`.

### Changes Made

1. **Added Pydantic Input Schemas**:
```python
class ComparePoliciesInput(BaseModel):
    document_ids: list = Field(..., description="List of document IDs to compare")
    aspect: str = Field(..., description="The aspect to compare")

class SummarizeDocumentInput(BaseModel):
    document_id: int = Field(..., description="The document ID to summarize")
    focus: str = Field("general", description="Focus area for summary")
```

2. **Created Structured Wrapper Methods**:
```python
def _compare_policies_structured(self, document_ids: list, aspect: str) -> str:
    # Convert float IDs to integers (LLM sometimes returns floats)
    document_ids = [int(doc_id) for doc_id in document_ids]
    return compare_policies(document_ids=document_ids, aspect=aspect)

def _summarize_document_structured(self, document_id: int, focus: str = "general") -> str:
    return summarize_document(document_id=int(document_id), focus=focus)
```

3. **Updated Tool Definitions**:
```python
StructuredTool.from_function(
    func=self._compare_policies_structured,
    name="compare_policies",
    description="Compare TWO OR MORE documents on a specific aspect...",
    args_schema=ComparePoliciesInput
)
```

## Benefits

1. **Type Safety**: Pydantic validates input types automatically
2. **Better Error Messages**: Clear validation errors if wrong types are passed
3. **Float to Int Conversion**: Handles LLM returning floats (110.0) instead of ints (110)
4. **Consistency**: All tools now use the same StructuredTool pattern
5. **Function Calling Compatibility**: Works properly with Gemini's native function calling

## Testing

The comparison query should now work correctly:
```
Query: "compare document 100 and 79 on purpose"
Expected: Comparison table with both documents
```

The agent will:
1. Classify intent as "comparison"
2. Use `list_documents` to find documents
3. Call `compare_policies` with structured args: `{document_ids: [100, 79], aspect: "purpose"}`
4. Format the response with comparison table data
5. Return structured JSON with `format: "comparison"` and table data

## Status
✅ Fixed - All tools now use StructuredTool with proper Pydantic schemas
