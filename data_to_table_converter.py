import json
import yaml

class DataParsingError(Exception):
    """Custom exception for data parsing errors."""
    pass

def parse_data(text_content: str) -> tuple[any, str]:
    """
    Tries to parse text content as JSON, then as YAML.
    Returns the parsed Python object and the detected type ('JSON' or 'YAML').
    Raises DataParsingError if both fail.
    """
    try:
        data = json.loads(text_content)
        return data, "JSON"
    except json.JSONDecodeError:
        try:
            data = yaml.safe_load(text_content)
            # YAML can parse simple strings or numbers without error,
            # which might not be what we consider "structured data" for table view.
            # We are primarily interested in dicts or lists of dicts.
            if data is None: # Handles empty YAML or YAML that only contains comments
                 raise DataParsingError("Content is empty or not valid structured data (YAML parsed as None).")
            if not isinstance(data, (dict, list)):
                raise DataParsingError(f"Content was parsed as YAML but is not a dictionary or list (type: {type(data).__name__}). Table view requires a structured object or array.")
            return data, "YAML"
        except yaml.YAMLError as e_yaml:
            raise DataParsingError(f"Failed to parse as JSON and YAML. YAML error: {e_yaml}")
        except DataParsingError: # Re-raise if it's our specific error from YAML parsing
            raise
        except Exception as e_yaml_other: # Catch other potential errors during YAML load (less common)
             raise DataParsingError(f"Failed to parse as JSON. Unexpected YAML error: {e_yaml_other}")
    except Exception as e_json_other: # Catch other potential errors during JSON load
        raise DataParsingError(f"Unexpected JSON parsing error: {e_json_other}")


def _format_value(value, indent_level=0, max_depth=2):
    """Helper to format cell values, pretty-printing collections."""
    if indent_level > max_depth:
        return "[...]" # Indicate truncated due to depth

    if isinstance(value, (dict, list)):
        try:
            # Pretty print with an indent that reflects the current cell's context
            # For initial simplicity, keep indent small for cell values.
            return json.dumps(value, indent=2)
        except TypeError:
            return str(value) # Fallback for un-serializable objects
    elif value is None:
        return "null"
    elif isinstance(value, bool):
        return str(value).lower()
    return str(value)

def format_to_text_table(data: any) -> str:
    """
    Formats parsed Python data (list of dicts, or a single dict) into a text table.
    For nested structures, they are currently pretty-printed as JSON strings within cells.
    """
    if not isinstance(data, (list, dict)):
        return "Data is not a list or dictionary, cannot format as table."

    lines = []

    if isinstance(data, list):
        if not data:
            return "Data is an empty list."

        # Assuming list of dictionaries for table structure
        # Filter out non-dictionary items for header collection, but process all for rows
        dict_items = [item for item in data if isinstance(item, dict)]
        if not dict_items:
            # If list contains no dicts, treat as a single column list of values
            headers = ["Value"]
            rows = [[_format_value(item)] for item in data]
        else:
            # Collect all unique keys from all dictionaries to form headers
            header_set = set()
            for item in dict_items:
                header_set.update(item.keys())

            if not header_set: # List of empty dicts
                 return "Data is a list of empty dictionaries."

            headers = sorted(list(header_set)) # Consistent column order

            rows = []
            for item in data:
                if isinstance(item, dict):
                    rows.append([_format_value(item.get(header, "")) for header in headers])
                else:
                    # If an item in the list is not a dict, represent it in the first column
                    # and leave other columns blank for this row.
                    row_values = [_format_value(item)] + [""] * (len(headers) - 1)
                    rows.append(row_values)

    elif isinstance(data, dict):
        if not data:
            return "Data is an empty dictionary."
        headers = ["Key", "Value"]
        rows = [[str(k), _format_value(v)] for k, v in data.items()]

    # Calculate column widths
    if not rows and not headers: # Should be caught earlier, but as a safeguard
        return "No data to format."

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            # Ensure cell is string for len()
            cell_str = str(cell)
            # Check if this row has this column, otherwise skip (for jagged rows, though we try to pad)
            if i < len(col_widths):
                 lines_in_cell = cell_str.splitlines()
                 max_line_len_in_cell = max(len(line) for line in lines_in_cell) if lines_in_cell else 0
                 col_widths[i] = max(col_widths[i], max_line_len_in_cell)
            elif i < len(headers): # cell might exist but col_widths wasn't extended for it.
                 # This case should ideally not be hit if headers cover all possible keys from dict_items
                 pass


    # Create table separator
    separator = "+-" + "-+-".join(["-" * w for w in col_widths]) + "-+"

    # Add header
    header_line_parts = []
    for i, header in enumerate(headers):
        header_line_parts.append(header.ljust(col_widths[i]))
    lines.append(separator)
    lines.append("| " + " | ".join(header_line_parts) + " |")
    lines.append(separator)

    # Add rows
    # For rows with multi-line cells, this will become more complex.
    # For now, assume single line per cell for simplicity of text table.
    # Multi-line content from _format_value (JSON dumps) will make table jagged.
    # This is a known limitation of this "first cut".
    for row in rows:
        row_line_parts = []
        for i, cell in enumerate(row):
            cell_str = str(cell)
            # For now, just take the first line of a multi-line cell for width calculation.
            # The actual cell content might still be multi-line.
            first_line_of_cell = cell_str.splitlines()[0] if cell_str.strip() else ""
            row_line_parts.append(first_line_of_cell.ljust(col_widths[i] if i < len(col_widths) else len(first_line_of_cell)))
        lines.append("| " + " | ".join(row_line_parts) + " |")

    lines.append(separator)

    return "\n".join(lines)

