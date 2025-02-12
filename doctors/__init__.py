from flask import Blueprint

doctor_blueprint= Blueprint("doctor",__name__)
from app.doctors import views