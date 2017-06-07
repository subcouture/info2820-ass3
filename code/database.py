#!/usr/bin/env python3

from modules import pg8000
import configparser
import json

#####################################################
##  Database Connect https://www.tutorialspoint.com/postgresql/postgresql_limit_clause.htm
## https://www.tutorialspoint.com/postgresql/postgresql_privileges.htm
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
        login = """CREATE OR REPLACE FUNCTION login(id CHAR(10),ps CHAR(20))
                 RETURNS TABLE(
                        member_id   char(10),
                        title	VARCHAR(4),
                        family_name     VARCHAR(30),
                        given_names	VARCHAR(30),
                        country_code	CHAR(3),
                        accommodation	INT,
                        pass_word VARCHAR(20)
                 ) AS $$
                 BEGIN
                 RETURN QUERY(
                  SELECT * FROM member WHERE member.member_id=id AND member.pass_word=ps
                 );
                 END;
                 $$ LANGUAGE plpgsql;"""

        cur.execute(login);

        sql = "SELECT * FROM login(%s,%s)"
        cur.execute(sql,(member_id,password));
        if(cur.rowcount == 0):
            return None
        member = cur.fetchone()

        getCountry = """CREATE OR REPLACE FUNCTION getCountry(code CHAR(3))
                 RETURNS TABLE(
                        country_name VARCHAR(40)
                 ) AS $$
                 BEGIN
                 RETURN QUERY(
                  SELECT Country.country_name FROM public.Country WHERE Country.country_code=code
                 );
                 END;
                 $$ LANGUAGE plpgsql;"""

        cur.execute(getCountry);

        #select country name
        sql = "SELECT * FROM getCountry(%s)"
        cur.execute(sql,[member[4]])
        country_name = cur.fetchone()

        #select residence
        getPlace = """CREATE OR REPLACE FUNCTION getPlace(id INT)
                      RETURNS TABLE(
                                place_id INT,
                                place_name 	VARCHAR(80),
                                gps_long	REAL,
                                gps_lat	REAL,
                                address	VARCHAR(200),
                                located_in	INT
                      ) AS $$
                      BEGIN
                      RETURN QUERY(
                        SELECT * FROM public.place WHERE place.place_id = id
                      );
                      END;
                      $$ LANGUAGE plpgsql;"""
        cur.execute(getPlace)
        sql = "SELECT * FROM getPlace(%s)"
        cur.execute(sql,[member[5]])
        val = cur.fetchone()
        residence = val[1]
        #check member type
        getAthlete = """CREATE OR REPLACE FUNCTION getAthlete(id CHAR(10))
                     RETURNS TABLE(
                        member_id char(10)
                     ) AS $$
                     BEGIN
                     RETURN QUERY(
                        SELECT * FROM Athlete WHERE Athlete.member_id = id
                     );
                     END;
                     $$ LANGUAGE plpgsql;"""
        getOfficial = """CREATE OR REPLACE FUNCTION getOfficial(id CHAR(10))
                     RETURNS TABLE(
                        member_id char(10)
                     ) AS $$
                     BEGIN
                     RETURN QUERY(
                        SELECT * FROM Official WHERE Official.member_id = id
                     );
                     END;
                     $$ LANGUAGE plpgsql;"""
        cur.execute(getAthlete)
        cur.execute(getOfficial)
        sql = "SELECT * FROM getAthlete(%s)"
        cur.execute(sql,(member_id,));
        if(cur.rowcount == 0): #if user is not athlete
            sql = "SELECT * FROM getOfficial(%s)"
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
        #print("Error When Login")
        cur.close();
        connection.close()
        return None

    # Dummy data - change rows to be useful!
    # FORMAT = [member_id, title, firstname, familyname, countryName, residence]
    # e.g. user_data = ['1141171337', 'Mr', 'Potato', 'Head', 'Australia', 'SIT']

    user_data = [member[0],member[1],member[3],member[2],country_name[0],residence]
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
        getMember = """CREATE OR REPLACE FUNCTION getMember(id CHAR(10))
                     RETURNS TABLE(
                        member_id   char(10),
                        title	VARCHAR(4),
                        family_name     VARCHAR(30),
                        given_names	VARCHAR(30),
                        country_code	CHAR(3),
                        accommodation	INT,
                        pass_word VARCHAR(20)
                     ) AS $$
                     BEGIN
                     RETURN QUERY(
                        SELECT * FROM Member WHERE Member.member_id = id
                     );
                     END;
                     $$ LANGUAGE plpgsql;"""
        cur.execute(getMember)
        sql = """SELECT * FROM getMember(%s)"""
        cur.execute(sql,(member_id,))
        member = cur.fetchone()

        sql = "SELECT * FROM getPlace(%s)"
        cur.execute(sql,[member[5]])
        place_info = cur.fetchone()
    except:
        #print("Error When Searching Accom Info")
        connection.close()
        cur.close()
        return None

    accom_rows = [place_info[1],place_info[4],place_info[3],place_info[2]]

    # Check what type of member we are
    if(mem_type == 'athlete'):

        # get the details for athletes
        # Member details [total events, total gold, total silver, total bronze, number of bookings]
        try:
            getAthleteInfo = """CREATE OR REPLACE FUNCTION getAthleteInfo(id BIGINT)
                                RETURNS TABLE(
                                    total_event BIGINT,
                                    gold BIGINT,
                                    silver BIGINT,
                                    bronze BIGINT,
                                    nbooked BIGINT
                                ) AS $$
                                BEGIN
                                RETURN QUERY(
                                  SELECT
                                 (SELECT COUNT(*) FROM Participates WHERE athlete_id = id) +
                                 (SELECT COUNT(*) FROM TeamMember WHERE athlete_id = id) as total_event,

                                 (SELECT COUNT(*) FROM Participates WHERE athlete_id = id AND medal = 'G')  +
                                 (SELECT COUNT(*) FROM TeamMember JOIN Team USING(event_id) WHERE athlete = id AND medal = 'G')as gold,
                                 (SELECT COUNT(*) FROM Participates WHERE athlete_id = id AND medal = 'S')  +
                                 (SELECT COUNT(*) FROM TeamMember JOIN Team USING(event_id) WHERE athlete = id AND medal = 'S')as silver,
                                 (SELECT COUNT(*) FROM Participates WHERE athlete_id = id AND medal = 'B')  +
                                 (SELECT COUNT(*) FROM TeamMember JOIN Team USING(event_id) WHERE athlete = id AND medal = 'B')as bronze,
                                 (SELECT COUNT(*) FROM Booking WHERE booked_for = id) as booking
                                );
                                END;
                                $$ LANGUAGE plpgsql;"""
            cur.execute(getAthleteInfo)
            sql = "SELECT * FROM getAthleteInfo(%s)"
            cur.execute(sql,(member_id,))
            details = cur.fetchone()
        except:
            #print("Error When Searching Athlete Info")
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
            favRole = """CREATE OR REPLACE FUNCTION favRole(id CHAR(10))
                         RETURNS TABLE(
                            role VARCHAR(10),
                            max BIGINT
                         ) AS $$
                         BEGIN
                         RETURN QUERY(
                                SELECT record.role,max(record.count) as max
                                FROM(SELECT R.role, COUNT(*) as count
                                FROM RunsEvent R
                                WHERE R.member_id=id
                                GROUP BY R.role) as record
                                GROUP BY record.role
                         );
                         END;
                         $$ LANGUAGE plpgsql;"""
            cur.execute(favRole);
            sql = "SELECT * FROM favRole(%s)"
            cur.execute(sql,(member_id,))
            role = cur.fetchone() #assume unqiue
            if(role is None):
                role = ["No role"] #prevent programing from crashing because unvalid example data

            getOfficialInfo = """CREATE OR REPLACE FUNCTION getOfficialInfo(id CHAR(10))
                                 RETURNS TABLE(
                                    total_event BIGINT,
                                    nbooked BIGINT
                                 ) AS $$
                                 BEGIN
                                 RETURN QUERY(
                                      SELECT
                                     (SELECT COUNT(*) FROM RunsEvent WHERE member_id=id) as total_event,
                                     (SELECT COUNT(*) FROM Booking WHERE booked_for = id) as bookings
                                 );
                                 END;
                                 $$ LANGUAGE plpgsql;"""
            cur.execute(getOfficialInfo)
            sql = "SELECT * FROM getOfficialInfo(%s)"
            cur.execute(sql,(member_id,))
            details = cur.fetchone()
        except:
            #print("Error When getting official info")
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

        try:
            getStaffInfo =  """CREATE OR REPLACE FUNCTION getStaffInfo(id CHAR(10))
                                 RETURNS TABLE(
                                    nbooked BIGINT
                                 ) AS $$
                                 BEGIN
                                 RETURN QUERY(
                                      SELECT
                                     (SELECT COUNT(*) FROM Booking WHERE booked_for = id) as bookings
                                 );
                                 END;
                                 $$ LANGUAGE plpgsql;"""
            cur.execute(getStaffInfo)
            sql = "SELECT COUNT(*) FROM getStaffInfo(%s)"
            cur.execute(sql,(member_id,))
            details = cur.fetchone()
        except:
            #print("Error When getting staff info")
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

    connection = database_connect();
    if (connection is None):
        return False
    cur = connection.cursor(); #get cursor
    #print(my_member_id, for_member, vehicle, date, hour, start_destination, end_destination)

    try:
        #check if member is a Staff
        bookingValid = """CREATE OR REPLACE FUNCTION bookingValid(id CHAR(10),m_id CHAR(10),v_code CHAR(8), d_time TIMESTAMP, start_p VARCHAR(20), end_p VARCHAR(20))
                          RETURNS TABLE(
                            staff BIGINT,
                            member BIGINT,
                            capacity INT,
                            _nbooked INT,
                            _journey_id int
                          ) AS $$
                          BEGIN
                          RETURN QUERY(
                          SELECT
                          (SELECT count(*) FROM public.Staff WHERE member_id=id),
                          (SELECT count(*) FROM member WHERE member_id = m_id),
                          (SELECT vehicle.capacity FROM public.vehicle WHERE vehicle_code = v_code),
                          (SELECT nbooked FROM Journey JOIN place P1 ON(from_place = P1.place_id)
                          JOIN place P2 On(to_place = P2.place_id)
                          WHERE vehicle_code = v_code AND depart_time = d_time AND P1.place_name = start_p AND P2.place_name = end_p),
                          (SELECT journey_id FROM Journey JOIN place P1 ON(from_place = P1.place_id)
                          JOIN place P2 On(to_place = P2.place_id)
                          WHERE vehicle_code = v_code AND depart_time = d_time AND P1.place_name = start_p AND P2.place_name = end_p)
                          );
                          END;
                          $$ LANGUAGE plpgsql;
                          """
        cur.execute(bookingValid)

        time = date + " "  + hour + ":00:00"
        #print(time)
        sql = "SELECT * FROM bookingValid(%s,%s,%s,%s,%s,%s)"
        cur.execute(sql,(my_member_id,for_member,vehicle,time,start_destination,end_destination))
        val = cur.fetchone()
        for i  in val:
            if val[i] is None:
                return False
        nbooked = val[3]
        capacity = val[2]
        journey_id = val[4]
        if(nbooked > capacity): #if no space
            return False

        #data for testing
        #129;"2017-05-30 13:30:00";573;561;"AY91AN39";16;"2017-05-30 14:00:00"
        #INSERT INTO journey VALUES (129, '2017-05-30 13:30:00', 573, 561, 'AY91AN39', 16, '2017-05-30 14:00:00');

        #then everything should be good to go
        makeBooking = """CREATE OR REPLACE FUNCTION public.makebooking(id character varying,my_id character varying,j_id integer,)
                        RETURNS integer AS
                        $BODY$
                         BEGIN
                         INSERT INTO Booking VALUES(id,my_id,CURRENT_TIMESTAMP,j_id);
                         UPDATE Journey SET nbooked =nbooked + 1 WHERE journey_id = j_id;
                         RETURN 0;
                         END;
                         $BODY$
                         LANGUAGE plpgsql VOLATILE;"""
        cur.execute(makeBooking)
        sql = "SELECT makeBooking(%s,%s,%s)"
        cur.execute(sql,(for_member,my_member_id,journey_id))
    except:
        #print("Error when making a booking")
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


    #test account: A000040397 samurai
    try:
        connection = database_connect()
        if (connection is None):
            return None
        cur = connection.cursor()

        allBookings = """CREATE OR REPLACE FUNCTION allBookings(id CHAR(10))
                         RETURNS TABLE(
                            v_code CHAR(8),
                            _day text,
                            _time text,
                            place_s VARCHAR(80),
                            place_e VARCHAR(80)
                         ) AS $$
                         BEGIN
                         RETURN QUERY(
                          SELECT vehicle_code,
                         TO_CHAR(EXTRACT(DAY FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(MONTH FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(YEAR FROM depart_time),'fm0000') as day,
                         TO_CHAR(EXTRACT(hour FROM depart_time),'fm00') || TO_CHAR(EXTRACT(minute FROM depart_time),'fm00')as time,
                         (SELECT place_name FROM public.Place WHERE place_id = to_place) as to_place,
                         (SELECT place_name FROM public.Place WHERE place_id = from_place) as from_place
                         FROM public.Journey JOIN public.Vehicle USING(vehicle_code) JOIN public.Place P1 ON(from_place = P1.place_id) JOIN public.Place P2 ON(to_place = P2.place_id) JOIN Booking USING(journey_id)
                         WHERE Booking.booked_for = id
                         ORDER BY day,time,to_place,from_place,vehicle_code
                         );
                         END;
                         $$ LANGUAGE plpgsql;"""
        cur.execute(allBookings)
        sql = "SELECT * FROM allBookings(%s)"
        cur.execute(sql,(member_id,))
        lists = cur.fetchall()
        cur.close()
        connection.close()
    except:
        #print("Error when searching bookings")
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
        dayBookings = """CREATE OR REPLACE FUNCTION dayBookings(id CHAR(10), year CHAR(10), month CHAR(10), day CHAR(10))
                         RETURNS TABLE (
                           _v_code CHAR(8),
                           __day text,
                           __time text,
                           _place_s VARCHAR(80),
                           _place_e VARCHAR(80)
                         ) AS $$
                         BEGIN
                         RETURN QUERY(
                            SELECT * FROM allBookings(id)
                            WHERE _day = (day || '/' || month || '/' || year)
                            ORDER BY _day, _time, place_s,place_e,v_code
                         );
                         END;
                         $$ LANGUAGE plpgsql;"""
        cur.execute(dayBookings)
        sql = "SELECT * FROM dayBookings(%s,%s,%s,%s)"
        cur.execute(sql,(member_id,year,month,day))
        lists = cur.fetchall()
        cur.close()
        connection.close()
        #print(lists)
    except:
        #print("Error when searching bookings by day")
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
    print(b_date,b_hour)
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
        getBookings = """CREATE OR REPLACE FUNCTION getBookings(id CHAR(10), year CHAR(10), month CHAR(10), day CHAR(10),code CHAR(10))
                         RETURNS TABLE(
                            v_code CHAR(8),
                            name text,
                            _when_booked text
                         ) AS $$
                         BEGIN
                         RETURN QUERY(
                             SELECT vehicle_code,
                             ((SELECT given_names FROM Member WHERE member_id = booked_by) || ' ' ||  (SELECT family_name FROM Member WHERE member_id = booked_by)) as booked_by,
                             TO_CHAR(EXTRACT(DAY FROM when_booked),'fm00') || '/' || TO_CHAR(EXTRACT(MONTH FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(YEAR FROM depart_time),'fm0000') as when_booked
                             FROM Booking JOIN Journey USING(journey_id) join member ON (booked_by = member_id)
                             WHERE Booking.booked_for = id
                             AND TO_CHAR(EXTRACT(DAY FROM depart_time),'fm00') = day
                             AND TO_CHAR(EXTRACT(year FROM depart_time),'fm0000') = year
                             AND TO_CHAR(EXTRACT(month FROM depart_time),'fm00')= month
                             AND vehicle_code = code
                         );
                         END;
                         $$ LANGUAGE plpgsql;"""

        cur.execute(getBookings)
        sql = "SELECT * FROM getBookings(%s,%s,%s,%s,%s)"
        cur.execute(sql,(member_id,year,month,day,vehicle))
        val = cur.fetchone()
        cur.close()
        connection.close()
    except:
        #print("Error when searching booking detail")
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


