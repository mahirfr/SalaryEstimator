# SALARY ESTIMATOR

[Video Demo](https://youtu.be/F4wNGVRvPBk)

#### Description:
This is a niche project designed to help temporary workes (in France) calculate their salary.
The reasons for why it was made are explained in a youtube video for which the url is just above.
It's a simple website written in Python that uses Flask, SQLAlchemy(sqlite3), HTML & CSS, Bootstrap and a bit of JavaScript.

It has a website folder which stores the entire code for our website and it also has a main.py file that's not inside of the website folder.

###### main.py
Inside of this file is a tiny bit of code which just let's us run our website or our web server.
It imports the ``` create_app ``` from our __init__.py file in the website folder which we initialse as app and run it.

###### website/__init__.py
This file turns our website folder into a python package so that we can run the files in it automatically.
It contains our secret key (which will be left out for security purposes), our blueprints, creates our database, uses the flask login manager to get the id of the user who is logged in
using the imported models.py User table.

###### website/models.py
This file contains our three database tables which are User, Zone and Day.
In the User table 
we have the user's email,
password (not the actual password but its hash value, used from the imported werkzeug.security module),
id which is the primary key,
user's hourly_rate which is used to calculate the users salary, user's region (which will be used to check if the user was payed double if he worked a sunday which is only thecase for certain regions in France, this option will be available for the sites final version),
user's sundays column (which will keep count of the sundays the user worked necessary for calculating his salary, this is empty for now and will also be available for the sites final version),
meal column which is used to calcultate the users imposable meals which are given by the empolyer,
day and zone columns which contain the foreign key relationships of the two remaining tables.

In the Day table 
    we have an id as the table's primary key which is used to delete a given day's information if the user's input was incorrect, 
    date column which serves multiple purposes (on the client side, it's obvious to have a date on which they worked and our side it is used to calculate overtime pay by looking at which week it is and the end of month to give the user his monthy pay), 
    hours column which gives us the hours worked for the given date, 
    meal_qty column which tells us if the client was payed his meal for the day (it's automatically the case if they worked for more than 4 hours for that given day),
    user_id column which is the foreign key of the User table,
    zone_id column which is the foreign key of the Zone table.

In the Zone table
    we have the id as the table's primary key,
    km column which is used for the different pay parameters based on the distance traveled which are given by the employer,
    price column which represents the price for the kilometers traveled,
    user_id which is the foreign key of the User table,
    day column which is the relationship with the Day table.
* this table was initially pre-populated but that led to less personalisation and lesser accuracy when the pay was calculated given the uncertainty of the paramaters which are not the same
for the entire France and which can also be defined by the empoyer, so the choice was brought down to the client's entry's.

###### website/auth.py
In this file we have the authentication routes and the blueprint file definition.
Inscription route:
    where the user creates his account by entering his email, password and confirmation of the password
    when the information passes the security requirements the user gets added to the database and gets redirected to his profile.
Login route:
    where the user loggs in with his email and password
    if the information entered is incorrect the user gets a flashed message which tells the user to reenter their details
Logout route:
    the user can only access this route if they're already logged in (@login_required module from flask_login)
    the user gets logged out using the imported logout_user module from flask_login

###### website/utilities.py
In this file are just the predefined regions used for the templating language. 
Originally there were more than two which were used to calculate users zones, but the design was simplified and most of them served no purpose.
The two remaining regions were left because they are the only to pay double for a sunday worked.

###### website/views.py
This is the longest file in our website folder which contains most of our views (or url break-points).
Like the auth.py file it is defined as a blueprint and has routes.
Index route:
    the user doesn't need to be logged in to access this page
    it calculates the user salary with less accuracy than the detail route. 
    it's purpose is to give the client the ball park of the salary rather than a precise estimation.
    Once the user fills out the weekly hours the salary template is rendered where the user can see his estimation. 
Detail route: 
    the user needs to be logged in to access this page 
    it calculates the salary with very good precision.
    We insert the user's data into the db and calculate it by separating the dates into weeks and weeks into months.
    We treat the edge cases where the week is in two months, and if there was any overtime to be payed that overtime is passed into the next month.
    After filling the forms the user sumbits and the same page is rendered but with a populated table of months, how many hours the user worked that month, his IFM and ICP which only temporary workers get and the salary for that month.
Consultez route:
    In this route the user gets to see the information he entered for each date and delete it if they wish.
    A js table was taken from https://datatables.net/ in which the user can search by date for the day the user wants.
    The table can show 10, 25, 50 or 100 results at a time which is more esthetically pleasing than showing the user's input all at once.
Profile route:
    in this route the user gets to personalise his information.
    How much is his hourly rate, how much does he get paid for what distance and what it his imposable meal plan.
    All of this information can be found on the user's contract or work agreement.
    Once filled out the detail.html page is rendered.

###### website/static
This folder contains a tiny bit of css for the navbar, footer and some small details.

###### website/templates
This folder contains all of the html pages for the website.
The purpose of which is explained in views.py and auth.py.

It was a project I wanted to do for a long time and because of cs50 I finally had acquired the skills necessary to complete it !
Thanks cs50 <3