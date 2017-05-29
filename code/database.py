'''

syntax for database connections

conn = database_connect()
if(conn is None):
    return None
# Sets up the rows as a dictionary
cur = conn.cursor()
val = None
try:
    # Try getting all the information returned from the query
    # NOTE: column ordering is IMPORTANT
    cur.execute("""SELECT *
                    FROM event""")
    val = cur.fetchall()
except:
    # If there were any errors, we print something nice and return a NULL value
    print("Error fetching from database")

cur.close()                     # Close the cursor
conn.close()                    # Close the connection to the db
return val



'''



#!/usr/bin/env python3

from modules import pg8000
import configparser
import json


#####################################################
##  Database Connect
#####################################################

'''
Connects to the database using the connection string
'''
def database_connect():
    # Read the config file
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Create a connection to the database
    connection = None
    try:
        # Parses the config file and connects using the connect string
        connection = pg8000.connect(database=config['DATABASE']['user'],
                                    user=config['DATABASE']['user'],
                                    password=config['DATABASE']['password'],
                                    host=config['DATABASE']['host'])
    except pg8000.OperationalError as e:
        print("""Error, you haven't updated your config.ini or you have a bad
        connection, please try again. (Update your files first, then check
        internet connection)
        """)
        print(e)
    # return the connection to use
    return connection

#####################################################
##  Login
#####################################################

'''
Check that the users information exists in the database.

- True = return the user data
- False = return None
'''
def check_login(member_id, password):

    # Check if the user details are correct!
    # Return the relevant information (watch the order!)

    # member_id and password should be found in the table 'Member'
    # test account: A000030488 password

    # 1. create connection with DB, get cursor
    connection = database_connect();
    if (connection is None):
        return None;
    cur = connection.cursor(); #get cursor

    # 2. execute the SQL from DB
    try:
        # select member
        sql = """SELECT *
                 FROM public.member
                 WHERE member_id=%s AND pass_word=%s"""
        cur.execute(sql,(member_id,password))
        member = cur.fetchone()
        if (member is None):
            emptyList = {}  #return an empty list if incorrect name/password
            return emptyList 
        
        #select country name
        sql = """SELECT country_name
                 FROM public.Country
                 WHERE country_code=%s"""
        cur.execute(sql,[member[4]])
        country_name = cur.fetchone()
        
        #select residence
        sql = """SELECT place_name
                 FROM   public.place 
                 WHERE place_id=%s"""
        cur.execute(sql,[member[5]])
        residence = cur.fetchone()
        
        #check member type
        sql = """SELECT *
                 FROM public.Athlete
                 WHERE member_id=%s"""

        cur.execute(sql,(member_id,))
        if(cur.rowcount == 0): #if user is not athlete
            sql = """SELECT *
                     FROM public.Official
                     WHERE member_id=%s"""
            cur.execute(sql,(member_id,))
            if(cur.rowcount != 0): #if user is not official
                member_type = cur.fetchone()
            else:
                member_type = ["Staff"]
        else:
            member_type = cur.fetchone()

        cur.close()
        connection.close()
    except:
        #when reciving error
        print("Error When Login")
        cur.close();
        connection.close()
        return None

    # Dummy data - change rows to be useful!
    # FORMAT = [member_id, title, firstname, familyname, countryName, residence]
    # e.g. user_data = ['1141171337', 'Mr', 'Potato', 'Head', 'Australia', 'SIT']

    user_data = [member[0],member[1],member[3],member[2],country_name[0],residence[0]]
    # Get the member's type
    # e.g. user_type = ['athlete']
    user_type = [member_type[0]]

    tuples = {
            'member_id': user_data[0],
            'title': user_data[1],
            'first_name': user_data[2],
            'family_name': user_data[3],
            'country_name': user_data[4],
            'residence': user_data[5],
            'member_type': user_type[0]
        }

    return tuples


#####################################################
## Member Information
#####################################################

'''
Get the details for a member, including:
    - all the accommodation details,
    - information about their events
    - medals
    - bookings.

If they are an official, then they will have no medals, just a list of their roles.
'''
def member_details(member_id, mem_type):

    # TODO
    # Return all of the user details including subclass-specific details
    #   e.g. events participated, results.

    # TODO - Dummy Data (Try to keep the same format)
    # Accommodation [name, address, gps_lat, gps_long]
    accom_rows = ['SIT', '123 Some Street, Boulevard', '-33.887946', '151.192958']

    # Check what type of member we are
    if(mem_type == 'athlete'):
        # TODO get the details for athletes
        # Member details [total events, total gold, total silver, total bronze, number of bookings]
        member_information_db = [5, 2, 1, 2, 20]

        member_information = {
            'total_events': member_information_db[0],
            'gold': member_information_db[1],
            'silver': member_information_db[2],
            'bronze': member_information_db[3],
            'bookings': member_information_db[4]
        }
    elif(mem_type == 'official'):

        # TODO get the relevant information for an official
        # Official = [ Role with greatest count, total event count, number of bookings]
        member_information_db = ['Judge', 10, 20]

        member_information = {
            'favourite_role' : member_information_db[0],
            'total_events' : member_information_db[1],
            'bookings': member_information_db[2]
        }
    else:

        # TODO get information for staff member
        # Staff = [number of bookings ]
        member_information_db = [10]
        member_information = {'bookings': member_information_db[0]}

    accommodation_details = {
        'name': accom_rows[0],
        'address': accom_rows[1],
        'gps_lat': accom_rows[2],
        'gps_lon': accom_rows[3]
    }

    # Leave the return, this is being handled for marking/frontend.
    return {'accommodation': accommodation_details, 'member_details': member_information}

