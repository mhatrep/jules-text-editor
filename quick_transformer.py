import csv
import re

def transform_line(line_parts: list[str], pattern: str, full_line: str, line_number: int) -> str:
    """
    Transforms a single line based on the pattern and its parts.
    - $1, $2, ...: Corresponds to parts of the line split by the delimiter.
    - $0: Represents the full, original line.
    - $lineNumber: The current line number (1-indexed).
    - $tab: A tab character.
    - $newline: A newline character.
    - \\$: A literal dollar sign.
    """
    # First, handle escaped dollar signs so they don't get treated as placeholders
    pattern = pattern.replace('\\$', '$$ESCAPED_DOLLAR$$')

    def replacer(match):
        token = match.group(1)
        if token == '0':
            return full_line
        elif token == 'lineNumber':
            return str(line_number)
        elif token == 'tab':
            return '\t'
        elif token == 'newline':
            return '\n'
        # Check if token is a positive integer (for $1, $2, etc.)
        elif token.isdigit() and int(token) > 0:
            try:
                index = int(token) - 1
                return line_parts[index] if 0 <= index < len(line_parts) else ''
            except ValueError: # Should not happen if token.isdigit() and int(token) > 0
                return match.group(0) # Should not be reached
        else: # Unknown token
            return match.group(0) # Return the original matched string (e.g., "$unknown")

    transformed_pattern = re.sub(r'\$(\w+)', replacer, pattern)

    # Restore escaped dollar signs
    return transformed_pattern.replace('$$ESCAPED_DOLLAR$$', '$')

def quick_transform(data: str, pattern: str, delimiter: str) -> str:
    """
    Transforms input data using a pattern and a delimiter.

    Args:
        data: The input string data, with lines separated by newlines.
        pattern: The transformation pattern string.
        delimiter: The delimiter used to split each line of the input data.
                   If delimiter is an empty string or None, lines are not split,
                   and only $0, $lineNumber, $tab, $newline are effectively available
                   (or $1 would represent the whole line if line_parts becomes [full_line]).

    Returns:
        A string with each transformed line, joined by newlines.
    """
    result = []

    # Handle empty delimiter case: treat each line as a single part
    if not delimiter:
        lines = data.strip().splitlines()
        for idx, line_content in enumerate(lines, 1):
            # For no delimiter, line_parts effectively contains the full line as its only element.
            # $1 would then be the full line. $0 is also the full line.
            line_parts = [line_content]
            transformed = transform_line(line_parts, pattern, line_content, idx)
            result.append(transformed)
    else:
        # Use csv.reader for robust delimiter handling (e.g., quoted fields)
        # We need to handle the case where the delimiter might be multiple characters,
        # csv.reader expects a single character delimiter.
        # For multi-char delimiters, we might need to pre-split or use regex.
        # For now, assuming standard single-character delimiters that csv.reader handles.
        # If delimiter is, e.g., '\\t', csv.reader needs '\t'.

        effective_delimiter = delimiter
        if delimiter == '\\t':
            effective_delimiter = '\t'
        elif delimiter == '\\n': # Though splitting by newline is usually implicit
            effective_delimiter = '\n'
        # Add other common escaped delimiters if necessary, or use a more robust way
        # to interpret escaped sequences if the GUI allows them.
        # For now, let's assume simple literal delimiters or common escapes handled above.

        try:
            reader = csv.reader(data.strip().splitlines(), delimiter=effective_delimiter)
            for idx, row in enumerate(reader, 1):
                full_line = effective_delimiter.join(row) # Reconstruct full line as CSV would see it
                transformed = transform_line(row, pattern, full_line, idx)
                result.append(transformed)
        except csv.Error as e:
            # If csv.reader fails (e.g. delimiter issue not caught above, or malformed CSV)
            # Fallback to simple split if robust CSV parsing isn't critical or fails.
            # This part can be made more sophisticated.
            # For now, let's re-raise or return an error message.
            # Or, provide a simpler split as a fallback:
            # print(f"CSV reading error: {e}. Falling back to simple split.")
            # lines = data.strip().splitlines()
            # for idx, line_content in enumerate(lines, 1):
            #     line_parts = line_content.split(delimiter) # Simple split
            #     transformed = transform_line(line_parts, pattern, line_content, idx)
            #     result.append(transformed)
            # For now, let's assume the GUI layer will catch this or we return an error string.
            raise ValueError(f"Error processing CSV data: {e}. Ensure delimiter is a single character or properly escaped if needed for special characters like tab (\\t).")


    return '\n'.join(result)

