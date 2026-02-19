"""
Sliding-window chunker.

Splits pages into overlapping chunks measured in whitespace-delimited tokens
(words). Each chunk carries metadata: source filename, page number, chunk
index within the document, and character offsets into the original page text.
"""

CHUNK_SIZE = 500   # words per chunk
OVERLAP = 50       # words shared with the next chunk


def chunk_pages(pages: list[dict], chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[dict]:
    """
    Args:
        pages: output of loader — list of {page, text, source}
        chunk_size: target number of words per chunk
        overlap: number of words repeated between adjacent chunks

    Returns:
        list of chunk dicts:
          {chunk_id, source, page, text, char_start, char_end}
    """
    chunks = []
    chunk_id = 0

    for page_info in pages:
        page_num = page_info["page"]
        source = page_info["source"]
        text = page_info["text"]

        words = text.split()
        if not words:
            continue

        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            # Locate character offsets in the original page text
            char_start = _find_char_offset(text, chunk_words[0], start, words)
            char_end = char_start + len(chunk_text)

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "source": source,
                    "page": page_num,
                    "text": chunk_text,
                    "char_start": char_start,
                    "char_end": char_end,
                }
            )
            chunk_id += 1

            if end == len(words):
                break
            start = end - overlap

    return chunks


def _find_char_offset(full_text: str, first_word: str, word_index: int, all_words: list[str]) -> int:
    """
    Approximate character offset for the chunk's first word by reconstructing
    the prefix from word list.
    """
    prefix = " ".join(all_words[:word_index])
    # The offset is roughly len(prefix) + 1 space (if prefix non-empty)
    if prefix:
        pos = len(prefix) + 1
    else:
        pos = 0
    return pos
