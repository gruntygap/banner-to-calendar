# banner-to-calendar
Uses resources from Banner to export student schedule to Google Calendar

Goes into a bethel account, then directs to banner, scrapes the term of choice for class info.

Then creates events for each class and puts them into a google calendar

Test link
https://banner.bethel.edu/prod8/bwskfshd.P_CrseSchdDetl?term_in=201851

We have to go to: https://banner.bethel.edu/prod8/bwskfshd.P_CrseSchdDetl
Then we take all the dates from the menu, and then once someone selects one. We grab the value and input it into the link on line 9.


https://developers.google.com/api-client-library/python/

https://developers.google.com/google-apps/calendar/quickstart/python#troubleshooting

https://developers.google.com/google-apps/calendar/create-events


# THIS REPO HAS BEEN ARCHIVED.
I used this tool for a few semesters before auth.bethel.edu changed.
It seems that bethel decided to go with a third party which uses generated tokens for each login.
Fancy javascript and the likes have probably broken this setup, which worked FLAWLESSLY.
There is a chance that I will visit this setup again, as beautifulSoup is the best html parser out there.

But for now, I will lay this project to sleep, in an archived form.

I hope to finish what I started with banner-to-calendar mark II. Check my Repos
