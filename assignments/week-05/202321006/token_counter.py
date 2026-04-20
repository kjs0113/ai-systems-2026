import tiktoken

def count_tokens(text: str, model="claude-3-5-sonnet-20241022"):
    """Accurately count tokens for the specified model."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Default to cl100k_base for newer models
        encoding = tiktoken.get_encoding("cl100k_base")
    
    return len(encoding.encode(text))

if __name__ == "__main__":
    sample_text = "Hello, this is a token counting test."
    print(f"Token count: {count_tokens(sample_text)}")
