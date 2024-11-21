# Clone the repository
git clone https://github.com/tianyhe/vrchat-guide.git
Set-Location vrchat-guide

# If submodules are not cloned
git submodule update --init --recursive

put all service_account.json, credentials.json etc file at their location as per the original README.md
AND
put llm_config.yaml at \SimulationSystem-VRCHAT path


# Create and activate virtual environment
uv venv
.\venv\Scripts\activate

# Install dependencies
uv sync
uv pip install -e ".[all]"

# Install SpaCy Model
python -m spacy download en_core_web_sm

# load env file
.env


For PostgreSQL setup in PowerShell:

# Launch psql
psql -U postgres

# Then run these SQL commands:
# CREATE DATABASE vrchat_events;
# CREATE ROLE select_user WITH PASSWORD 'select_user';
# GRANT SELECT ON ALL TABLES IN SCHEMA public TO select_user;
# ALTER ROLE select_user LOGIN;
# CREATE ROLE creator_role WITH PASSWORD 'creator_role';
# GRANT CREATE ON DATABASE vrchat_events TO creator_role;
# GRANT CREATE ON SCHEMA public TO creator_role;
# ALTER ROLE creator_role LOGIN;
# \q


{run all 4 scripts in wsl}:
if you encounter any error while running init_database.py or other,
go to powershell in your windows and run

an and check for
Ethernet adapter vEthernet (WSL (Hyper-V firewall)):

   Connection-specific DNS Suffix  . :
   Link-local IPv6 Address . . . . . : fe80::4449:e9:82e:e471%34
   IPv4 Address. . . . . . . . . . . : 172.28.192.1
   Subnet Mask . . . . . . . . . . . : 255.255.240.0
   Default Gateway . . . . . . . . . :

pick IPV4 address from here and change
host:{your IPV4 address} in init_database.py and in the entire codebase where you are defining host. (e.g. \scripts\db_sync.py, \packages\suql\src\suql\postgresconnection.py (something like this) etc)

For running services:
# Initialize database schema
python scripts/database/init_database.py

# Start Calendar Events Sync
python scripts/db_sync.py

# Start Embedding Server (new terminal)
python packages/suql/src/suql/faiss_embedding.py

# Start Free-text Server (new terminal)
python scripts/free_text_server.py



For running the agent:
# Web Interface
Set-Location src/vrchat_guide/frontend/
chainlit run app_vrchat_guide.py --port 8800

# Text Mode
python src/vrchat_guide/vrchatbot.py


# running integration:
Run two client on one machine (as you sent me in the video, but with two different accounts)
bring those two avatar's in same world (send friend request, accept, send invite, accept)

`cd \SimulationSystem-VRCHAT`
`python integration.py`
