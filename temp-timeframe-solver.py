import logging
import json
from models import db, User, Timeframe
from abe_gpt import summarize_process_agents
from abe import app

# Configure logging
logging.basicConfig(filename='timeframe_summary_debug.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def test_timeframe_summary_workflow():
    with app.app_context():
        logging.info("Starting timeframe summary workflow test")

        # Create a test user
        test_user = User(username='test_user', email='test@example.com')
        test_user.set_password('password')
        db.session.add(test_user)
        db.session.commit()
        logging.info(f"Created test user with ID: {test_user.id}")

        # Create a test timeframe
        test_timeframe = Timeframe(name='Test Timeframe', user_id=test_user.id, agents_data='[]', images_data='{}', thumbnail_images_data='{}')
        db.session.add(test_timeframe)
        db.session.commit()
        logging.info(f"Created test timeframe with ID: {test_timeframe.id}")

        # Generate a test payload for summarize_process_agents
        test_payload = {
            "agents_data": [],
            "instructions": {},
            "timeframe_name": "Test Timeframe"
        }

        try:
            # Call summarize_process_agents with the test payload and user
            summarize_process_agents(test_timeframe, test_payload, test_user)
            db.session.commit()
            logging.info("Called summarize_process_agents function")

            # Retrieve the updated test timeframe from the database
            updated_test_timeframe = Timeframe.query.get(test_timeframe.id)
            logging.info(f"Retrieved updated test timeframe with ID: {updated_test_timeframe.id}")

            # Log the generated summary
            logging.info(f"Generated summary: {updated_test_timeframe.summary}")

            # Verify if the summary is not None
            if updated_test_timeframe.summary is None:
                logging.error("Summary is None after calling summarize_process_agents")
            else:
                logging.info("Summary is not None after calling summarize_process_agents")

            # Simulate the retrieval of timeframes in the timeframes route
            test_user_timeframes = test_user.timeframes
            logging.info(f"Retrieved {len(test_user_timeframes)} timeframes for the test user")

            # Iterate over the test user's timeframes and log the summary
            for timeframe in test_user_timeframes:
                logging.info(f"Timeframe {timeframe.id} summary: {timeframe.summary}")

                # Verify if the summary is not None
                if timeframe.summary is None:
                    logging.error(f"Summary is None for Timeframe {timeframe.id}")
                else:
                    logging.info(f"Summary is not None for Timeframe {timeframe.id}")

        except Exception as e:
            logging.exception("An error occurred during the timeframe summary workflow test")

        finally:
            # Clean up the test data
            db.session.delete(test_timeframe)
            db.session.delete(test_user)
            db.session.commit()
            logging.info("Cleaned up test data")

        logging.info("Timeframe summary workflow test completed")

# Run the test
test_timeframe_summary_workflow()