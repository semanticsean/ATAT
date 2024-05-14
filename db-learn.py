# db-learn.py
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import logging

# Ensure this environment variable is set correctly
# Replace 'postgres://' with 'postgresql://' if necessary
db_url = os.environ.get('DATABASE_URL', 'postgresql://localhost')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

# Configure logging
logging.basicConfig(filename='schema_and_data.log', level=logging.INFO)


def dump_schema_and_data(model_class, model_name):
    inspector = inspect(engine)
    table_name = model_class.__tablename__
    columns = inspector.get_columns(table_name)

    logging.info(f"Schema for {model_name}:")
    for column in columns:
        logging.info(f"- {column['name']}: {column['type']}")

    # Retrieve data snippets from the model
    data_snippets = session.query(model_class).limit(5).all()

    logging.info(f"\nData snippets for {model_name}:")
    for snippet in data_snippets:
        logging.info(snippet.__dict__)


def list_agents_for_user(user_id):
    # Retrieve the user by id
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        logging.info(f"No user found with id {user_id}")
        return

    # Check if agents_data is a list and use it directly
    agents = user.agents_data if isinstance(user.agents_data, list) else []

    logging.info(f"Agents for User {user_id}:")
    for agent in agents:
        agent_id = agent.get('id')
        agent_type = agent.get('agent_type',
                               'Unknown')  # Default type if not provided
        logging.info(f"Agent ID: {agent_id}, Agent Type: {agent_type}")


# Importing the models
from models import User, Timeframe, Agent

# Dump schema and data for models
model_classes = [User, Timeframe, Agent]
for model_class in model_classes:
    dump_schema_and_data(model_class, model_class.__name__)

# Example usage: List agents for a specific user
list_agents_for_user(62)

session.close()