if __name__ == '__main__':
    # Example Usage:
    sample_data_csv = """John,Doe,35,"New York, NY"
Jane,Smith,29,"Los Angeles, CA"
Peter\\$Jones,Bloggs,42,London"""

    sample_pattern_csv = "Name: $1 $2, Age: $3, City: $4. Line: $lineNumber. All: $0. Literal: \\$100. Special: $tab-$newline"

    print("--- CSV Example ---")
    try:
        output_csv = quick_transform(sample_data_csv, sample_pattern_csv, ",")
        print(output_csv)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Tab Delimited Example (using literal tab in data) ---")
    sample_data_tsv = "First\tSecond\t123\nAlpha\tBeta\t456"
    sample_pattern_tsv = "Col1: $1, Col3: $3"
    try:
        output_tsv = quick_transform(sample_data_tsv, sample_pattern_tsv, "\t") # Direct tab
        print(output_tsv)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Tab Delimited Example (using '\\t' as delimiter string) ---")
    try:
        output_tsv_escaped = quick_transform(sample_data_tsv, sample_pattern_tsv, "\\t") # Escaped tab string
        print(output_tsv_escaped)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- No Delimiter Example (Line-by-Line) ---")
    sample_data_lines = "This is line one.\nThis is line two."
    sample_pattern_lines = "Processed ($lineNumber): $1" # $1 will be the full line
    try:
        output_lines = quick_transform(sample_data_lines, sample_pattern_lines, "") # Empty delimiter
        print(output_lines)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Fixed-width (simulated by no delimiter, pattern uses substring logic if needed, not directly supported by $ tokens) ---")
    # QuickText itself has more direct fixed-width support. This simulation is basic.
    # User would need to use language features in pattern if the pattern language supported it, e.g. $0.substring(0,10)
    # The current transform_line doesn't support methods on $N tokens.
    # For true fixed-width, transform_line would need to be different or data pre-processed.
    # With current logic and empty delimiter: $1 is the whole line.
    sample_data_fixed = "Part1     Part2   End"
    sample_pattern_fixed = "Line: $1"
    try:
        output_fixed = quick_transform(sample_data_fixed, sample_pattern_fixed, "")
        print(output_fixed)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Escaped Dollar Sign Example ---")
    data_with_dollar = "ProductA,$10.99\nProductB,$20.00"
    pattern_with_dollar = "Item: $1, Price: \\$$2" # User wants literal $ before the price from column 2
    try:
        output_dollar = quick_transform(data_with_dollar, pattern_with_dollar, ",")
        print(output_dollar)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Unknown token example ---")
    data_simple = "hello"
    pattern_simple = "$1 $foo $lineNumber"
    try:
        output_simple = quick_transform(data_simple, pattern_simple, "")
        print(output_simple) # Expect: hello $foo 1
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Empty input data ---")
    try:
        output_empty = quick_transform("", "Pattern: $1", ",")
        print(f"Output for empty data: '{output_empty}'") # Expect: ''
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Input data with only newlines ---")
    try:
        output_newlines = quick_transform("\n\n", "Pattern: $1 ($lineNumber)", ",")
        print(f"Output for newline data: '{output_newlines}'") # Expect: Pattern:  (1)\nPattern:  (2)\nPattern:  (3)
                                                            # because splitlines() on "\n\n" gives ["","",""]
                                                            # and csv.reader on empty strings gives empty rows.
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Input data with quotes and delimiter inside ---")
    sample_data_quotes = 'Product,"Description, with comma",Price\nItemA,"Hello, World",10.99'
    sample_pattern_quotes = "Product: $1 | Desc: $2 | Price: $3"
    try:
        output_quotes = quick_transform(sample_data_quotes, sample_pattern_quotes, ",")
        print(output_quotes)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Delimiter is space ---")
    sample_data_space = "word1 word2 word3\nnext line words"
    sample_pattern_space = "$1-$2-$3"
    try:
        output_space = quick_transform(sample_data_space, sample_pattern_space, " ")
        print(output_space)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Input data has fewer columns than pattern expects ---")
    sample_data_few_cols = "col1,col2\nanother_col1"
    sample_pattern_few_cols = "$1 | $2 | $3" # $3 will be empty for the second line
    try:
        output_few_cols = quick_transform(sample_data_few_cols, sample_pattern_few_cols, ",")
        print(output_few_cols)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Using $0 ---")
    sample_data_for_zero = "data1,data2,data3"
    sample_pattern_for_zero = "Line as is: $0 | First field: $1"
    try:
        output_for_zero = quick_transform(sample_data_for_zero, sample_pattern_for_zero, ",")
        print(output_for_zero)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Pattern with only $0 and $lineNumber ---")
    sample_pattern_zero_ln = "Original ($lineNumber): $0"
    try:
        output_zero_ln = quick_transform(sample_data_csv, sample_pattern_zero_ln, ",")
        print(output_zero_ln)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Pattern with only special tokens ---")
    sample_pattern_special_only = "$lineNumber:$tab-$newline"
    try:
        output_special_only = quick_transform("line1\nline2", sample_pattern_special_only, ",")
        print(output_special_only) # Expect "1:\t-\n\n2:\t-\n" (double newline because result lines are joined by \n)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Pattern with $0 and no delimiter specified ---")
    sample_data_no_delim_zero = "Full line one\nAnother full line"
    sample_pattern_no_delim_zero = "$lineNumber: $0 (also $1)"
    try:
        output_no_delim_zero = quick_transform(sample_data_no_delim_zero, sample_pattern_no_delim_zero, "")
        print(output_no_delim_zero)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Pattern with literal dollar signs and placeholders ---")
    data_financial = "ITEM001,500,USD"
    pattern_financial = "UPDATE records SET amount = \\$$2 WHERE id = '$1';"
    try:
        output_financial = quick_transform(data_financial, pattern_financial, ",")
        print(output_financial) # Expect: UPDATE records SET amount = $500 WHERE id = 'ITEM001';
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Pattern with only literal dollar signs ---")
    pattern_literal_only = "This is \\$100 and that is \\$200."
    try:
        output_literal_only = quick_transform("data", pattern_literal_only, ",")
        print(output_literal_only) # Expect: This is $100 and that is $200.
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Pattern with placeholder like $01 (should be $1) ---")
    data_leading_zero = "val1,val2"
    pattern_leading_zero = "$01-$0" # $01 is not a special token, should be treated as $1 by current logic if digit
                                  # My current regex \$\w+ will match "01" as the token. int("01") is 1.
                                  # So this should work as $1.
    try:
        output_leading_zero = quick_transform(data_leading_zero, pattern_leading_zero, ",")
        print(output_leading_zero) # Expect: val1-val1,val2
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Pattern with $ followed by non-word char (e.g. $!) ---")
    pattern_non_word = "Value is $1, currency is $!" # My regex \$\w+ will not match $!
    try:
        output_non_word = quick_transform("data,other", pattern_non_word, ",")
        print(output_non_word) # Expect: Value is data, currency is $!
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Pattern with $ at the end of string ---")
    pattern_dollar_end = "Value is $1 then $"
    try:
        output_dollar_end = quick_transform("data", pattern_dollar_end, "")
        print(output_dollar_end) # Expect: Value is data then $
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Complex CSV with quotes and escaped quotes within quotes ---")
    # Standard CSV doesn't really have a universal "escaped quotes within quotes" other than "" for a quote.
    # Let's test with csv.reader's behavior for "field with ""quotes"" in it"
    data_complex_csv = '1,"Field with ""internal"" quotes",value3'
    pattern_complex_csv = "ID: $1, Field2: '$2', Field3: '$3'"
    try:
        output_complex_csv = quick_transform(data_complex_csv, pattern_complex_csv, ",")
        print(output_complex_csv)
        # Expect: ID: 1, Field2: 'Field with "internal" quotes', Field3: 'value3'
        # because csv.reader handles "" as a single " inside a quoted field.
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Malformed CSV (unclosed quote) to test csv.Error fallback/handling ---")
    data_malformed_csv = '1,"Unclosed field,value2'
    # My quick_transform currently re-raises csv.Error as ValueError.
    try:
        output_malformed_csv = quick_transform(data_malformed_csv, "$1 - $2", ",")
        print(output_malformed_csv)
    except ValueError as e:
        print(f"Error (expected for malformed CSV): {e}")

    print("\n--- Input with just a delimiter ---")
    data_just_delimiter = ","
    pattern_just_delimiter = "[$1]-[$2]" # Expect [""]-[""]
    try:
        output_just_delimiter = quick_transform(data_just_delimiter, pattern_just_delimiter, ",")
        print(output_just_delimiter)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Input with two delimiters ---")
    data_two_delimiters = ",,"
    pattern_two_delimiters = "[$1]-[$2]-[$3]" # Expect [""]-[""]-[""]
    try:
        output_two_delimiters = quick_transform(data_two_delimiters, pattern_two_delimiters, ",")
        print(output_two_delimiters)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Input with leading delimiter ---")
    data_leading_delimiter = ",val1,val2"
    pattern_leading_delimiter = "[$1]-[$2]-[$3]" # Expect [""]-[val1]-[val2]
    try:
        output_leading_delimiter = quick_transform(data_leading_delimiter, pattern_leading_delimiter, ",")
        print(output_leading_delimiter)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Input with trailing delimiter ---")
    data_trailing_delimiter = "val1,val2,"
    pattern_trailing_delimiter = "[$1]-[$2]-[$3]" # Expect [val1]-[val2]-[""]
    try:
        output_trailing_delimiter = quick_transform(data_trailing_delimiter, pattern_trailing_delimiter, ",")
        print(output_trailing_delimiter)
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Input is multiple newlines and pattern uses $1, $lineNumber with no delimiter ---")
    data_many_newlines_no_delim = "\n\n\n" # 3 newlines -> 4 empty lines by splitlines()
    pattern_many_newlines_no_delim = "L$lineNumber: ($1)"
    try:
        output_many_newlines_no_delim = quick_transform(data_many_newlines_no_delim, pattern_many_newlines_no_delim, "")
        print(output_many_newlines_no_delim)
        # Expect: L1: ()\nL2: ()\nL3: ()\nL4: ()
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Input is multiple newlines and pattern uses $1, $lineNumber with comma delimiter ---")
    data_many_newlines_comma_delim = "\n\n\n" # 3 newlines -> 4 empty lines by splitlines()
                                              # csv.reader on "" yields [''] if not strip() first.
                                              # data.strip().splitlines() on "\n\n\n" is ["", "", "", ""]
                                              # csv.reader on each "" gives row=['']
    pattern_many_newlines_comma_delim = "L$lineNumber: ($1)"
    try:
        output_many_newlines_comma_delim = quick_transform(data_many_newlines_comma_delim, pattern_many_newlines_comma_delim, ",")
        print(output_many_newlines_comma_delim)
        # Expect: L1: ()\nL2: ()\nL3: ()\nL4: ()
        # because row is [''] for an empty line, so row[0] is '', line_parts[0] is ''.
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Pattern uses $10 where data only has 2 columns ---")
    data_less_cols_than_10 = "a,b\nc,d"
    pattern_less_cols_than_10 = "$1-$10" # $10 should be empty string
    try:
        output_less_cols_than_10 = quick_transform(data_less_cols_than_10, pattern_less_cols_than_10, ",")
        print(output_less_cols_than_10) # Expect: a-\nc-
    except ValueError as e:
        print(f"Error: {e}")
