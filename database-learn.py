import base64
from io import BytesIO
from PIL import Image
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import logging

# Configure logging
logging.basicConfig(filename='database_learn.log', level=logging.INFO)

# Create a connection to the database
engine = create_engine('sqlite:///example.db')
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class Timeframe(Base):
    __tablename__ = 'timeframes'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    summary = Column(Text)
    image_data = Column(Text)
    thumbnail_image_data = Column(Text)

# Create the tables in the database
Base.metadata.create_all(engine)

def save_image_data(timeframe_id, image_data, thumbnail_data):
    try:
        timeframe = session.query(Timeframe).get(timeframe_id)
        if timeframe:
            # Convert image data to base64 and store in the database
            timeframe.image_data = base64.b64encode(image_data).decode('utf-8')
            timeframe.thumbnail_image_data = base64.b64encode(thumbnail_data).decode('utf-8')
            session.commit()
            logging.info(f"Image data saved successfully for Timeframe ID: {timeframe_id}")
        else:
            logging.error(f"Timeframe with ID {timeframe_id} not found.")
    except Exception as e:
        session.rollback()
        logging.error(f"Error occurred while saving image data: {str(e)}")

def get_image_data(timeframe_id):
    try:
        timeframe = session.query(Timeframe).get(timeframe_id)
        if timeframe:
            # Retrieve image data from the database and decode from base64
            image_data = base64.b64decode(timeframe.image_data)
            thumbnail_data = base64.b64decode(timeframe.thumbnail_image_data)
            logging.info(f"Image data retrieved successfully for Timeframe ID: {timeframe_id}")
            return image_data, thumbnail_data
        else:
            logging.error(f"Timeframe with ID {timeframe_id} not found.")
    except Exception as e:
        logging.error(f"Error occurred while retrieving image data: {str(e)}")

# Example usage
timeframe_id = 1
timeframe_name = "Test Timeframe"
summary = "This is a test timeframe summary."

# Create a new timeframe
new_timeframe = Timeframe(id=timeframe_id, name=timeframe_name, summary=summary)
session.add(new_timeframe)
session.commit()

# Generate example image and thumbnail data
image = Image.new('RGB', (800, 600), color='red')
thumbnail = image.copy()
thumbnail.thumbnail((200, 200))

# Convert image and thumbnail to bytes
image_buffer = BytesIO()
image.save(image_buffer, format='PNG')
image_data = image_buffer.getvalue()

thumbnail_buffer = BytesIO()
thumbnail.save(thumbnail_buffer, format='PNG')
thumbnail_data = thumbnail_buffer.getvalue()

# Save image data to the database
save_image_data(timeframe_id, image_data, thumbnail_data)

# Retrieve image data from the database
retrieved_image_data, retrieved_thumbnail_data = get_image_data(timeframe_id)

# Verify the retrieved image data
retrieved_image = Image.open(BytesIO(retrieved_image_data))
retrieved_thumbnail = Image.open(BytesIO(retrieved_thumbnail_data))

logging.info(f"Retrieved image size: {retrieved_image.size}")
logging.info(f"Retrieved thumbnail size: {retrieved_thumbnail.size}")