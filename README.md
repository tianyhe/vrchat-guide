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
- OpenAI API key

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/tianyhe/vrchat-guide.git
cd vrchat-guide

# Create and activate virtual environment
uv venv
source venv/bin/activate  # Unix
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
uv sync
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

# Initialize Schema
python scripts/database/init_database.py
```

### 4. Start Required Services

```bash
# Install spaCy model
python -m spacy download en_core_web_sm

# Start Embedding Server
python packages/suql/src/suql/faiss_embedding.py

# Start Free-text Server (in new terminal)
python scripts/free_text_server.py
```

## 🧪 Verify Installation

```bash
# Test dependencies
python tests/verify_install.py
python tests/test_dependencies.py

# Test database connection
python tests/test_db_connection.py

# Test entry point
python tests/test_entry_point.py
```

## 📖 Documentation

For detailed development instructions and API documentation, please refer to:
- [Development Guide](docs/development.md)
- [API Reference](docs/api/README.md)
- [Configuration Guide](docs/configuration.md)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This project implements concepts from the paper ["Coding Reliable LLM-based Integrated Task and Knowledge Agents with GenieWorksheets"](https://arxiv.org/abs/2407.05674).

---
<div align="center">
Made with ❤️ for the VRChat community
</div>