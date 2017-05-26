# INFO2120 Assignment 3 Documentation
## Source code

### Installation and Usage
1. Download the ZIP file.
2. Make sure you have ``python3`` installed on your system. If not:
    1. Install python3: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    2. Open terminal (or powershell)
        * Make sure you can run ``python3``
        * Note: you may need to edit the 'environment variables'
3. Unzip the ZIP file.
4. Edit **config.ini** with your **pgAdmin** details!
5. Depending on your operating system:
    * Windows: open ``run.bat``
    * Mac: open ``run.command``
    * Unix/Linux/Terminal: run ``python3 main.py``
6. Experiment how it works
7. Your turn :)

### Main Important Files :

#### config.ini
* Edit this to have your database connection information
* user = your_unikey
* password = password for pgAdmin

#### database.py
* Sets up connections to the database
* Runs all the queries (you write)
* Has all the database functions
* Most of your work is done in here

#### routes.py
* Handles how the website runs
* You need to do some *slight* modifications to this file.

#### templates
* If you want to change the way anything looks - template files
* Take a look at the structure and how it works
* Understand what you need to do in **routes.py** in order to get everything working.

## What to look for
I've put in some nice *TODO* statements, detailing what you have to do. The **week 8** tutorial is a good place to start and look at what you need to do :) It's a good place to look if you're getting stuck or not sure what to start with.

## I want to do awesome stuff!
Honestly, the limitations lie with you, just make sure you're looking at the **marking criteria** and understanding where you are getting the marks.

## Help!? I don't understand any of this
* Like I said before, **week 8** tutorial (and lecture) are very very *very* helpful, so it would be a good place to start.
* Check out the Flask tutorial and documentation to understand how it all works: [http://flask.pocoo.org/docs/0.10/tutorial/](http://flask.pocoo.org/docs/0.10/tutorial/)
* Check out the pg8000 documentation: [https://pythonhosted.org/pg8000/quickstart.html](https://pythonhosted.org/pg8000/quickstart.html)

# Good luck :)