#####################################################
##  Booking (make, get all, get details)
#####################################################

'''
Make a booking for a member.
Only a staff type member should be able to do this ;)
Note: `my_member_id` = Staff ID (bookedby)
      `for_member` = member id that you are booking for
'''
def make_booking(my_member_id, for_member, vehicle, date, hour, start_destination, end_destination):

    # TODO - make a booking
    # Insert a new booking
    # Only a staff member should be able to do this!!
    # Make sure to check for:
    #       - If booking > capacity
    #       - Check the booking exists for that time/place from/to.
    #       - Update nbooked
    #       - Etc.
    # return False if booking was unsuccessful :)
    # We want to make sure we check this thoroughly
    # MUST BE A TRANSACTION ;)
    return True

'''
List all the bookings for a member
'''
def all_bookings(member_id):

    # TODO - fix up the bookings_db information
    # Get all the bookings for this member's ID
    # You might need to join a few things ;)
    # It will be a list of lists - e.g. your rows

    # Format:
    # [
    #    [ vehicle, startday, starttime, to, from ],
    #   ...
    # ]
    bookings_db = [
        [ 'BL4Z3D', '17/05/2017', '2100', 'SIT', 'Wentworth'],
        [ 'TR870R', '21/12/2020', '0600', 'Velodrome', 'Urbanest']
    ]

    bookings = [{
        'vehicle': row[0],
        'start_day': row[1],
        'start_time': row[2],
        'to': row[3],
        'from': row[4]
    } for row in bookings_db]

    return bookings

'''
List all the bookings for a member on a certain day
'''
def day_bookings(member_id, day):

    # TODO - fix up the bookings_db information
    # Get bookings for the member id for just one day
    # You might need to join a few things ;)
    # It will be a list of lists - e.g. your rows

    # Format:
    # [
    #    [ vehicle, startday, starttime, to, from ],
    #   ...
    # ]

    bookings_db = [
        [ 'BL4Z3D', '17/05/2017', '2100', 'SIT', 'Wentworth'],
    ]

    bookings = [{
        'vehicle': row[0],
        'start_day': row[1],
        'start_time': row[2],
        'to': row[3],
        'from': row[4]
    } for row in bookings_db]

    return bookings


'''
Get the booking information for a specific booking
'''
def get_booking(b_date, b_hour, vehicle, from_place, to_place):

    # TODO - fix up the row to get booking information
    # Get the information about a certain booking, including who booked etc.
    # It will include more detailed information

    # Format:
    #   [vehicle, startday, starttime, to, from, booked_by (name of person), when booked]
    row = ['TR870R', '21/12/2020', '0600', 'SIT', 'Wentworth', 'Mike', '21/12/2012']

    booking = {
        'vehicle': row[0],
        'start_day': row[1],
        'start_time': row[2],
        'to': row[3],
        'from': row[4],
        'booked_by': row[5],
        'whenbooked': row[6]
    }

    return booking

#####################################################
## Journeys
#####################################################

'''
List all the journeys between two places.
'''
def all_journeys(from_place, to_place):

    # TODO - get a list of all journeys between two places!
    # List all the journeys between two locations.
    # Should be chronologically ordered
    # It is a list of lists

    # Format:
    # [
    #   [ vehicle, day, time, to, from, nbooked, vehicle_capacity],
    #   ...
    # ]
    journeys_db = [
        ['TR470R', '21/12/2020', '0600', 'SIT', 'Wentworth', 7, 8]
    ]

    journeys = [{
        'vehicle': row[0],
        'start_day': row[1],
        'start_time': row[2],
        'to' : row[3],
        'from' : row[4]
    } for row in journeys_db]

    return journeys


'''
Get all of the journeys for a given day, from and to a selected place.
'''
def get_day_journeys(from_place, to_place, journey_date):

    # TODO - update the journeys_db variable to get information from the database about this journey!
    # List all the journeys between two locations.
    # Should be chronologically ordered
    # It is a list of lists

    # Format:
    # [
    #   [ vehicle, day, time, to, from, nbooked, vehicle_capacity],
    #   ...
    # ]
    journeys_db = [
        ['TR470R', '21/12/2020', '0600', 'SIT', 'Wentworth', 7, 8]
    ]

    journeys = [{
        'vehicle': row[0],
        'start_day': row[1],
        'start_time': row[2],
        'to': row[3],
        'from': row[4]
    } for row in journeys_db]

    return journeys



