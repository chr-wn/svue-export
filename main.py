import os
import getpass
import csv
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import Optional, Tuple, List, Dict, Any

API_URL = "https://sisstudent.fcps.edu/SVUE/Service/PXPCommunication.asmx"
HEADERS = {"Content-Type": "application/soap+xml; charset=utf-8"}
OUTPUT_FILENAME = "grades.csv"
REPORTING_PERIODS = 4

def get_credentials() -> Tuple[str, str]:
    """
    Loads StudentVUE credentials from a .env file or, if not found,
    prompts the user to enter them securely.
    """
    load_dotenv()
    username = os.getenv("STUDENTVUE_USERNAME")
    password = os.getenv("STUDENTVUE_PASSWORD")

    if username and password:
        print("Credentials successfully loaded from .env file.")
        return username, password
    else:
        print("No .env file detected. Please provide your credentials.")
        username = input("Enter StudentVUE Username: ")
        password = getpass.getpass("Enter StudentVUE Password: ")
        return username, password

def fetch_gradebook_data(
    session: requests.Session, username: str, password: str, period: int
) -> Optional[BeautifulSoup]:
    """
    Fetches the raw gradebook XML data for a specific reporting period.

    Args:
        session: The active requests.Session object.
        username: The user's StudentVUE username.
        password: The user's StudentVUE password.
        period: The integer for the reporting period (e.g., 0 for Q1).

    Returns:
        A BeautifulSoup object of the parsed gradebook XML, or None if an
        error occurs.
    """
    print(f"Requesting data for reporting period {period + 1}...")

    xml_request_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <ProcessWebServiceRequest xmlns="http://edupoint.com/webservices/">
      <userID>{username}</userID>
      <password>{password}</password>
      <skipLoginLog>true</skipLoginLog>
      <parent>false</parent>
      <webServiceHandleName>PXPWebServices</webServiceHandleName>
      <methodName>Gradebook</methodName>
      <paramStr>&lt;Params&gt;&lt;ReportPeriod&gt;{period}&lt;/ReportPeriod&gt;&lt;/Params&gt;</paramStr>
    </ProcessWebServiceRequest>
  </soap12:Body>
</soap12:Envelope>"""

    try:
        response = session.post(API_URL, data=xml_request_body.encode('utf-8'), headers=HEADERS)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml-xml')
        gradebook_xml_content = soup.find('ProcessWebServiceRequestResult').text

        if "ERROR" in gradebook_xml_content:
            print(f"  -> Server returned an error for period {period + 1}. The period may not exist or data is unavailable.")
            return None

        print(f"  -> Successfully retrieved data for period {period + 1}.")
        return BeautifulSoup(gradebook_xml_content, 'lxml-xml')

    except requests.exceptions.RequestException as e:
        print(f"  -> A network error occurred for period {period + 1}: {e}")
        return None

def write_data_to_csv(writer: csv.writer, gradebook_soup: BeautifulSoup):
    """
    Parses the gradebook XML and writes course and assignment data to a CSV file.
    """
    courses = gradebook_soup.find_all("Course")
    for course in courses:
        course_title = course.get("Title")
        course_room = course.get("Room")
        course_staff = course.get("Staff")
        course_period = course.get("Period")
        
        marks = course.find_all("Mark")
        for mark in marks:
            mark_name = mark.get("MarkName")
            calculated_score = mark.get("CalculatedScoreString")
            assignments = mark.find_all("Assignment")

            if not assignments:
                row = [
                    mark_name, course_title, course_room, course_staff, course_period,
                    calculated_score, mark_name,
                    "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"
                ]
                writer.writerow(row)
            else:
                for assignment in assignments:
                    row = [
                        mark_name, course_title, course_room, course_staff, course_period,
                        calculated_score, mark_name,
                        assignment.get("Measure"), assignment.get("Type"),
                        assignment.get("Date"), assignment.get("DueDate"),
                        assignment.get("Score"), assignment.get("Points"), assignment.get("Notes")
                    ]
                    writer.writerow(row)

def main():
    """
    Main execution function to connect to the StudentVUE API and export
    grades for all available reporting periods to a CSV file.
    """
    print("--- StudentVUE Grade Exporter ---")
    username, password = get_credentials()

    csv_header = [
        "Quarter", "Course Title", "Room", "Teacher", "Period", "Overall Score", 
        "Mark", "Assignment", "Type", "Date Assigned", "Date Due", "Score", 
        "Points", "Notes"
    ]

    try:
        with requests.Session() as session, open(OUTPUT_FILENAME, "w", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(csv_header)

            for period in range(REPORTING_PERIODS):
                gradebook_soup = fetch_gradebook_data(session, username, password, period)
                
                if gradebook_soup:
                    write_data_to_csv(writer, gradebook_soup)
                
                time.sleep(.25)

        print(f"\nExport complete. All available data has been saved to '{OUTPUT_FILENAME}'")

    except IOError as e:
        print(f"\nA critical file error occurred: Could not write to {OUTPUT_FILENAME}. Details: {e}")
    except Exception as e:
        print(f"\nAn unexpected critical error occurred: {e}")

if __name__ == "__main__":
    main()
