from app.doctors import  __init__
##entry point
from app import create_app
if __name__=='__main__':
    app=create_app("dev")


    app.run()
