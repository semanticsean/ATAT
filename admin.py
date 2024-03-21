from flask import Flask
from models import db, User
import os

app = Flask(__name__)

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
  app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace(
      "postgres://", "postgresql://", 1)
else:
  raise ValueError('Invalid or missing DATABASE_URL')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


def main():
  with app.app_context():
    users = User.query.all()
    print("Available users:")
    for index, user in enumerate(users, start=1):
      print(f"{index}. {user.username}")

    while True:
      user_choice = input("Enter the user ID (or 'q' to quit): ")
      if user_choice.lower() == 'q':
        break

      try:
        user_index = int(user_choice) - 1
        if user_index < 0 or user_index >= len(users):
          raise ValueError
      except ValueError:
        print("Invalid user ID. Please try again.")
        continue

      selected_user = users[user_index]
      print(f"Selected user: {selected_user.username}")
      print(f"Current credit balance: {selected_user.credits}")

      while True:
        update_choice = input(
            "Update credits? (Enter a number or 'q' to quit): ")
        if update_choice.lower() == 'q':
          break

        try:
          new_balance = int(update_choice)
          if new_balance < 0:
            raise ValueError
        except ValueError:
          print("Invalid input. Please enter a non-negative integer.")
          continue

        selected_user.credits = new_balance
        db.session.commit()
        print(
            f"Updated {selected_user.username}'s credit balance to {new_balance} credits."
        )
        break


if __name__ == '__main__':
  main()
