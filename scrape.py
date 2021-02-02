#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, re
import json
import requests
from bs4 import BeautifulSoup
import string
printable = set(string.printable)

import codecs, sys
sys.stdout = codecs.getwriter("UTF-8")(sys.stdout)

# this scrapes sis itu for all the course data.
# see data_spec.md for interpreting out_file.

out_file="data.json"

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
    index_text = requests.get(sis_url, headers=headers)
    soup = BeautifulSoup(index_text.text, "html.parser")
    undergradcourses_option = soup.find(attrs={"name": "derskodu"})
    undergradcourses = []
    for c in undergradcourses_option.children:
        try:
            undergradcourses.append(c.get("value"))
        except:
            pass
    return undergradcourses

def loadAllSections(ccode):
    course_text = requests.post(sis_url, headers=headers, data={"seviye": "LS", "derskodu": ccode, "B1": "G%F6ster"})
    soup = BeautifulSoup(course_text.text, "html.parser")
    allrows = soup.find_all("tr")
    allsections = []
    for r in allrows:
        ch = r.children
        section = {}
        section["CRN"] = ch.next().text
        section["Course Code"] = ch.next().text
        ch.next()  # Skip
        section["Instructor"] = ch.next().text
        section["Building"] = ch.next().text
        # TODO Find a more elegant way to do this
        days = ch.next().text.split(" ")
        parsed_days = []
        for day in days:
            day = day.strip()
            day = filter(lambda x: x in printable, day)
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
                print "Assigning to sunday due to Day Error: " + day
                parsed_days.append(6)
                continue
            parsed_days.append(day)
        section["Day"] = parsed_days
        section["Time"] = ch.next().text
        section["Room"] = ch.next().text
        section["Capacity"] = ch.next().text
        section["Enrolled"] = ch.next().text
        allsections.append(section)
    return allsections

def getTimes(sec):
    times = []
    hours = sec["Time"].split("\n")
    for i, hh in enumerate(hours):
        if hh == "---- " or hh == "" or hh == "/ ":
            times.append({"s": 0, "e": 0, "d": sec["Day"][i], "p": sec["Building"] + " " + sec["Room"]})
            continue
        h = hh.split("/")
        try:
            shour = int(str(h[0][0:2]))*60+int(str(h[0][2:4]))
            ehour = int(str(h[1][0:2]))*60+int(str(h[1][2:4]))
            times.append({"s": shour, "e": ehour, "d": sec["Day"][i], "p": sec["Building"] + " " + sec["Room"]})
        except ValueError:
            print "Error at hour parsing: " + hh
            return times
    return times

#courses = getCoursesList()
courses = json.load(open("all.json", "r"))
courses_data = []
for c in courses[1:10]: # TODO Parse all
    print "Loading sections of course %s" %c
    sections = loadAllSections(c)
    course = {"n":  c, "c": c, "s": {}}
    for i, s in enumerate(sections[2:]):
        times = getTimes(s)
        course["s"][c+" "+s["CRN"]] = {"i": [s["Instructor"]], "c": [], "t": times} # TODO
    courses_data.append(course)
    #break
json.dump(courses_data, open(out_file, "w"))



