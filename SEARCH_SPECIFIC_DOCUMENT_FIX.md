# search_specific_document Tool Fix

## Error
```
Error: Invalid argument provided to Gemini: 400 
* GenerateContentRequest.contents[5].parts[0].function_response.name: Name cannot be empty.
```

## Root Cause
The `search_specific_document` tool was still using the old `Tool` wrapper with a lambda function that expected a string argument to be parsed with `eval()`. This caused issues with Gemini's function calling API.

## Solution
Converted `search_specific_document` to use `StructuredTool` with a Pydantic schema, matching the pattern used for all other tools.

### Changes Made

1. **Added Pydantic Input Schema**:
```python
class SearchSpecificDocumentInput(BaseModel):
    document_id: int = Field(..., description="The document ID to search within")
    query: str = Field(..., description="The search query to find relevant content")
```

2. **Created Structured Wrapper Method**:
```python
def _search_specific_document_structured(self, document_id: int, query: str) -> str:
    return search_specific_document_lazy(
        document_id=int(document_id),
        query=query,
        user_role=self.current_user_role,
        user_institution_id=self.current_user_institution_id
    )
```

3. **Updated Tool Definition**:
```python
StructuredTool.from_function(
    func=self._search_specific_document_structured,
    name="search_specific_document",
    description="Search WITHIN a specific document...",
    args_schema=SearchSpecificDocumentInput
)
```

## All Tools Now Use StructuredTool

✅ `count_documents` - StructuredTool with CountDocumentsInput
✅ `list_documents` - StructuredTool with ListDocumentsInput  
✅ `compare_policies` - StructuredTool with ComparePoliciesInput
✅ `summarize_document` - StructuredTool with SummarizeDocumentInput
✅ `search_specific_document` - StructuredTool with SearchSpecificDocumentInput

Only simple tools remain as `Tool`:
- `search_documents` - Takes a plain string query
- `get_document_metadata` - Takes optional document ID

## Benefits

1. **Type Safety**: Pydantic validates all inputs
2. **Better Error Messages**: Clear validation errors
3. **Gemini Compatibility**: Proper function calling schema
4. **Consistency**: All structured tools use the same pattern
5. **No eval()**: Safer, no string parsing needed

## Status
✅ Fixed - All tools with structured arguments now use StructuredTool with Pydantic schemas