if __name__ == '__main__':
    # Test cases
    print("--- JSON List of Objects ---")
    json_text_list = """
    [
        {"name": "Alice", "age": 30, "city": "New York"},
        {"name": "Bob", "age": 24, "city": "Los Angeles", "occupation": "Engineer"},
        {"name": "Charlie", "age": 35, "details": {"status": "active", "projects": ["P1", "P2"]}}
    ]
    """
    try:
        parsed_json_list, p_type = parse_data(json_text_list)
        print(f"Parsed as: {p_type}")
        print(format_to_text_table(parsed_json_list))
    except DataParsingError as e:
        print(e)

    print("\n--- JSON Object ---")
    json_text_object = """
    {
        "product": "Laptop",
        "price": 1200,
        "available": true,
        "specs": {
            "cpu": "i7",
            "ram": "16GB"
        }
    }
    """
    try:
        parsed_json_object, p_type = parse_data(json_text_object)
        print(f"Parsed as: {p_type}")
        print(format_to_text_table(parsed_json_object))
    except DataParsingError as e:
        print(e)

    print("\n--- YAML List ---")
    yaml_text_list = """
    - name: David
      city: Chicago
      skills:
        - Python
        - Docker
    - name: Eve
      city: Boston
      occupation: Designer
    """
    try:
        parsed_yaml_list, p_type = parse_data(yaml_text_list)
        print(f"Parsed as: {p_type}")
        print(format_to_text_table(parsed_yaml_list))
    except DataParsingError as e:
        print(e)

    print("\n--- YAML Object ---")
    yaml_text_object = """
    fruit: apple
    size: large
    color: red
    related:
      - pie
      - cider
    """
    try:
        parsed_yaml_object, p_type = parse_data(yaml_text_object)
        print(f"Parsed as: {p_type}")
        print(format_to_text_table(parsed_yaml_object))
    except DataParsingError as e:
        print(e)

    print("\n--- Simple List (not objects) ---")
    simple_list_text = """
    ["item1", "item2", {"key": "value"}, "item4"]
    """
    try:
        parsed_simple_list, p_type = parse_data(simple_list_text)
        print(f"Parsed as: {p_type}")
        print(format_to_text_table(parsed_simple_list))
    except DataParsingError as e:
        print(e)

    print("\n--- Invalid Data ---")
    invalid_text = "This is not json or yaml { "
    try:
        parse_data(invalid_text) # Should raise error
    except DataParsingError as e:
        print(e)

    print("\n--- Empty JSON Array ---")
    empty_json_array = "[]"
    try:
        parsed_data, p_type = parse_data(empty_json_array)
        print(f"Parsed as: {p_type}")
        print(format_to_text_table(parsed_data))
    except DataParsingError as e:
        print(e)

    print("\n--- Empty JSON Object ---")
    empty_json_object = "{}"
    try:
        parsed_data, p_type = parse_data(empty_json_object)
        print(f"Parsed as: {p_type}")
        print(format_to_text_table(parsed_data))
    except DataParsingError as e:
        print(e)

    print("\n--- YAML that is just a string ---")
    yaml_just_string = "hello world"
    try:
        parsed_data, p_type = parse_data(yaml_just_string)
        print(f"Parsed as: {p_type}") # This will parse
        print(format_to_text_table(parsed_data)) # This should indicate not table-able
    except DataParsingError as e:
        print(f"Error (expected for non-structured YAML): {e}")

    print("\n--- YAML with only comments ---")
    yaml_only_comments = "# This is a comment\n# So is this"
    try:
        parsed_data, p_type = parse_data(yaml_only_comments) # safe_load returns None
        print(f"Parsed as: {p_type if 'p_type' in locals() else 'Error before type detection'}")
        if parsed_data is not None: # Should be caught by parse_data
             print(format_to_text_table(parsed_data))
    except DataParsingError as e:
        print(f"Error (expected): {e}")

    print("\n--- JSON list with non-dict items ---")
    json_mixed_list = """
    [
        {"id": 1, "value": "apple"},
        "banana",
        {"id": 2, "value": "cherry"},
        null,
        true,
        [1,2,3]
    ]
    """
    try:
        parsed_data, p_type = parse_data(json_mixed_list)
        print(f"Parsed as: {p_type}")
        print(format_to_text_table(parsed_data))
    except DataParsingError as e:
        print(e)
