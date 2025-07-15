import re
import random

def trim_whitespace(text, mode="both"):
    """Trims whitespace from the given text."""
    if mode == "leading":
        return "\n".join([line.lstrip() for line in text.splitlines()])
    elif mode == "trailing":
        return "\n".join([line.rstrip() for line in text.splitlines()])
    elif mode == "both":
        return "\n".join([line.strip() for line in text.splitlines()])
    return text

def change_case(text, case_type):
    """Changes the case of the given text."""
    if case_type == "upper":
        return text.upper()
    elif case_type == "lower":
        return text.lower()
    elif case_type == "title":
        return text.title()
    return text

def sort_lines(text, sort_type="alpha_asc", case_sensitive=True, remove_duplicates=False):
    """Sorts the lines in the given text."""
    lines = text.splitlines()
    if remove_duplicates:
        lines = list(dict.fromkeys(lines))

    sort_key = None
    if not case_sensitive:
        sort_key = str.lower

    if sort_type == "alpha_asc":
        lines.sort(key=sort_key)
    elif sort_type == "alpha_desc":
        lines.sort(key=sort_key, reverse=True)
    elif sort_type == "len_asc":
        lines.sort(key=len)
    elif sort_type == "len_desc":
        lines.sort(key=len, reverse=True)
    elif sort_type == "reverse":
        lines.reverse()

    return "\n".join(lines)

def pad_lines(text, target_length, pad_char, alignment):
    """Pads the lines in the given text."""
    lines = text.splitlines()
    padded_lines = []
    for line in lines:
        if alignment == "left":
            padded_lines.append(line.ljust(target_length, pad_char))
        elif alignment == "right":
            padded_lines.append(line.rjust(target_length, pad_char))
        elif alignment == "center":
            padded_lines.append(line.center(target_length, pad_char))
    return "\n".join(padded_lines)

def add_prefix_suffix(text, prefix, suffix, skip_empty):
    """Adds a prefix and/or suffix to each line."""
    lines = text.splitlines()
    modified_lines = []
    for line in lines:
        if skip_empty and not line.strip():
            modified_lines.append(line)
        else:
            modified_lines.append(f"{prefix}{line}{suffix}")
    return "\n".join(modified_lines)

def double_space_lines(text):
    """Adds a blank line after each line."""
    return "\n\n".join(text.splitlines())

def reduce_blank_lines(text):
    """Reduces multiple blank lines to a single blank line."""
    return re.sub(r'\n{2,}', '\n\n', text)

def remove_all_blank_lines(text):
    """Removes all blank lines from the text."""
    return "\n".join([line for line in text.splitlines() if line.strip()])

def delete_duplicate_consecutive_lines(text):
    """Deletes duplicate consecutive lines."""
    lines = text.splitlines()
    if not lines:
        return ""

    new_lines = [lines[0]]
    for i in range(1, len(lines)):
        if lines[i] != lines[i-1]:
            new_lines.append(lines[i])

    return "\n".join(new_lines)

def reverse_lines(text):
    """Reverses the order of lines in the text."""
    lines = text.splitlines()
    lines.reverse()
    return "\n".join(lines)

def condense_internal_whitespace(text):
    """Replaces multiple internal spaces/tabs on each line with a single space."""
    return "\n".join([" ".join(line.split()) for line in text.splitlines()])

def join_lines(text, separator=" "):
    """Joins all lines into a single line."""
    return separator.join([line.strip() for line in text.splitlines() if line.strip()])

def remove_punctuation(text):
    """Removes punctuation from the text."""
    return re.sub(r'[^\w\s]', '', text)

def shuffle_lines(text):
    """Shuffles the lines in the text."""
    lines = text.splitlines()
    random.shuffle(lines)
    return "\n".join(lines)
