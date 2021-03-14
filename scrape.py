#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re
import json
import requests
from bs4 import BeautifulSoup
import string
printable = set(string.printable)

import codecs, sys
#sys.stdout = codecs.getwriter("UTF-8")(sys.stdout)

from HashMap import HashTable

# this scrapes sis itu for all the course data.
# see data_spec.md for interpreting out_file.

# Use this to not send a request to sis_url everytime. Also gives us speed.
USE_CACHE = True
CACHE_DIR = "./cache/"
out_file="data.json"

# Create cache dir if not already exists
if not os.path.isdir(CACHE_DIR):
    os.makedirs(CACHE_DIR)

if USE_CACHE:
    print("Warning: Cache mode is active.")

sis_url="https://www.sis.itu.edu.tr/TR/ogrenci/ders-programi/ders-programi.php?seviye=LS"

# we need cookies and stuff, also pretend that we are firefox on windows
s = requests.Session()
headers = requests.utils.default_headers()
headers = {"Host": "www.sis.itu.edu.tr",
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.sis.itu.edu.tr/TR/ogrenci/ders-programi/ders-programi.php?seviye=LS",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://www.sis.itu.edu.tr",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-GPC": "1",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache"
                }
def getCoursesList():
    index_text = ""
    if USE_CACHE and os.path.isfile(CACHE_DIR+"index.html"):
        with open(CACHE_DIR+"index.html", "r") as f:
            index_text = "".join(f.readlines())
    else:
        index_text = requests.get(sis_url, headers=headers).text
        with open(CACHE_DIR+"index.html", "w+") as f:
            f.writelines(index_text)
            f.flush()
    soup = BeautifulSoup(index_text, "html.parser")
    undergradcourses_option = soup.find(attrs={"name": "derskodu"})
    undergradcourses = []
    for c in undergradcourses_option.children:
        try:
            undergradcourses.append(c.get("value"))
        except:
            pass
    return undergradcourses

def loadAllSections(ccode):
    course_text = ""
    if USE_CACHE and os.path.isfile(CACHE_DIR+ccode):
        with open(CACHE_DIR+ccode, "r") as f:
            course_text = "".join(f.readlines())
    else:
        course_text = requests.post(sis_url, headers=headers, data={"seviye": "LS", "derskodu": ccode, "B1": "G%F6ster"}).text
        with open(CACHE_DIR+ccode, "w+") as f:
            f.writelines(course_text)
            f.flush()
    soup = BeautifulSoup(course_text, "html.parser")
    allrows = soup.find_all("tr")
    allsections = []
    for r in allrows:
        ch = r.children
        section = {}
        section["CRN"] = next(ch).text
        section["Course Code"] = next(ch).text
        section["Course Title"] = next(ch).text
        section["Instructor"] = next(ch).text
        section["Building"] = next(ch).text
        # TODO Find a more elegant way to do this
        days = next(ch).text.split(" ")
        parsed_days = []
        for day in days:
            day = day.strip()
            day = "".join(list(filter(lambda x: x in printable, day)))
            if day == "" or day == "----":
                continue
            if day == "Pazartesi":
                day = 0
            elif day == "Sal":
                day = 1
            elif day == "aramba":
                day = 2
            elif day == "Perembe":
                day = 3
            elif day == "Cuma":
                day = 4
            elif day == "Cumartesi":
                day = 5
            elif day == "Pazar":
                day = 6
            else:
                print("Skipping day due to Day Error: %s" % day)
                #print("Assigning to sunday due to Day Error: " + day)
                #parsed_days.append(6)
                continue
            parsed_days.append(day)
        section["Day"] = parsed_days
        section["Time"] = next(ch).text
        section["Room"] = next(ch).text
        section["Capacity"] = next(ch).text
        section["Enrolled"] = next(ch).text
        allsections.append(section)
    return allsections

def getTimes(sec):
    times = []
    hours = sec["Time"].split(" ")
    for i, hh in enumerate(hours):
        if hh == "---- " or hh == "" or hh == "/ " or hh == "/":
            # TODO No time is specified. What to do?
            #times.append({"s": 0, "e": 0, "d": sec["Day"][i], "p": sec["Building"] + " " + sec["Room"]})
            continue
        h = hh.split("/")
        try:
            shour = int(str(h[0][0:2]))*60+int(str(h[0][2:4]))
            ehour = int(str(h[1][0:2]))*60+int(str(h[1][2:4]))
            times.append({"s": shour, "e": ehour, "d": sec["Day"][i], "p": sec["Building"] + " " + sec["Room"]})
        except ValueError:
            print("Error at hour parsing: " + hh)
            return times
    return times

courses = getCoursesList()
courses_data = []
for c in courses:
    if c == "":
        continue
    print("Loading courses of department %s" %c)
    sections = loadAllSections(c)
    alternatives = HashTable(len(sections))
    for i, s in enumerate(sections[2:]):
        times = getTimes(s)
        sectionCode = s["CRN"]    # ie. "20726"
        course = alternatives.get_val(s["Course Code"])
        if course != None:  # Append section to the course
            course["s"][sectionCode] = {"i": [s["Instructor"]], "c": [], "t": times, "a": int(s["Capacity"])-int(s["Enrolled"])}
        else:   # Create course
            course = {"n":  s["Course Code"], "c": s["Course Title"], "s": {}}
            course["s"][sectionCode] = {"i": [s["Instructor"]], "c": [], "t": times, "a": int(s["Capacity"])-int(s["Enrolled"])}
            alternatives.set_val(s["Course Code"], course)
    courses_data += alternatives.to_list()
json.dump(courses_data, open(out_file, "w+"))




