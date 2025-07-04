# Jules Text Editor

Jules Text Editor is a multi-tab text editor built with Python and Tkinter, offering basic to advanced text processing capabilities. It's designed to provide a lightweight yet functional editing experience for developers and text manipulation tasks.

## Features

*   **Multi-tab Interface**: Work with multiple files simultaneously. Each tab manages its own file and state.
*   **Core Editing**:
    *   Standard text input, selection, cut, copy, paste, undo, redo.
    *   Line Numbers displayed alongside the text.
*   **File Operations**:
    *   New, Open, Save, Save As.
    *   Automatic check for unsaved changes before closing tabs or exiting.
    *   Window and tab titles indicate file status (e.g., "\*" for unsaved).
*   **Text Processing (Format Menu)**:
    *   **Trim Whitespace**:
        *   Trim Leading Whitespace
        *   Trim Trailing Whitespace
        *   Trim Both Ends Whitespace
        (Applies to selected text or the whole document if no selection. Operates line by line.)
    *   **Change Case**:
        *   To Uppercase
        *   To Lowercase
        *   To Title Case
        (Applies to selected text or the whole document.)
    *   **Sort Lines**:
        *   Options: Alphabetical (Asc/Desc), By Length (Shortest/Longest First), Reverse Line Order.
        *   Dialog to configure sort parameters, including Case Sensitive and Remove Duplicates options where applicable.
        (Applies to selected lines or the whole document.)
    *   **Line Spacing Sub-menu**:
        *   **Condense Internal Whitespace**: Replaces multiple internal spaces/tabs on each line with a single space. Preserves leading/trailing line whitespace.
        *   **Double Space Lines**: Inserts one blank line after each original line.
        *   **Reduce Multiple Blank Lines to One**: Ensures no more than one blank line between blocks of text; also trims leading/trailing blank lines from the processed section.
        *   **Remove All Blank Lines**: Deletes all lines that are empty or contain only whitespace.
    *   **Line Alteration Sub-menu**:
        *   **Delete Duplicate Consecutive Lines**: Keeps the first line of a consecutive block of identical lines and deletes the rest (emulates `uniq`).
        *   **Reverse Lines**: Reverses the order of the selected lines (or all lines).
    *   **Join/Split Lines Sub-menu**:
        *   **Join Lines (with space)**: Joins selected/all lines into a single line, using a space as a separator. Lines are trimmed of whitespace and empty lines (after trim) are filtered out before joining.
        *   **Join Lines (with ', ')**: Similar to above, but uses a comma followed by a space (\", \") as the separator.
*   **Search (Search Menu)**:
    *   **Find/Replace Dialog (Ctrl+F)**:
        *   Find Next, Replace, Replace All. All matches highlighted, current match distinctly.
        *   Options: Case sensitive, Whole word, Regular expression (uses Tkinter's built-in regex capabilities), Wrap around, Search backwards.
        *   Non-modal dialog allows interaction with text while open.
        *   Find field can be pre-populated with selected text.

## How to Run

1.  **Prerequisites**:
    *   Python 3.x (Tkinter is usually included with standard Python installations).
2.  **Running the Editor**:
    *   Save the main application file as `editor.py` (and the `utils` directory if it contains any helper modules, though currently it's just an `__init__.py`).
    *   Open a terminal or command prompt.
    *   Navigate to the directory where you saved `editor.py`.
    *   Run the command: `python editor.py`

## Future Considerations / Potential Enhancements

*   Syntax Highlighting for various programming languages.
*   More advanced Regular Expression options (e.g., using Python's `re` module more extensively).
*   Status Bar (displaying line/column, encoding, etc.).
*   Advanced filtering capabilities.
*   Customizable settings (fonts, colors, keybindings).
*   Plugin system.

## Known Limitations
*   The "Regular Expression" option in Find/Replace uses Tkinter's Tcl-based regex engine, which may have different syntax or feature set compared to Python's `re` module.
*   Performance for some operations (like "Replace All" or sorting) on extremely large files might be slow due to the nature of Tkinter's text widget manipulations.
*   Line numbers canvas has a fixed width; very large line numbers (>9999) might get clipped.

---

Developed by Jules (AI Agent).
