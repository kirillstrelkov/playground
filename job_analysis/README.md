# Job Analysis

A CLI tool to analyze job postings from a CSV, fetch each job link, extract the job description, send the content to a local LLM (via OpenAI-compatible API, e.g., LM Studio), and output CSVs with extracted requirements and skill frequency.

---

## Quickstart

1. **Install dependencies:**
   ```bash
   make dev-install
   ```

2. **Start your local LLM server:**
   - Launch [LM Studio](https://lmstudio.ai/) or another OpenAI-compatible API server.
   - Make sure it's running at `http://localhost:1234/v1` (or update the URL in `src/cli.py`).

3. **Prepare your `.env` file:**
   - Copy from a template if needed.
   - Set any required API keys (not needed for local LM Studio, but required by the library).

4. **Run the analysis:**
   ```bash
   make run
   # Or directly:
   python src/cli.py
   ```

   - By default, the tool reads from `data/in/Job applications - 2024_2025.csv`.

---

## How it Works

- Loads job positions and links from a CSV.
- Fetches each job posting using Selenium (headless Chrome).
- Extracts and cleans the text content.
- Sends the job description to a local LLM (via OpenAI API) to extract technical skills as a JSON array.
- Aggregates all skills and computes frequency tables and a skill matrix.

---

## Input Data Format

The tool expects a CSV file with at least these columns:
- **Job position**: The job title.
- **Link**: The URL to the job posting.

Example:
```csv
Job position,Link
Software Engineer,https://example.com/job1
Data Scientist,https://example.com/job2
```

---

## Output

- `data/out/skills.csv`: All extracted skills per job.
- `data/out/skills_freq.csv`: Frequency table of skills.
- `data/out/skills_matrix.csv`: Binary matrix of jobs vs. skills.

---

## Development

```bash
make fmt     # Format code with ruff
make lint    # Lint code with ruff
make test    # Run tests with pytest
make clean   # Clean artifacts and cache
```

---

## Configuration

- **Local LLM**: By default, uses LM Studio at `http://localhost:1234/v1` with a dummy API key.
- **Multiprocessing**: Uses all CPU cores minus one for parallel job fetching.
- **Environment**: Set variables in `.env` if needed.

---

## Advanced Usage

- To analyze a different CSV, update `_INPUT_CSV` in `src/cli.py` or modify the script to accept CLI arguments.
- To use a different LLM or API endpoint, change the `base_url` in [`client`](src/cli.py).

---

## Testing

Run all tests:
```bash
make test
```

---

## Notes

- The tool uses Selenium and Chrome in headless mode to fetch job postings, which works for most dynamic sites.
- Skills extraction is performed by a local LLM via the OpenAI API interface.
- For best results, ensure your local LLM is loaded and ready before running the analysis.
