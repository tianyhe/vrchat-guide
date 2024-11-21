# VRChat Guide 🎮

An intelligent VRChat agent built using the Genie Worksheets framework, demonstrating advanced knowledge-integrated task assistance for social VR environments. This project showcases real-time knowledge retrieval and task completion capabilities to provide immersive, dynamic, and personalized assistance for VRChat users.

<div align="center">

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-blue.svg)](https://www.postgresql.org/)

</div>

## 🌟 Features

- Real-time event information retrieval and recommendations
- Personalized VRChat experience assistance
- Task completion support for common VRChat activities
- Dynamic knowledge integration with VRChat's social environment
- Adaptive response system based on user preferences

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher
- UV package manager
- OpenAI API key / Azure OpenAI API key

## 🚀 Quick Start

### 1. Clone and Setup

To install Genie, we recommend using uv ([UV installation guide](https://github.com/astral-sh/uv?tab=readme-ov-file#installation))

```bash
# Clone the repository
git clone https://github.com/tianyhe/vrchat-guide.git
cd vrchat-guide

# If submodules are not cloned, run the following command
git submodule update --init --recursive

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Unix
# or
.venv\Scripts\activate   # Windows

# Install core dependencies
uv sync

# Install Development Dependencies
uv pip install -e ".[all]"

# Install SpaCy Model
python -m spacy download en_core_web_sm

```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
# PYTHONPATH Configuration
export PYTHONPATH="${PYTHONPATH}:${PWD}/packages/genie-worksheets"
export PYTHONPATH="${PYTHONPATH}:${PWD}/packages/neu-llm-avatars"
export PYTHONPATH="${PYTHONPATH}:${PWD}/packages/genie-worksheets/src"
export PYTHONPATH="${PYTHONPATH}:${PWD}/packages/genie-worksheets/packages/knowledge-agent/src"
export PYTHONPATH="${PYTHONPATH}:${PWD}/packages/suql/src"
export PYTHONPATH="${PYTHONPATH}:${PWD}/packages"

# API Configuration
export OPENAI_API_KEY=your_openai_api_key
```

Load the environment:
```bash
source .env  # Remember to source after opening new terminal sessions
```

### 3. Database Setup

```bash
# Setup PostgreSQL Database
sudo -u postgres psql

postgres=# CREATE DATABASE vrchat_events;
postgres=# CREATE ROLE select_user WITH PASSWORD 'select_user';
postgres=# GRANT SELECT ON ALL TABLES IN SCHEMA public TO select_user;
postgres=# ALTER ROLE select_user LOGIN;
postgres=# CREATE ROLE creator_role WITH PASSWORD 'creator_role';
postgres=# GRANT CREATE ON DATABASE vrchat_events TO creator_role;
postgres=# GRANT CREATE ON SCHEMA public TO creator_role;
postgres=# ALTER ROLE creator_role LOGIN;
postgres=# \q

```

### 4. Configure Required Services and Credentials

#### LLM Config File Setup

Create the llm_config.yaml file and place it the following path:

```bash
./llm_config.yaml
./src/vrchat_guide/llm_config.yaml
./packages/genie-worksheets/packages/knowledge-agent/src/kraken/llm_config.yaml
```

#### Spreadsheet Specification

To create a new agent, you should have a Google Service Account and create a new spreadsheet. 
You can follow the instructions [here](https://cloud.google.com/iam/docs/service-account-overview) to create a Google Service Account.
Share the created spreadsheet with the service account email.

You should save the service_account key as `service_account.json` in the following path:

```bash
./packages/genie-worksheets/src/worksheets/service_account.json
```

Here is a starter worksheet that you can use for your reference: [Starter Worksheet](https://docs.google.com/spreadsheets/d/1ST1ixBogjEEzEhMeb-kVyf-JxGRMjtlRR6z4G2sjyb4/edit?usp=sharing)

Here is a sample spreadsheet for a restaurant agent: [VRChat Guide Agent](https://docs.google.com/spreadsheets/d/1aLyf6kkOpKYTrnvI92kHdLVip1ENCEW5aTuoSZWy2fU/edit?gid=0#gid=0)

Please note that we only use the specification defined in the first sheet of the spreadsheet.

#### Google Calendar API Configuration

Setup the Google Calendar API and place the credentials in the following path:
```bash
./config/credentials.json
```
First time  you run the program, you should authorize the application to access your Google Calendar. The `token.json` file will be created in the same directory.


### 5. Start Required Services

The following services are required to run the VRChat Guide agent:

- PostgreSQL Database
- Embedding Server (FAISS)
- Free-text Server

Each of them should be started in separate terminal windows.

#### Start PostgreSQL Database

The PostgreSQL database is used to store event information and user preferences. Initialize the database schema if not already initialized:
```bash
# Initialize Schema (only need to run once)
python scripts/database/init_database.py

# Start Calendar Events Sync
python scripts/db_sync.py
```

#### Start Embedding Server

The Embedding Server is used to generate embeddings for free-text queries. Start the server using the following command:
```bash
python packages/suql/src/suql/faiss_embedding.py
```
p.s. This will occasionally crash, but it's fine.

#### Start Free-text Server (in new terminal)

The Free-text Server is used to handle free-text queries. Start the server using the following command:
```bash
python scripts/free_text_server.py
```

## 🧪 Verify Development Setup

```bash
# Test dependencies
python tests/verify_install.py
python tests/test_dependencies.py

# Test database connection
python tests/test_db_connection.py

# Test entry point
python tests/test_entry_point.py
```

## 🚦 Run the VRChat Guide Agent

### Running the Agent (Web Interface)

Create a folder `frontend/`  under `experiments/agents/<agent_name>` and create a `app_*` file.

You can run the agent in a web interface by running:

**NOTE:** You should run the agent in the `frontend` directory to preserve the frontend assets.

For our agent:
```bash
cd src/vrchat_guide/frontend/
chainlit run app_vrchat_guide.py --port 8800
```

### Running the Agent (Text Mode)

You can also run the agent in text mode by running:

```bash
# Start the VRChat Guide Agent in text mode
python src/vrchat_guide/vrchatbot.py
```

### Running the Agent in VRChat

Finally, here is what you all are waiting for - running the agent in VRChat!

You can run the agent in VRChat by running:

```bash
# TODO: WORK IN PROGRESS
```

## 📖 Documentation

For detailed development instructions and documentation, please refer to:
- [Custom Agent Development Guide](https://github.com/stanford-oval/genie-worksheets)
- [Custom SUQL Database Setup Guide](https://github.com/stanford-oval/suql/blob/main/docs/install_source.md)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This project implements concepts from the paper ["Coding Reliable LLM-based Integrated Task and Knowledge Agents with GenieWorksheets"](https://arxiv.org/abs/2407.05674).

```
@article{genieworksheets,
  title={Coding Reliable LLM-based Integrated Task and Knowledge Agents with GenieWorksheets},
  author={Joshi, Harshit and Liu, Shicheng and Chen, James and Weigle, Robert and Lam, Monica S},
  journal={arXiv preprint arXiv:2407.05674},
  year={2024}
}
```

---
<div align="center">
Made with ❤️ for the VRChat community
</div>