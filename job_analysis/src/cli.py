from __future__ import annotations

__version__ = "0.1.0"

import json
from multiprocessing import Pool, cpu_count
from pathlib import Path
from textwrap import dedent
from time import sleep

import openai
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tenacity import retry, stop_after_attempt, wait_fixed

_DATA_DIR_IN = Path("data/in")
_DATA_DIR_OUT = Path("data/out")
_INPUT_CSV = _DATA_DIR_IN / "Job applications - 2024_2025.csv"
_OUT_DIR_SKILLS = _DATA_DIR_OUT / "skills"
_OUT_DIR_TEXTS = _DATA_DIR_OUT / "texts"
_OUT_SKILLS = _DATA_DIR_OUT / "skills.csv"
_OUT_SKILLS_FREQ = _DATA_DIR_OUT / "skills_freq.csv"
_OUT_SKILLS_MATRIX = _DATA_DIR_OUT / "skills_matrix.csv"

client = openai.OpenAI(
    base_url="http://172.24.80.1:1234/v1",
    api_key="lm-studio",  # Can be any string, but required by the library
)

# TODO: refactor and commit
# TODO: check if not only single job is taken from web page - example LinkedIn contains multiple jobs
# TODO: if link is linkedin - expand first then taken main text

# Load environment variables from .env file
load_dotenv()


def load_csv_data(csv_path: str, position_col: str, link_col: str) -> pd.DataFrame:
    """Load job data from local CSV file."""
    df = pd.read_csv(csv_path)

    # Standardize columns (trim whitespace)
    cols = {c: c.strip() for c in df.columns}
    df.rename(columns=cols, inplace=True)

    # Check if required columns exist
    if position_col not in df.columns:
        raise ValueError(
            f"Position column '{position_col}' not found. Available columns: {list(df.columns)}"
        )
    if link_col not in df.columns:
        raise ValueError(
            f"Link column '{link_col}' not found. Available columns: {list(df.columns)}"
        )

    # Return only required columns and drop rows with missing data
    return df[[position_col, link_col]].dropna()


@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
def fetch_url_text(url):
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    sleep(5)
    text = driver.page_source
    driver.quit()

    soup = BeautifulSoup(text, "html.parser")
    # Remove script/style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())

    logger.debug(f"Fetched {len(text)} characters from {url}")

    return text


def analyze_single_job(job_data: tuple) -> dict:
    """Analyze a single job - designed for multiprocessing."""
    id_, link = job_data

    out_path = Path(f"data/out/texts/{id_}.txt")

    if not out_path.exists():
        text = fetch_url_text(link)
        out_path.write_text(text)

    return (id_, out_path.read_text())


class Column:
    POSITION = "Job position"
    LINK = "Link"
    SKILL = "skill"
    ID = "id"


def get_and_analyze_job_descriptions():
    """Analyze jobs and write CSV with columns: Job position, Link, Requirements."""
    logger.info(f"Reading CSV file: '{_INPUT_CSV}'")
    df = load_csv_data(_INPUT_CSV, Column.ID, Column.LINK)

    rows = df.to_dict(orient="records")

    # Prepare data for multiprocessing
    job_data_list = [(str(row[Column.ID]), str(row[Column.LINK])) for row in rows]

    logger.info(f"Analyzing {len(job_data_list)} jobs...")

    # Use multiprocessing for parallel analysis
    workers = cpu_count() - 1
    with Pool(processes=workers) as pool:
        job_descs = pool.map(analyze_single_job, job_data_list)

    # Extract skills using LLM
    logger.info("Extracting skills using LLM...")
    # NOTE: don't use multiprocessing here to pass context memory limit
    for id_, text in job_descs:
        get_skills_from_text(id_, text)

    logger.info("Done")


def aggregate():
    """Aggregate requirements frequency across jobs."""
    df_in = load_csv_data(_INPUT_CSV, Column.ID, Column.LINK)

    data = []
    for path in Path(_OUT_DIR_SKILLS).glob("*.json"):
        try:
            skills = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from {path}, check and fix content.")
            raise e

        data += [{Column.SKILL: skill, Column.ID: path.stem} for skill in skills]

    df_skills = pd.DataFrame(data)
    df_skills.set_index(Column.ID, inplace=True)
    df_skills.to_csv(_OUT_SKILLS)
    logger.info(f"Skills written to '{_OUT_SKILLS}'")

    # fix data
    df_skills["skill"] = df_skills["skill"].str.lower()
    df_skills["skill"] = df_skills["skill"].apply(lambda x: "go" if x == "golang" else x)
    df_skills["skill"] = df_skills["skill"].apply(lambda x: "postgresql" if x == "postgres" else x)

    df_skills["short_skill"] = df_skills["skill"].str.split().str[0]
    df_counted_skills = (
        df_skills.groupby(["short_skill"])
        .size()
        .reset_index(name="count")
        .sort_values(by="count", ascending=False)
    )
    df_counted_skills.to_csv(_OUT_SKILLS_FREQ, index=False)
    logger.info(f"Aggregated skills frequency written to '{_OUT_SKILLS_FREQ}'")

    new_columns = df_counted_skills[df_counted_skills["count"] > 1]["short_skill"].tolist()

    data = []
    data_with_skills = {int(i) for i in df_skills.index.unique()}
    for row in df_in.to_dict(orient="records"):
        if row[Column.ID] not in data_with_skills:
            continue

        id_ = str(row[Column.ID])
        skills = df_skills[df_skills.index == id_]["short_skill"].tolist()
        for col in new_columns:
            row[col] = 1 if col in skills else 0
        data.append(row)

    df_final = pd.DataFrame(data)
    df_final.transpose().to_csv(_OUT_SKILLS_MATRIX, index=True, header=False)

    logger.info(f"Skill matrix written to '{_OUT_SKILLS_MATRIX}'")


def get_skills_from_text(id_, document_text):
    """
    Reads a text file and sends its content to the OpenAI API to extract skills.
    """
    if not document_text:
        return "[]"

    root_folder = Path("data/out/skills")
    root_folder.mkdir(parents=True, exist_ok=True)
    output_path = root_folder / f"{id_}.json"
    if not output_path.exists():
        try:
            # Define the system prompt and the user's message
            system_prompt = dedent("""
            Role: You are an HR expert with 10 years of experience in hiring in software development field.
            Task: Your task is to analyze job descriptions for computer science roles and extract technical skills and requirements that are mentioned in the job description.
            Output Format: Always return a single JSON array of strings. Do NOT include anything else - just JSON array.
            Edge Case Handling: If the input text is not a job description, return an empty array `[]`.

            Special Instructions:
            - Skills should be contains '/' if they contains just split into multiple skills, e.g. "C/C++" -> "C", "C++"

            Example Output:
            ["Python", "Machine Learning", "Data Analysis"]

            Example Output 2:
            ["Java", "Spring", "Microservices", "SQL"]

            Example Output for non-job description:
            []
            """)

            user_message = dedent(f"""
            Analyze the following text and extract all skills and requirements as a single JSON array of strings:

            ----
            {document_text}
            ----
            """)

            # Send the request to the Chat Completions API
            completion = client.chat.completions.create(
                model="meta-llama-3-8b-instruct",  # Use a suitable model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "text"},  # Force the model to return a JSON object
            )

            # Extract the JSON response
            skills_json = completion.choices[0].message.content
            output_path.write_text(skills_json)

        except Exception as e:
            logger.error(f"An error occurred: {e}")

    return output_path.read_text()


if __name__ == "__main__":
    get_and_analyze_job_descriptions()
    aggregate()
