import requests
import os
from bs4 import BeautifulSoup
import time
import logging

DELAY_TIME = 60 # seconds
URL = 'https://www.t2c.fr/actualites-infos-trafic-par-ligne/ligne-a'



filehandle = open("null_content.html", 'r')
null_response_text = filehandle.read() 
filehandle.close()

log = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"), format='%(asctime)s %(message)s')
log.info("Running Website Monitor")

def process_html(string):
    soup = BeautifulSoup(string, features="lxml")

    # make the html look good
    soup.prettify()

    # keep only the main content
    main = soup.find("main")
    
    # convert to a string, remove '\r', and return
    return str(main).replace('\r', '')

def tramIsWorkingRN():
    """Check if the website was updated"""
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36','Pragma': 'no-cache', 'Cache-Control': 'no-cache'}
    response = requests.get(URL, headers=headers)

    processed_response_html = process_html(response.text)

    if null_response_text == processed_response_html:
        return True
    else:
        return False
        

# GOOGLE SHEETS
import gspread
gc = gspread.service_account()
sh = gc.open("T2C Tracker")
worksheet = sh.sheet1

def updateGoogleSheetCount():
    """Update the Google Sheet"""
    log.info("Updating Google Sheet")
    # get the current date
    now = time.strftime("%d/%m/%Y")
    
    cell = worksheet.find(now)
    row = cell.row
    # find curent count
    current_count = worksheet.cell(row, 3).value
    # update the cell
    worksheet.update_cell(row, 3, current_count + 1)



previousStateTramWorkingRN = True

while True:
    if tramIsWorkingRN() == previousStateTramWorkingRN:
        log.info("No change")
    else:
        log.info("CHANGE DETECTED")
        previousStateTramWorkingRN = tramIsWorkingRN()
        updateGoogleSheetCount()
    time.sleep(DELAY_TIME)

