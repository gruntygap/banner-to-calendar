from __future__ import print_function
import httplib2
import os
import cookielib
import mechanize
from bs4 import BeautifulSoup
import getpass


from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Banner to Calendar'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_banner_credentials(user, password):
    jar = cookielib.FileCookieJar("cookies")
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    browser.set_cookiejar(jar)
    browser.open('https://auth.bethel.edu/cas/login')
    browser.select_form(nr=0)  # check yoursite forms to match the correct number
    browser['username'] = user  # use the proper input type=text name
    browser['password'] = password  # use the proper input type=password name
    browser.submit()
    # return jar
    browser.open('https://www.bethel.edu/its/banner/ssb')
    # Change the line below so it will allow for selection of a term.
    response = browser.open('https://banner.bethel.edu/prod8/bwskfshd.P_CrseSchdDetl?term_in=201851')
    return response.read()


# Parses the Day of the Week (Ex. MWF = [Monday, Wednesday, Friday])
def parse_dotw(rand):
    days = []
    chars = list(rand)
    for letter in chars:
        if letter == "M":
            days.append('MO')
        if letter == "T":
            days.append('TU')
        if letter == "W":
            days.append('WE')
        if letter == "R":
            days.append('TH')
        if letter == "F":
            days.append('FR')
    return days


def main():
    # First gets the class data from banner
    # html = get_banner_credentials(raw_input("enter banner username: "), raw_input("enter banner password: "))
    html = get_banner_credentials(raw_input("enter banner username: "), getpass.getpass("enter banner password: "))
    soup = BeautifulSoup(html, 'html.parser')
    all_classes = soup.find('div', class_="pagebodydiv")
    all_tables = all_classes.find_all('table', 'datadisplaytable')
    # Table part is the number that the current table is on, part 1 is just scraping for a title
    # part 2 is scraping for the class times, days of class, location of the class, and date range for the class
    table_part = 1
    new_class = Class()
    classes = []
    for table in all_tables:
        print(table_part)
        if table_part == 1:
            table_part = 2
            title = table.find('caption', class_='captiontext')
            new_class.class_name = title.string
        elif table_part == 2:
            table_part = 1
            nothing = table.find('tr')
            info_table = nothing.find_next('tr').find_all('td')
            counter = 1
            for data in info_table:
                # Parse class times
                if counter == 2:
                    time_range = data.string.split(' - ')
                    new_class.class_start = datetime.datetime.strptime(time_range[0], "%I:%M %p").time()
                    new_class.class_end = datetime.datetime.strptime(time_range[1], "%I:%M %p").time()
                # Parse MTWRF
                if counter == 3:
                    new_class.class_days = parse_dotw(data.string)
                # Parse Location
                if counter == 4:
                    new_class.class_location = data.string
                # Parse Date Range
                if counter == 5:
                    date_range = data.string.split(' - ')
                    new_class.class_date_start = datetime.datetime.strptime(date_range[0], "%b %d, %Y")
                    new_class.class_date_end = datetime.datetime.strptime(date_range[1], "%b %d, %Y")


                counter = counter + 1
            # Adds the class to the classes array
            classes.append(new_class)
            # Resets the temp Class
            new_class = Class()

    """Shows basic usage of the Google Calendar API.

        Creates a Google Calendar API service object and outputs a list of the next
        10 events on the user's calendar.
        """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

    calendar_list_entry = service.calendarList().get(calendarId='primary').execute()

    print(calendar_list_entry['summary'])
    print()
    print(" -- Adding Classes to Calendar -- ")
    for class_ in classes:
        print(class_.class_name)
        print(class_.class_location)
        start = datetime.datetime.combine(class_.class_date_start, class_.class_start)
        end = datetime.datetime.combine(class_.class_date_start, class_.class_end)
        date_start = class_.class_date_start.strftime('%Y%m%dT000000Z')
        until = class_.class_date_end.strftime("%Y%m%dT000000Z")
        days = ""
        count = 1
        for day in class_.class_days:
            if len(class_.class_days) == count:
                days = days + day
            else:
                days = days + day + ","
            count = count + 1

        event = {
            "summary": class_.class_name,
            "location": class_.class_location,
            "description": "",
            "start": {
                "dateTime": start.strftime("%Y-%m-%dT%H:%M:%S-06:00"),
                "timeZone": "America/Chicago",
            },
            "end": {
                "dateTime": end.strftime("%Y-%m-%dT%H:%M:%S-06:00"),
                "timeZone": "America/Chicago",
            },
            "recurrence": [
                "RRULE:FREQ=WEEKLY;BYDAY="+days+";UNTIL="+until+";"
            ],
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))


class Class:
    def __init__(self):
        self.class_name = "default"
        self.class_start = "default"
        self.class_end = "default"
        self.class_days = "default"
        self.class_location = "default"
        self.class_date_start = "default"
        self.class_date_end = "default"

    @property
    def class_name(self):
        return self.class_name

    @class_name.setter
    def class_name(self, value):
        self.class_name = value

    @property
    def class_location(self):
        return self.class_location

    @class_location.setter
    def class_location(self, value):
        self.class_location = value

    @property
    def class_days(self):
        return self.class_days

    @class_days.setter
    def class_days(self, value):
        self.class_days = value

    @property
    def class_start(self):
        return self.class_start

    @class_start.setter
    def class_start(self, value):
        self.class_start = value

    @property
    def class_end(self):
        return self.class_end

    @class_end.setter
    def class_end(self, value):
        self.class_end = value

    @property
    def class_date_start(self):
        return self.class_date_start

    @class_date_start.setter
    def class_date_start(self, value):
        self.class_date_start = value

    @property
    def class_date_end(self):
        return self.class_date_end

    @class_date_end.setter
    def class_date_end(self, value):
        self.class_date_end = value


if __name__ == '__main__':
    main()
