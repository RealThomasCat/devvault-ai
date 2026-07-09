def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> list[str]:
    """
    Split text into overlapping character-based chunks.

    Leading and trailing whitespace is removed before chunking. Each chunk is at
    most `chunk_size` characters, and consecutive chunks overlap by
    `chunk_overlap` characters to reduce context loss at chunk boundaries.

    Args:
        text: Source text to split.
        chunk_size: Maximum number of characters per chunk.
        chunk_overlap: Number of characters repeated between consecutive chunks.

    Returns:
        A list of non-empty text chunks in their original order.

    Raises:
        ValueError: If `chunk_size` is not positive, `chunk_overlap` is negative,
        or `chunk_overlap` is greater than or equal to `chunk_size`.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    # Clean the input text by stripping leading and trailing whitespace
    cleaned_text = text.strip()

    if not cleaned_text:
        return []

    chunks: list[str] = []
    start = 0

    # Loop through the cleaned text and create chunks based on the specified chunk size and overlap
    while start < len(cleaned_text):
        end = start + chunk_size
        chunk = cleaned_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(cleaned_text):
            break

        start = end - chunk_overlap

    return chunks