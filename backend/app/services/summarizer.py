from transformers import pipeline, logging as hf_logging
import torch # Make sure torch is imported if you are using it explicitly

# Optional: Set logging level for transformers to avoid excessive informational messages
hf_logging.set_verbosity_error()

# Initialize the summarization pipeline
# Using BART model fine-tuned on CNN Daily Mail dataset
# This model will be downloaded the first time it's used (can be large ~1.6GB)
# Consider device='cuda' if you have a compatible GPU and installed torch with CUDA support
# device = 0 if torch.cuda.is_available() else -1 # -1 for CPU, 0 for first GPU
device = -1 # Default to CPU for broader compatibility initially
summarizer_pipeline = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    device=device # Use -1 for CPU, >=0 for GPU device index
)


def summarize_text(text: str, max_length: int = 150, min_length: int = 50) -> str:
    """
    Summarizes the input text using a pre-trained transformer model.

    Args:
        text: The text content to summarize.
        max_length: The maximum number of tokens in the summary.
        min_length: The minimum number of tokens in the summary.

    Returns:
        The summarized text.

    Raises:
        Exception: If summarization fails.
    """
    if not text:
        return ""

    try:
        # The pipeline handles tokenization and model inference
        # Note: BART has a max input token limit (1024 tokens). Longer texts might need chunking.
        # We are not implementing chunking here for simplicity.
        summary_result = summarizer_pipeline(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False # Use default greedy search
        )
        return summary_result[0]['summary_text']

    except Exception as e:
        print(f"Error during summarization: {e}")
        # Consider more specific error handling/logging
        raise Exception("Failed to generate summary.") from e

# --- Optional Chunking Logic (More Advanced) ---
# If you need to handle texts longer than the model's limit (e.g., 1024 tokens for BART)
# you would need to split the text, summarize chunks, and combine summaries.
# This is a non-trivial task and omitted here for simplicity. Example idea:
# 1. Use a tokenizer to split text into chunks respecting the model limit.
# 2. Summarize each chunk.
# 3. Combine the chunk summaries (e.g., just concatenate them, or run another summarization pass).
# ---