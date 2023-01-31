import requests
import os
from bs4 import BeautifulSoup
import time
import logging
import gspread

DELAY_TIME = 60  # seconds
URL = 'https://www.t2c.fr/actualites-infos-trafic-par-ligne/ligne'

filehandle = open("null_content.html", encoding="ISO-8859-1", mode="r")
null_response_text = filehandle.read()
filehandle.close()

log = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"), format='%(asctime)s %(message)s')
log.info("Running Website Monitor")


def process_html(string):
    """Full website HTML to just the interesting part"""
    soup = BeautifulSoup(string, features="lxml")

    soup.prettify()  # make the html look good
    main_content_html = soup.find("div", {"class": "c-information__holder"})

    return str(main_content_html).replace('\r', '')


def tramIsWorkingRN():
    """Check if the website was updated"""
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36','Pragma': 'no-cache', 'Cache-Control': 'no-cache'}
    try:
        response = requests.get(URL, headers=headers)
    except requests.exceptions.RequestException as e:
        log.error(e)
        return False

    processed_response_html = process_html(response.text)

    if processed_response_html == null_response_text :
        return True
    else:
        return False


# GOOGLE SHEETS
gc = gspread.service_account()
sh = gc.open("T2C Tracker")
worksheet = sh.sheet1


def next_available_row(col_num):
    str_list = list(filter(None, worksheet.col_values(col_num)))
    return len(str_list)+1


class Outage:
    def __init__(self, start_time, HTML):
        self.row = next_available_row(9)
        self.id = self.row-1
        self.start_time = start_time
        self.end_time = None
        self.HTML = HTML


def updateGoogleSheet():
    """Update the Google Sheet time and state"""
    log.info("Updating Google Sheet")
    # update the state
    worksheet.update_cell(3, 7, previousStateTramWorkingRN)
    # update the time/date
    worksheet.update_cell(4, 7, time.strftime("%d/%m/%Y %H:%M:%S"))


def addOutageToGoogleSheets():
    """Starts or finishes an outage and updates the Google Sheet"""
    # update the count
    now = time.strftime("%d/%m/%Y")
    cell = worksheet.find(now)
    row = cell.row
    current_count = worksheet.cell(row, 3).value
    worksheet.update_cell(row, 3, int(current_count)+1)

    # add/modify the outage to the sheet
    if previousStateTramWorkingRN is True:
        outage = Outage(time.strftime("%d/%m/%Y %H:%M:%S"), processed_response_html)
        log.info("Adding outage to Google Sheets")
        worksheet.update_cell(outage.row, 9, outage.id)
        worksheet.update_cell(outage.row, 10, outage.start_time)
        worksheet.update_cell(outage.row, 14, outage.HTML)
        current_ids = worksheet.cell(row, 4).value
        worksheet.update_cell(row, 4, current_ids+","+str(outage.id))
    elif outage is not None:
        outage.end_time = time.strftime("%d/%m/%Y %H:%M:%S")
        log.info("Adding outage to Google Sheets")
        worksheet.update_cell(outage.row, 11, outage.end_time)
        current_ids = worksheet.cell(row, 5).value
        if outage.id not in current_ids:
            worksheet.update_cell(row, 5, outage.id)

outage=None
processed_response_html = process_html(null_response_text)
previousStateTramWorkingRN = tramIsWorkingRN()
updateGoogleSheet()

while True:
    if tramIsWorkingRN() == previousStateTramWorkingRN:
        log.info("No change")
    else:
        log.info("CHANGE DETECTED")
        addOutageToGoogleSheets()
        previousStateTramWorkingRN = tramIsWorkingRN()
        updateGoogleSheet()
    time.sleep(DELAY_TIME)
