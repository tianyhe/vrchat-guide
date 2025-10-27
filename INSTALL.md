# VRChat Guide - Getting Started Guide

The following documentation has been run and tested on macOS.

## Prerequisites

### Genie + SUQL Framework

- Python 3.11 or higher
- UV package manager
- PostgreSQL 14 or higher + postgresql-plpython3
- OpenAI API key / Azure OpenAI API key
- Google Service Account Key - spreadsheet specification access
- Google Calendar API Credentials - syncing calendar data to database

### VRChat Integration - from NEU-LLM-Avatars - TODO

- ffmpeg (for audio processing in VRChat)
- Torch with CUDA support
- Visual C++ Build Tools
- Visual C++ Redistrubutable
- VBCable
- 2 Computers - needed for simulation

## Installation

```shell
# Clone the repository
git clone --recurse-submodules https://github.com/tianyhe/vrchat-guide.git
cd vrchat-guide

# If submodules are not cloned, run the following command
git submodule update --init --recursive

# Create and activate virtual environment
uv venv
source .venv/bin/activate
uv sync

# Install genie-worksheets in editable mode if not already installed
uv pip install -e packages/genie-worksheets

# Install spaCy model if not already installed
python -m spacy download en_core_web_sm

# Update PYTHONPATH to include Genie Worksheets package
export PYTHONPATH="${PROJECT_ROOT}/packages:${PYTHONPATH}"
export PYTHONPATH="${PROJECT_ROOT}/packages/genie-worksheets:${PYTHONPATH}"
```

## **LLM Config**

You should create a `.env` file similar to `.env.example` and fill in the values for the LLM API keys and endpoints.

```shell
LLM_API_KEY=<>
LLM_API_BASE_URL=<>  # for openai
LLM_API_ENDPOINT=<>  # for azure
LLM_API_VERSION=<>  # for azure
```

## **Spreadsheet Specification**

To create a new agent, you should have a Google Service Account and create a new spreadsheet. You can follow the instructions [service-account-overview](https://cloud.google.com/iam/docs/service-account-overview) to create a Google Service Account. Share the created spreadsheet with the service account email.

You should save the service_account key as `service_account.json` in the `packages/genie-worksheets/src/worksheets/config/` directory.

## Google Calendar API Configuration

To obtain VRChat event data, the current approach pulls event information from subscribed public calendars (e.g., VRChat Events Hub).

Setup the Google Calendar API and place the credentials in the following path:
`config/credentials.json`

First time you run the program, you should authorize the application to access
your Google Calendar. The `token.json` file will be created in the same directory.

## **Database Setup - Linux / MacOS**

The following services are required to run the VRChat Guide agent:

- PostgreSQL Database
- Embedding Server (FAISS)
- Free-text Server

The database and agent can run on separate machines (e.g., a server and a client). The database can be set up on a separate machine, and the agent can be run on a local machine. But the address and port are needed for the agent to connect to the database.

### **Installing [PostgreSQL database](https://www.postgresql.org/)**

1. Follow the [instruction](https://www.postgresql.org/download/) there to install a postgreSQL database.
2. the SUQL compiler needs to make use of python functions within postgreSQL. This is done via the `postgresql-plpython3` language. If you are using Ubuntu, simply run `sudo apt-get install postgresql-plpython3-<your_psql_version>`.
3. Then, in your database's command line (incurred via `psql <your_database_name>`), do `CREATE EXTENSION plpython3u;`. This loads this language into the current db.

### **PostgresSQL Database**

The PostgreSQL database is used to store event information and user preferences. Initialize the database schema if not already initialized:

Create the database and users:

```sql
CREATE DATABASE vrchat_events;
CREATE ROLE select_user WITH PASSWORD 'select_user';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO select_user; 
ALTER ROLE select_user LOGIN;
CREATE ROLE creator_role WITH PASSWORD 'creator_role';
GRANT CREATE ON DATABASE vrchat_events TO creator_role; 
GRANT CREATE ON SCHEMA public TO creator_role;
ALTER ROLE creator_role LOGIN;
```

Initialize the database schema and start the syncing and embedding using the following command when in root:

```shell
# Initialize Schema (only need to run once)
python scripts/database/init_database.py

# Start Calendar Events Sync - Need Google Calendar API Setup
python scripts/db_sync.py
```

### Free-Text Server (in new terminal)

The Free-text Server is used to handle free-text queries on documents stored in `vrchat_guide/data.` Start the server using the following command when in root:

```shell
python scripts/free_text_server.py
```

For more information about SUQL and its usage, please refer to the [SUQL](https://github.com/stanford-oval/suql) repository.

### Few-Shot Prompts

The prompts for the semantic parser, response generator, and SUQL parser are stored in `vrchat_guide/prompts` for both the agent and the SUQL compilers.

## Agents

Details on how to create an agent can refer to `genie-worksheet/README.md - Creating Agents` session.

### Creating the Agent

VRChat Guide agent are present in the `src/vrchat-guide` folder.

`vrchat-guide/vrchatbot.py` are the updated version of the agent that works with the updated `genie-worksheet` packages.

### Add Prompts

For each agent you need to create prompts for:

- Semantic parsing: `semantic_parsing.prompt`
- Response generation: `response_generator.prompt`
- SUQL queries: `suql_parser.prompt`

These prompts are currently placed in the `prompts` folder.

### Setup the Agent

Creating and setting up the agent needs the following components:

1. Model configuration
2. API functions of the Agent
3. Starting prompt
4. SUQLKnowledgeBase for the Agent
5. SUQLParser for the Agent
6. Spreadsheet Specification Google Sheet ID
7. Build the Agent - Either with `Agent` class or `AgentBuilder` class

## Run the Agent

### Run servers

```shell
# Initialize database schema, if not yet initialized
python scripts/database/init_database.py

# Start Calendar Events Syn - Assume database schema are init
python scripts/db_sync.py

# Start Embedding Server (new terminal)
python scripts/embedding_server.py
(p.s. This may crash, won't be able to test at the moment.) - possibly memory issues

# Start Free-text Server (new terminal)
python scripts/free_text_server.py
```

### Command-Line Interface

You can run the agent in CLI to verify setup by running:

```shell
# Start the VRChat Guide Agent in text mode
python src/vrchat_guide/vrchatbot.py
```

### Web Interface - TODO

**NOTE:** You should run the agent in the `frontend` directory to preserve the frontend assets.

```shell
cd src/vrchat_guide/frontend/

# Start the VRChat Guide Agent in web interface without metrics logging
chainlit run app_vrchat_guide.py --port 8800
```

### VRChat Interface - TODO

```shell
cd src/vrchat_guide/vrchat_interface/

# Start the VRChat Guide Avatar in VRChat
# Enable OSC control of the avatar
# Switch sound output to "CABLE Input" in Windows sound settings

python .\vrchat_interface.py # Windows
```
