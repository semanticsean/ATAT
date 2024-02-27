
from flask import Flask, render_template, request, send_from_directory
import json
import os
import random


app = Flask(__name__)


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=8080)