#####################################################
## Events
#####################################################

'''
List all the events running in the olympics
'''
def all_events():

    # TODO - update the events_db to get all events
    # Get all the events that are running.
    # Return the data (NOTE: look at the information, requires more than a simple select. NOTE ALSO: ordering of columns)
    # It is a list of lists
    # Chronologically order them by start

    # Format:
    # [
    #   [name, start, sport, venue_name]
    # ]
    events_db = [
        ['200M Freestyle', '0800', 'Swimming', 'Olympic Swimming Pools'],
        ['1km Women\'s Cycle', '1800', 'Cycling', 'Velodrome']
    ]

    events = [{
        'name': row[0],
        'start': row[1],
        'sport': row[2],
        'venue': row[3],
    } for row in events_db]

    return events

'''
Get all the events for a certain sport - list it in order of start
'''
def all_events_sport(sportname):

    # TODO - update the events_db to get all events for a particular sport
    # Get all events for sport name.
    # Return the data (NOTE: look at the information, requires more than a simple select. NOTE ALSO: ordering of columns)
    # It is a list of lists
    # Chronologically order them by start

    # Format:
    # [
    #   [name, start, sport, venue_name]
    # ]

    events_db = [
        ['1km Women\'s Cycle', '1800', 'Cycling', 'Velodrome'],
        ['1km Men\'s Cycle', '1920', 'Cycling', 'Velodrome']
    ]

    events = [{
        'name': row[0],
        'start': row[1],
        'sport': row[2],
        'venue': row[3],
    } for row in events_db]

    return events

'''
Get all of the events a certain member is participating in.
'''
def get_events_for_member(member_id):

    # TODO - update the events_db variable to pull from the database
    # Return the data (NOTE: look at the information, requires more than a simple select. NOTE ALSO: ordering of columns)
    # It is a list of lists
    # Chronologically order them by start

    # Format:
    # [
    #   [name, start, sport, venue_name]
    # ]

    events_db = [
        ['1km Women\'s Cycle', '1800', 'Cycling', 'Velodrome'],
        ['1km Men\'s Cycle', '1920', 'Cycling', 'Velodrome']

    ]

    events = [{
        'name': row[0],
        'start': row[1],
        'sport': row[2],
        'venue': row[3],
    } for row in events_db]

    return events

'''
Get event information for a certain event
'''
def event_details(eventname):
    # TODO - update the event_db to get that particular event
    # Get all events for sport name.
    # Return the data (NOTE: look at the information, requires more than a simple select. NOTE ALSO: ordering of columns)
    # It is a list of lists
    # Chronologically order them by start

    # Format:
    #   [name, start, sport, venue_name]

    event_db = ['1km Women\'s Cycle', '1800', 'Cycling', 'Velodrome']


    event = {
        'name' : event_db[0],
        'start': event_db[1],
        'sport': event_db[2],
        'venue': event_db[3]
    }

    return event



#####################################################
## Results
#####################################################

'''
Get the results for a given event.
'''
def get_results_for_event(event_name):

    # TODO - update the results_db to get information from the database!
    # Return the data (NOTE: look at the information, requires more than a simple select. NOTE ALSO: ordering of columns)
    # This should return a list of who participated and the results.

    # This is a list of lists.
    # Order by ranking of medal, then by type (e.g. points/time/etc.)

    # Format:
    # [
    #   [member_id, result, medal],
    #   ...
    # ]

    results_db = [
        ['1234567890', '10pts', 'Gold'],
        ['8761287368', '8pts', 'Silver'],
        ['1638712633', '5pts', 'Bronze'],
        ['5873287436', '4pts', ''],
        ['6328743234', '4pts', '']
    ]

    results =[{
        'member_id': row[0],
        'result': row[1],
        'medal': row[2]
    } for row in results_db]

    return results

'''
Get all the officials that participated, and their positions.
'''
def get_all_officials(event_name):
    # TODO
    # Return the data (NOTE: look at the information, requires more than a simple select. NOTE ALSO: ordering of columns)
    # This should return a list of who participated and their role.

    # This is a list of lists.

    # [
    #   [member_id, role],
    #   ...
    # ]


    officials_db = [
        ['1234567890', 'Judge'],
        ['8761287368', 'Medal Holder'],
        ['1638712633', 'Random Bystander'],
        ['5873287436', 'Umbrella Holder'],
        ['6328743234', 'Marshall']
    ]

    officials = [{
        'member_id': row[0],
        'role': row[1]
    } for row in officials_db]


    return officials

# =================================================================
# =================================================================

#  FOR MARKING PURPOSES ONLY
#  DO NOT CHANGE

def to_json(fn_name, ret_val):
    return {'function': fn_name, 'res': json.dumps(ret_val)}

# =================================================================
# =================================================================
