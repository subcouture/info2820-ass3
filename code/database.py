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
    if 'database' not in config['DATABASE']:
        config['DATABASE']['database'] = config['DATABASE']['user']

    # Create a connection to the database
    connection = None
    try:
        # Parses the config file and connects using the connect string
        connection = pg8000.connect(database=config['DATABASE']['database'],
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
            if(cur.rowcount != 0): #if user is official
                member_type = ["official"]
            else:
                member_type = ["staff"]
        else:
            member_type = ["athlete"]


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

    connection = database_connect()
    if (connection is None):
        return None
    cur = connection.cursor()

    try:

        sql = """SELECT *
                 FROM public.member
                 WHERE member_id=%s"""
        cur.execute(sql,(member_id,))
        member = cur.fetchone()

        sql = """SELECT *
                 FROM public.Place
                 WHERE place_id=%s""" 
        cur.execute(sql,[member[5]])
        place_info = cur.fetchone()
    except:
        print("Error When Searching Accom Info")
        connection.close()
        cur.close()
        return None

    accom_rows = [place_info[1],place_info[4],place_info[3],place_info[2]]

    # Check what type of member we are
    if(mem_type == 'athlete'):

        # get the details for athletes
        # Member details [total events, total gold, total silver, total bronze, number of bookings]
        try: 
            sql = """SELECT 
                     (SELECT COUNT(*) FROM Participates WHERE athlete_id = %s) as total_event,
                     (SELECT COUNT(*) FROM Participates WHERE athlete_id = %s AND medal = 'G') as gold,
                     (SELECT COUNT(*) FROM Participates WHERE athlete_id = %s AND medal = 'S') as silver,
                     (SELECT COUNT(*) FROM Participates WHERE athlete_id = %s AND medal = 'B') as bronze,
                     (SELECT COUNT(*) FROM Booking WHERE booked_for = %s) as booking"""
                      
            cur.execute(sql,(member_id,member_id,member_id,member_id,member_id))
            details = cur.fetchone()
        except:
            print("Error When Searching Athlete Info")
            connection.close()
            cur.close()
            return None

        member_information_db = [details[0],details[1],details[2],details[3],details[4]]

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
        #test A000022388
        try:
            sql = """SELECT role,max(record.count) as max
                     FROM(SELECT role, COUNT(*) as count
                          FROM RunsEvent
                          WHERE member_id=%s
                          GROUP BY role) as record
                     GROUP BY role"""
            cur.execute(sql,(member_id,))
            role = cur.fetchone() #assume unqiue
            if(role is None):
                role = ["No role"] #prevent programing from crashing because unvalid example data
            
            sql = """SELECT
                     (SELECT COUNT(*) FROM RunsEvent WHERE member_id=%s) as total_event,
                     (SELECT COUNT(*) FROM Booking WHERE booked_for = %s) as bookings"""
            cur.execute(sql,(member_id,member_id))
            details = cur.fetchone()
        except:
            print("Error When getting official info")
            cur.close()
            connection.close()
            return None

        member_information_db = [role[0],details[0],details[1]]

        member_information = {
            'favourite_role' : member_information_db[0],
            'total_events' : member_information_db[1],
            'bookings': member_information_db[2]
        }
    else:

        # TODO get information for staff member
        # Staff = [number of bookings ]
        try:
            sql = """SELECT COUNT(*) FROM Booking WHERE booked_for=%s"""

            cur.execute(sql,(member_id,))
            details = cur.fetchone()
        except:
            print("Error When getting staff info")
            cur.close()
            connection.close()
            return None

        member_information_db =[details[0]]
        member_information = {'bookings': member_information_db[0]}

    cur.close()
    connection.close()
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

    connection = database_connect();
    if (connection is None):
        return False
    cur = connection.cursor(); #get cursor
    print(my_member_id, for_member, vehicle, date, hour, start_destination, end_destination)

    try:
        #check if member is a Staff
        sql = "SELECT * FROM public.Staff WHERE member_id=%s"
        cur.execute(sql,(my_member_id,))
        print("member is a staff: ",cur.rowcount)
        if (cur.rowcount == 0):
            return False
        #check member exists
        sql = "SELECT * FROM member WHERE member_id=%s"
        cur.execute(sql,(for_member,))
        print("member is exists:",cur.rowcount)
        if (cur.rowcount == 0):
            return False
        
        #get vehicle capacity
        sql = "SELECT capacity FROM public.Vehicle WHERE vehicle_code=%s"
        cur.execute(sql,(vehicle,))
        if (cur.rowcount == 0): #vehicle does not exits
            return False
        val = cur.fetchone()
        capacity = int(val[0])
        print("capacity is", capacity)
        
        #get num_booking on this vehicle at this time  BB62AC75
        time = date + " "  + hour + ":00:00"
        print(time)
        sql = """SELECT nbooked, journey_id FROM Journey JOIN place P1 ON(from_place = P1.place_id) JOIN place P2 On(to_place = P2.place_id)
               WHERE vehicle_code=%s AND depart_time=%s AND P1.place_name=%s AND P2.place_name=%s"""

        cur.execute(sql,(str(vehicle),str(time),str(start_destination),str(end_destination)))
        print(rowcount)
        if (cur.rowcount == 0): #no such journey
            return False
        val = cur.fetchone()
        nbooked = int(val[0])
        journey_id = val[1]
        print("nbooked is ",nbooked)
        print("journey_id is ",journey_id)
        
        if(nbooked > capacity): #if no space
            return False
        
        #then everything should be good to go
        try:
            sql = "INSERT INTO Booking VALUES(%s,%s,CURRENT_TIMESTAMP,%s);"
            cur.execute(sql,(member_id,my_member_id,journey_id))
            sql = "UPDATE Journey SET nbooked = nbooked + 1 WHERE vehicle_code = %s AND depart_time = %s"
            cur.execute(sql,(vehicle_code,time))
            connection.commit()
        except:
            print("cannot make the booking")
            connection.rollback()
            cur.close()
            connection.close() 
            return False
    except:
        print("Error when making a booking")
        cur.close()
        connection.close()
        return False

    cur.close()
    connection.close()
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

    #test account: A000040397 samurai
    try:
        connection = database_connect()
        if (connection is None):
            return None
        cur = connection.cursor()
        
        sql = """SELECT vehicle_code, 
                 TO_CHAR(EXTRACT(DAY FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(MONTH FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(YEAR FROM depart_time),'fm0000') as day,
                 TO_CHAR(EXTRACT(hour FROM depart_time),'fm00') || TO_CHAR(EXTRACT(minute FROM depart_time),'fm00')as time,
                 (SELECT place_name FROM public.Place WHERE place_id = to_place) as to_place,
                 (SELECT place_name FROM public.Place WHERE place_id = from_place) as from_place
                 FROM public.Journey JOIN public.Vehicle USING(vehicle_code) JOIN public.Place P1 ON(from_place = P1.place_id) JOIN public.Place P2 ON(to_place = P2.place_id) JOIN Booking USING(journey_id)
                 WHERE Booking.booked_for = %s
                 ORDER BY day,time,to_place,from_place,vehicle_code"""
        
        cur.execute(sql,(member_id,))
        lists = cur.fetchall()
        cur.close()
        connection.close()
    except:
        print("Error when searching bookings")
        cur.close()
        connection.close()
        return None
    
   #bookings_db = [
   #    [ 'BL4Z3D', '17/05/2017', '2100', 'SIT', 'Wentworth'],
   #    [ 'TR870R', '21/12/2020', '0600', 'Velodrome', 'Urbanest']
   #]
    bookings_db = lists
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

    #2017-12-13
    year = day[0:4]
    month = day[5:7]
    day = day[8:]

    try:
        connection = database_connect()
        if (connection is None):
            return None
        cur = connection.cursor()
        
        sql = """SELECT vehicle_code, 
                 TO_CHAR(EXTRACT(DAY FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(MONTH FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(YEAR FROM depart_time),'fm0000') as day,
                 TO_CHAR(EXTRACT(hour FROM depart_time),'fm00') || TO_CHAR(EXTRACT(minute FROM depart_time),'fm00')as time,
                 (SELECT place_name FROM public.Place WHERE place_id = to_place) as to_place,
                 (SELECT place_name FROM public.Place WHERE place_id = from_place) as from_place
                 FROM public.Journey JOIN public.Vehicle USING(vehicle_code) JOIN public.Place P1 ON(from_place = P1.place_id) JOIN public.Place P2 ON(to_place = P2.place_id) JOIN Booking USING(journey_id)
                 WHERE Booking.booked_for = %s
                 AND EXTRACT(YEAR FROM depart_time) = %s
                 AND EXTRACT(MONTH FROM depart_time) = %s
                 AND EXTRACT(day FROM depart_time) = %s
                 ORDER BY day,time,to_place,from_place,vehicle_code"""
        
        cur.execute(sql,(member_id,year,month,day))
        lists = cur.fetchall()
        cur.close()
        connection.close()
        print(lists)
    except:
        print("Error when searching bookings by day")
        cur.close()
        connection.close()
        return None



    bookings_db = lists

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
def get_booking(b_date, b_hour, vehicle, from_place, to_place, member_id):

    # TODO - fix up the row to get booking information
    # Get the information about a certain booking, including who booked etc.
    # It will include more detailed information

    #13/12/2017
    year = b_date[6:]
    month = b_date[3:5]
    day = b_date[0:2] 
    try:
        connection = database_connect()
        if (connection is None):
            return None
        cur = connection.cursor()
        

        #journey_id,booked_for is pm for booking
        #vehicle_Code, depart_time is pm for journey
        sql = """SELECT vehicle_code, 
                 ((SELECT given_names FROM Member WHERE member_id = booked_by) || ' ' ||  (SELECT family_name FROM Member WHERE member_id = booked_by)) as booked_by,
                 TO_CHAR(EXTRACT(DAY FROM when_booked),'fm00') || '/' || TO_CHAR(EXTRACT(MONTH FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(YEAR FROM depart_time),'fm0000') as when_booked
                 FROM Booking JOIN Journey USING(journey_id) join member ON (booked_by = member_id)
                 WHERE Booking.booked_for = %s
                 AND EXTRACT(YEAR FROM depart_time) = %s
                 AND EXTRACT(MONTH FROM depart_time) = %s
                 AND EXTRACT(day FROM depart_time) = %s
                 AND vehicle_code = %s"""
        
        cur.execute(sql,(member_id,year,month,day,vehicle))
        val = cur.fetchone()
        cur.close()
        connection.close()
    except:
        print("Error when searching booking detail")
        cur.close()
        connection.close()
        return None

    # Format:
    #   [vehicle, startday, starttime, to, from, booked_by (name of person), when booked]
    row = [val[0],b_date,b_hour,to_place,from_place,val[1],val[2]]

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

    connection = database_connect()
    if (connection is None):
        return None
    cur = connection.cursor()
    
    try:
        sql = "SELECT place_id FROM public.Place WHERE place_name=%s"
        cur.execute(sql,(from_place,))
        from_placeID = cur.fetchone()

        sql = "SELECT place_id FROM public.Place WHERE place_name=%s"
        cur.execute(sql,(to_place,))
        to_placeID = cur.fetchone()

        sql = """SELECT vehicle_code,
	TO_CHAR(EXTRACT(DAY FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(MONTH FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(YEAR FROM depart_time),'fm0000') as day, 
	TO_CHAR(EXTRACT(hour FROM depart_time),'fm00') || TO_CHAR(EXTRACT(minute FROM depart_time),'fm00')as time, 
	(SELECT place_name FROM public.Place WHERE place_id = %s) as to_place,

	(SELECT place_name FROM public.Place WHERE place_id = %s) as from_place,
	nbooked,capacity
                 FROM public.Journey JOIN public.Vehicle USING(vehicle_code) JOIN public.Place P1 ON(from_place = P1.place_id) JOIN public.Place P2 ON(to_place = P2.place_id)
                 WHERE from_place=%s and to_place=%s
                 ORDER BY day,time,to_place,from_place,vehicle_code"""
        cur.execute(sql,[to_placeID[0],from_placeID[0],from_placeID[0],to_placeID[0]])
        lists = cur.fetchall()
        cur.close()
        connection.close()
    except:
        cur.close()
        connection.close()
        print("Error when Searching for all journeys")
        return None
    
    # Format:
    # [
    #   [ vehicle, day, time, to, from, nbooked, vehicle_capacity],
    #   ...
    # ]
    #journeys_db = [
    #['TR470R', '21/12/2020', '0600', 'SIT', 'Wentworth', 7, 8]
    #]
    journeys_db = lists


    journeys = [{
        'vehicle': row[0],
        'start_day': row[1],
        'start_time': row[2],
        'to' : row[3],
        'from' : row[4],
        'booked' : row[5],
        'capacity' : row[6]
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

    connection = database_connect()
    if (connection is None):
        return None
    cur = connection.cursor()
    
    try:
        sql = "SELECT place_id FROM public.Place WHERE place_name=%s"
        cur.execute(sql,(from_place,))
        from_placeID = cur.fetchone()

        sql = "SELECT place_id FROM public.Place WHERE place_name=%s"
        cur.execute(sql,(to_place,))
        to_placeID = cur.fetchone()
        
        #2017-12-13
        year = int(journey_date[0:4])
        month = int(journey_date[5:7])
        day = int(journey_date[8:])
        
        print(year)
        print(month)
        print(day)
        sql = """SELECT vehicle_code,
	TO_CHAR(EXTRACT(DAY FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(MONTH FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(YEAR FROM depart_time),'fm0000') as day, 
	TO_CHAR(EXTRACT(hour FROM depart_time),'fm00') || TO_CHAR(EXTRACT(minute FROM depart_time),'fm00')as time, 
	(SELECT place_name FROM public.Place WHERE place_id = %s) as to_place,

	(SELECT place_name FROM public.Place WHERE place_id = %s) as from_place,
	nbooked,capacity
                 FROM public.Journey JOIN public.Vehicle USING(vehicle_code) JOIN public.Place P1 ON(from_place = P1.place_id) JOIN public.Place P2 ON(to_place = P2.place_id)
                 WHERE from_place=%s AND to_place=%s
                 AND EXTRACT(YEAR FROM depart_time) = %s
                 AND EXTRACT(MONTH FROM depart_time) = %s
                 AND EXTRACT(day FROM depart_time) = %s
                 ORDER BY day,time,to_place,from_place,vehicle_code"""
        cur.execute(sql,[to_placeID[0],from_placeID[0],from_placeID[0],to_placeID[0],year,month,day])
        lists = cur.fetchall()
        cur.close()
        connection.close()
    except:
        cur.close()
        connection.close()
        print("Error when Searching for journeys")
        return None

    # Format:
    # [
    #   [ vehicle, day, time, to, from, nbooked, vehicle_capacity],
    #   ...
    # ]
    journeys_db = lists    
    journeys = [{
        'vehicle': row[0],
        'start_day': row[1],
        'start_time': row[2],
        'to': row[3],
        'from': row[4],
        'booked' : row[5],
        'capacity' : row[6]

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
    # Chronologically order them by starA
    connection = database_connect()
    if (connection is None):
        return None
    cur = connection.cursor()

    try:
        sql = """SELECT event_name, 
                 TO_CHAR(EXTRACT(hour FROM event_start),'fm00') || TO_CHAR(EXTRACT(minute FROM event_start),'fm00') as time,
                 sport_name,place_name,event_gender,event_id
                 FROM Event JOIN Sport USING (sport_id) JOIN Place ON (sport_venue = place_id)
                 ORDER BY time
                 """
        cur.execute(sql)
        lists = cur.fetchall()
    except:
        print("Error when searching all events")
        cur.close()
        connection.close()
        return None

    cur.close()
    connection.close()
    # Format:
    # [
    #   [name, start, sport, venue_name]
    # ]
   #events_db = [
   #    ['200M Freestyle', '0800', 'Swimming', 'Olympic Swimming Pools', 'M', '123'],
   #    ['1km Women\'s Cycle', '1800', 'Cycling', 'Velodrome', 'W', '001']
   #]
    events_db = lists
    events = [{
        'name': row[0],
        'start': row[1],
        'sport': row[2],
        'venue': row[3],
        'gender': row[4],
        'event_id': row[5]
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

    connection = database_connect()
    if (connection is None):
        return None
    cur = connection.cursor()
    try:
        sql = """SELECT event_name, 
                 TO_CHAR(EXTRACT(hour FROM event_start),'fm00') || TO_CHAR(EXTRACT(minute FROM event_start),'fm00') as time,
                 sport_name,place_name,event_gender,event_id
                 FROM Event JOIN Sport USING (sport_id) JOIN Place ON (sport_venue = place_id)
                 WHERE sport_name = %s
                 ORDER BY time
                 """
        cur.execute(sql,(sportname,))
        lists = cur.fetchall()
    except:
        print("Error when searching the event")
        cur.close()
        connection.close()
        return None
    cur.close()
    connection.close()
    # Format:
    # [
    #   [name, start, sport, venue_name]
    # ]

    events_db = lists

    events = [{
        'name': row[0],
        'start': row[1],
        'sport': row[2],
        'venue': row[3],
        'gender': row[4],
        'event_id': row[5]
    } for row in events_db]

    return events

'''
Get all of the events a certain member is participating in.
'''
def get_events_for_member(member_id):  #did not find the html page

    # TODO - update the events_db variable to pull from the database
    # Return the data (NOTE: look at the information, requires more than a simple select. NOTE ALSO: ordering of columns)
    # It is a list of lists
    # Chronologically order them by start
    connection = database_connect()
    if (connection is None):
        return None
    cur = connection.cursor()
    try:
        sql = """SELECT event_name, 
                 TO_CHAR(EXTRACT(hour FROM event_start),'fm00') || TO_CHAR(EXTRACT(minute FROM event_start),'fm00') as time,
                 sport_name,place_name,event_gender
                 FROM Participates JOIN Event USING(event_id) JOIN Sport USING (sport_id) JOIN Place ON (sport_venue = place_id)
                 WHERE athlete_id = %s
                 ORDER BY time
                 """
        cur.execute(sql,(member_id,))
        lists = cur.fetchall()
    except:
        print("Error when searching athlete event") 
        cur.close()
        connection.close()
        return None
    cur.close()
    connection.close()

    # Format:
    # [
    #   [name, start, sport, venue_name]
    # ]

    events_db = lists

    events = [{
        'name': row[0],
        'start': row[1],
        'sport': row[2],
        'venue': row[3],
        'gender': row[4]
    } for row in events_db]

    return events

'''
Get event information for a certain event
'''
def event_details(event_id):
    # TODO - update the event_db to get that particular event
    # Return the data (NOTE: look at the information, requires more than a simple select. NOTE ALSO: ordering of columns)
    connection = database_connect()
    if (connection is None):
        return None
    cur = connection.cursor()
    try:
        sql = """SELECT event_name, 
                 TO_CHAR(EXTRACT(hour FROM event_start),'fm00') || TO_CHAR(EXTRACT(minute FROM event_start),'fm00') as time,
                 sport_name,place_name,event_gender
                 FROM  Event JOIN Sport USING (sport_id) JOIN Place ON (sport_venue = place_id)
                 WHERE event_id = %s
                 ORDER BY time
                 """
        cur.execute(sql,(event_id,))
        val = cur.fetchone()
    except:
        print("Error when searching event_details") 
        cur.close()
        connection.close()
        return None
    cur.close()
    connection.close()

    # Get the details for this event
    # Format:
    #   [name, start, sport, venue_name]
    event_db = val 


    event = {
        'name' : event_db[0],
        'start': event_db[1],
        'sport': event_db[2],
        'venue': event_db[3],
        'gender': event_db[4]
    }

    return event



#####################################################
## Results
#####################################################

'''
Get the results for a given event.
'''
def get_results_for_event(event_id):
    
    # TODO - update the results_db to get information from the database!
    # Return the data (NOTE: look at the information, requires more than a simple select. NOTE ALSO: ordering of columns)
    # This should return a list of who participated and the results.

    # This is a list of lists.
    # Order by ranking of medal, then by type (e.g. points/time/etc.)
    connection = database_connect()
    if (connection is None):
        return None
    cur = connection.cursor()

    try:
        sql = """(SELECT athlete_id, 'Gold' FROM Participates WHERE medal = 'G' AND event_id = %s)""" 
        cur.execute(sql,(event_id,))
        gold = cur.fetchone()
        
        sql = """(SELECT athlete_id, 'Silver' FROM Participates WHERE medal = 'S' AND event_id = %s)""" 
        cur.execute(sql,(event_id,))
        silver = cur.fetchone()

        sql = """(SELECT athlete_id, 'Bronze' FROM Participates WHERE medal = 'B' AND event_id = %s)""" 
        cur.execute(sql,(event_id,))
        bronze = cur.fetchone()

        sql = """SELECT athlete_id, ' ' FROM Participates WHERE medal is NULL AND event_id = %s"""
        cur.execute(sql,(event_id,))
        others = cur.fetchone()
        results = [gold,silver,bronze]
        while(others is not None):
            results.append(others)
            others = cur.fetchone()
    except:
        print("Error When Seaching for result")
        cur.close()
        connection.close()
        return None
    cur.close()
    connection.close()
    # Format:
    # [
    #   [member_id, result, medal],
    #   ...
    # ]

   #results_db = [
   #    ['1234567890', 'Gold'],
   #    ['8761287368', 'Silver'],
   #    ['1638712633', 'Bronze'],
   #    ['5873287436', ''],
   #    ['6328743234', '']
   #]
    results_db = results
    results =[{
        'member_id': row[0],
        'medal': row[1]
    } for row in results_db]

    return results


'''
Get all the officials that participated, and their positions.
'''
def get_all_officials(event_id):
    # TODO
    # Return the data (NOTE: look at the information, requires more than a simple select. NOTE ALSO: ordering of columns)
    # This should return a list of who participated and their role.

    # This is a list of lists.

    # [
    #   [member_id, role],
    #   ...
    # ]
    connection = database_connect()
    if (connection is None):
        return None
    cur = connection.cursor()

    try:
        sql = "SELECT member_id, role FROM RunsEvent WHERE event_id = %s"
        cur.execute(sql,(event_id,))
        lists = cur.fetchall()
    except:
        print("Error when searching for offical and their roles")
        cur.close()
        connection.close()
        return None
    cur.close()
    connection.close()


   #officials_db = [
   #    ['1234567890', 'Judge'],
   #    ['8761287368', 'Medal Holder'],
   #    ['1638712633', 'Random Bystander'],
   #    ['5873287436', 'Umbrella Holder'],
   #    ['6328743234', 'Marshall']
   #]

    officials_db = lists

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