def all_journeys_recursive(from_location, to_location):

    connection = database_connect()
    if (connection is None):
        return None
    cur = connection.cursor()

    try:
        sql = "SELECT location_id FROM public.location WHERE name=%s"
        cur.execute(sql,(from_location,))
        from_locationID = cur.fetchone()

        sql = "SELECT location_id FROM public.location WHERE name=%s"
        cur.execute(sql,(to_location,))
        to_locationID = cur.fetchone()

        sql = """

                SELECT vehicle_code,

                TO_CHAR(EXTRACT(DAY FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(MONTH FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(YEAR FROM depart_time),'fm0000') as day,
                TO_CHAR(EXTRACT(hour FROM depart_time),'fm00') || TO_CHAR(EXTRACT(minute FROM depart_time),'fm00')as time,

                (P1.place_name) as to_place,


                (P2.place_name) as from_place,

                nbooked,capacity

                FROM public.Journey JOIN public.Vehicle USING(vehicle_code) JOIN

                (WITH RECURSIVE parent AS (
                SELECT location_id, name
                FROM location
                WHERE location_id = %s
            ), tree AS (
                SELECT x.place_name, x.place_id, x.located_in, parent.name
                FROM place x
                INNER JOIN parent ON x.located_in = parent.location_id
                UNION ALL
                (SELECT y.place_name, y.place_id, y.located_in, z.name
                FROM place y INNER JOIN location z on y.located_in = z.location_id
                INNER JOIN tree t ON z.name = t.place_name
                WHERE y.place_name NOT IN (SELECT t.place_name)
                )
                )
                SELECT *
                FROM tree)
                P1 ON(journey.from_location = P1.place_id) JOIN
                (WITH RECURSIVE parent AS (
                SELECT location_id, name
                FROM location
                WHERE location_id = %s
            ), tree AS (
                SELECT x.place_name, x.place_id, x.located_in, parent.name
                FROM place x
                INNER JOIN parent ON x.located_in = parent.location_id
                UNION ALL
                (SELECT y.place_name, y.place_id, y.located_in, z.name
                FROM place y INNER JOIN location z on y.located_in = z.location_id
                INNER JOIN tree t ON z.name = t.place_name
                WHERE y.place_name NOT IN (SELECT t.place_name)
                )
                )
                SELECT *
                FROM tree)
                P2 ON(journey.to_location = P2.place_id)

                ORDER BY day,time,to_place,from_from, vehicle_code

              """

        cur.execute(sql,(to_locationID[0],from_locationID[0]))
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
        'to': row[3],
        'from': row[4],
        'booked' : row[5],
        'capacity' : row[6]
    } for row in journeys_db]

    return journeys

def get_day_journeys_recursive(from_place, to_place, journey_date):

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
        sql = "SELECT * FROM getPlace(%s)"
        cur.execute(sql,(from_place,))
        from_placeID = cur.fetchone()

        sql = "SELECT * FROM getPlace(%s)"
        cur.execute(sql,(to_place,))
        to_placeID = cur.fetchone()

        allJourneys = """CREATE OR REPLACE FUNCTION allJourneys(t_place CHAR(80),f_place CHAR(80))
                         RETURNS TABLE(
                            v_code CHAR(8),
                            _day TEXT,
                            _time TEXT,
                            place_s CHAR(80),
                            place_e CHAR(80),
                            _nbooked INT,
                            _capacity INT
                         ) AS $$
                         BEGIN
                         RETURN QUERY(
                              SELECT vehicle_code,
                    TO_CHAR(EXTRACT(DAY FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(MONTH FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(YEAR FROM depart_time),'fm0000') as day,
                    TO_CHAR(EXTRACT(hour FROM depart_time),'fm00') || TO_CHAR(EXTRACT(minute FROM depart_time),'fm00')as time,
                    (SELECT place_name FROM public.Place WHERE place_id = t_place) as to_place,

                    (SELECT place_name FROM public.Place WHERE place_id = f_place) as from_place,
                    nbooked,capacity
                             FROM public.Journey JOIN public.Vehicle USING(vehicle_code) JOIN public.Place P1 ON(from_place = P1.place_id) JOIN public.Place P2 ON(to_place = P2.place_id)
                             WHERE from_place= f_place AND to_place= t_place
                             ORDER BY day DESC,time DESC,to_place,from_place,vehicle_code
                         );
                         END;
                         $$ LANGUAGE plpgsql; """
        cur.execute(allJourneys)
        cur.execute(sql,[to_placeID[0],from_placeID[0]])
        lists = cur.fetchall()
        cur.close()
        connection.close()
    except:
        cur.close()
        connection.close()
        #print("Error when Searching for all journeys")
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
        sql = "SELECT * FROM getPlace(%s)"
        cur.execute(sql,(from_place,))
        from_placeID = cur.fetchone()

        sql = "SELECT * FROM getPlace(%s)"
        cur.execute(sql,(to_place,))
        to_placeID = cur.fetchone()

        #2017-12-13
        year = int(journey_date[0:4])
        month = int(journey_date[5:7])
        day = int(journey_date[8:])

        #print(year)
        #print(month)
        #print(day)
        getJourneys = """CREATE OR REPLACE FUNCTION getJourneys(t_place CHAR(80),f_place CHAR(80), year CHAR(10), month CHAR(10), day CHAR(10))
                         RETURNS TABLE(
                            v_code CHAR(8),
                            _day TEXT,
                            _time TEXT,
                            place_s CHAR(80),
                            place_e CHAR(80),
                            _nbooked INT,
                            _capacity INT
                         ) AS $$
                         BEGIN
                         RETURN QUERY(
                              SELECT vehicle_code,
                    TO_CHAR(EXTRACT(DAY FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(MONTH FROM depart_time),'fm00') || '/' || TO_CHAR(EXTRACT(YEAR FROM depart_time),'fm0000') as day,
                    TO_CHAR(EXTRACT(hour FROM depart_time),'fm00') || TO_CHAR(EXTRACT(minute FROM depart_time),'fm00')as time,
                    (SELECT place_name FROM public.Place WHERE place_id = t_place) as to_place,

                    (SELECT place_name FROM public.Place WHERE place_id = f_place) as from_place,
                    nbooked,capacity
                             FROM public.Journey JOIN public.Vehicle USING(vehicle_code) JOIN public.Place P1 ON(from_place = P1.place_id) JOIN public.Place P2 ON(to_place = P2.place_id)
                             WHERE from_place= f_place AND to_place= t_place
                             AND TO_CHAR(EXTRACT(DAY FROM depart_time),'fm00') = day
                             AND TO_CHAR(EXTRACT(year FROM depart_time),'fm0000') = year
                             AND TO_CHAR(EXTRACT(month FROM depart_time),'fm00')= month
                             ORDER BY day DESC,time DESC,to_place,from_place,vehicle_code
                         );
                         END;
                         $$ LANGUAGE plpgsql; """
        cur.execute(getJourneys)
        sql = "SELECT * FROM getJourneys(%s,%s,%s,%s,%s)"
        cur.execute(sql,[to_placeID[0],from_placeID[0],year,month,day])
        lists = cur.fetchall()
        cur.close()
        connection.close()
    except:
        cur.close()
        connection.close()
        #print("Error when Searching for journeys")
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
        getEvents = """CREATE OR REPLACE FUNCTION getEvents()
                        RETURNS TABLE(
                            _event_name VARCHAR(50),
                            _time TEXT,
                            _sport_name VARCHAR(20),
                            _place_name VARCHAR(80),
                            _event_gender CHAR,
                            _event_id INT
                        ) AS $$
                        BEGIN
                        RETURN QUERY(
                            SELECT event_name,
                         TO_CHAR(EXTRACT(hour FROM event_start),'fm00') || TO_CHAR(EXTRACT(minute FROM event_start),'fm00') as time,
                         sport_name,place_name,event_gender,event_id
                         FROM Event JOIN Sport USING (sport_id) JOIN Place ON (sport_venue = place_id)
                         ORDER BY time
                        );
                        END;
                        $$ LANGUAGE plpgsql;"""
        cur.execute(getEvents)
        sql = "SELECT * FROM getEvents()"
        cur.execute(sql)
        lists = cur.fetchall()
    except:
        #print("Error when searching all events")
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

        getEventsSports = """CREATE OR REPLACE FUNCTION getEventsSports(name CHAR(50))
                        RETURNS TABLE(
                            _event_name VARCHAR(50),
                            _time TEXT,
                            _sport_name VARCHAR(20),
                            _place_name VARCHAR(80),
                            _event_gender CHAR,
                            _event_id INT
                        ) AS $$
                        BEGIN
                        RETURN QUERY(
                            SELECT event_name,
                         TO_CHAR(EXTRACT(hour FROM event_start),'fm00') || TO_CHAR(EXTRACT(minute FROM event_start),'fm00') as time,
                         sport_name,place_name,event_gender,event_id
                         FROM Event JOIN Sport USING (sport_id) JOIN Place ON (sport_venue = place_id)
                         WHERE sport_name = name
                         ORDER BY time
                        );
                        END;
                        $$ LANGUAGE plpgsql;"""
        cur.execute(getEventsSports);
        sql = "SELECT * FROM getEventsSports(%s)"
        cur.execute(sql,(sportname,))
        lists = cur.fetchall()
    except:
        #print("Error when searching the event")
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
        getEventsMember = """CREATE OR REPLACE FUNCTION getEventsMember(id CHAR(10))
                        RETURNS TABLE(
                            _event_name VARCHAR(50),
                            _time TEXT,
                            _sport_name VARCHAR(20),
                            _place_name VARCHAR(80),
                            _event_gender CHAR,
                            _event_id INT
                        ) AS $$
                        BEGIN
                        RETURN QUERY(
                            SELECT event_name,
                         TO_CHAR(EXTRACT(hour FROM event_start),'fm00') || TO_CHAR(EXTRACT(minute FROM event_start),'fm00') as time,
                         sport_name,place_name,event_gender,event_id
                         FROM Participates JOIN Event USING(event_id) JOIN Sport USING (sport_id) JOIN Place ON (sport_venue = place_id)
                         WHERE athlete_id = %s
                         ORDER BY time
                        );
                        END;
                        $$ LANGUAGE plpgsql;"""
        cur.execute(getEventsMember)
        sql = "SELECT * FROM getEventsMember(%s)"
        cur.execute(sql,(member_id,))
        lists = cur.fetchall()
    except:
        #print("Error when searching athlete event")
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
        getEventsDetails = """CREATE OR REPLACE FUNCTION getEventsDetails(id CHAR(10))
                        RETURNS TABLE(
                            _event_name VARCHAR(50),
                            _time TEXT,
                            _sport_name VARCHAR(20),
                            _place_name VARCHAR(80),
                            _event_gender CHAR,
                            _event_id INT
                        ) AS $$
                        BEGIN
                        RETURN QUERY(
                            SELECT event_name,
                         TO_CHAR(EXTRACT(hour FROM event_start),'fm00') || TO_CHAR(EXTRACT(minute FROM event_start),'fm00') as time,
                         sport_name,place_name,event_gender,event_id
                         FROM Event JOIN Sport USING (sport_id) JOIN Place ON (sport_venue = place_id)
                         WHERE event_id = CAST(id AS INT)
                         ORDER BY time
                        );
                        END;
                        $$ LANGUAGE plpgsql;"""
        cur.execute(getEventsDetails)
        sql = "SELECT * FROM getEventsDetails(%s)"
        cur.execute(sql,(event_id,))
        val = cur.fetchone()
    except:
        #print("Error when searching event_details")
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
        getResults = """CREATE OR REPLACE FUNCTION getResults(id CHAR(10))
                        RETURNS TABLE(
                            _athlete_id CHAR(10),
                            results TEXT
                        ) AS $$
                        BEGIN
                        RETURN QUERY(
                                    SELECT athlete_id, CASE
                                    WHEN medal = 'G' THEN 'Gold'
                                    WHEN medal = 'S' THEN 'Silver'
                                    WHEN medal = 'B' THEN 'Bronze'
                                    ELSE ''
                                    END as rank
                                    FROM Participates JOIN event USING (event_id)
                                    WHERE event_id = CAST(id AS INT)
                                    ORDER BY
                                            CASE medal
                                            WHEN'G' THEN 1
                                            WHEN'S' THEN 2
                                            WHEN'B' THEN 3
                                            ELSE 4
                                            END, result_type
                        );
                        END;
                        $$ LANGUAGE plpgsql;"""

        getTeamResults = """CREATE OR REPLACE FUNCTION getTeamResults(id CHAR(10))
                            RETURNS TABLE(
                                _team_name VARCHAR(20),
                                result TEXT
                            )AS $$
                            BEGIN
                            RETURN QUERY(
                                    SELECT team_name, CASE
                                    WHEN medal = 'G' THEN 'Gold'
                                    WHEN medal = 'S' THEN 'Silver'
                                    WHEN medal = 'B' THEN 'Bronze'
                                    ELSE ''
                                    END as rank
                                    FROM Team JOIN event USING (event_id)
                                    WHERE event_id = CAST(id AS INT)
                                    ORDER BY
                                            CASE medal
                                            WHEN'G' THEN 1
                                            WHEN'S' THEN 2
                                            WHEN'B' THEN 3
                                            ELSE 4
                                            END, result_type
                            );
                            END;
                            $$ LANGUAGE plpgsql;"""
        cur.execute(getTeamResults)
        cur.execute(getResults)
        sql = "SELECT * FROM getResults(%s)"
        cur.execute(sql,(event_id,))
        if (cur.rowcount == 0): # This is a team event
            sql = "SELECT * FROM getTeamResults(%s)"
            cur.execute(sql,(event_id,))
        results = cur.fetchall()
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
    #   ..
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
        getAllOfficial = """CREATE OR REPLACE FUNCTION getAllOfficial(id CHAR(10))
                            RETURNS TABLE(
                                _id CHAR(10),
                                _role VARCHAR(10)
                            ) AS $$
                            BEGIN
                            RETURN QUERY(
                                SELECT member_id, role FROM RunsEvent WHERE event_id = CAST(id AS INT)
                            );
                            END;
                            $$ LANGUAGE plpgsql;"""
        cur.execute(getAllOfficial)
        sql = "SELECT * FROM getAllOfficial(%s)"
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
