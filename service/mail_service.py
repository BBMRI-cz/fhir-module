import logging
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import schedule

from util.config import NEW_FILE_PERIOD_DAYS,RECORDS_DIR_PATH

from util.custom_logger import setup_logger
from util.file_age_util import get_file_age

setup_logger()
logger = logging.getLogger()



class MailService:
    def __init__(self,records_path:str, new_file_period: int, smtp_host: str, smtp_port:int,email_receiver:str):
        self._dir_path = records_path
        try:
            self._new_file_period = int(new_file_period)
        except ValueError:
            logger.error(f"Error: provided new_file period is not an int, Initializing MailService with default value of 30 days.")
            self._new_file_period = 30
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.email_receiver = email_receiver
        #TODO CHANGE TO CORRECT EMAIL ONCE SET UP BY BBMRI
        self.email_sender = "test@example.com"

    def send_message(self,subject: str, body: str):
        message = MIMEMultipart()
        message["From"] = self.email_sender
        message["To"] = self.email_receiver
        message["Subject"] = subject
        message.attach(MIMEText(body,"plain"))
        try:
            with smtplib.SMTP(self.smtp_host,self.smtp_port) as server:
                server.sendmail(self.email_sender,self.email_receiver, message.as_string())
                logger.info("Email sent succesfully!")
        except Exception as e:
            logger.error(f"Error sending email: {e}")

    def check_if_data_files_are_fresh(self) -> bool:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".csv"):
                file_age = get_file_age(dir_entry.path)
                if file_age <= self._new_file_period:
                    return True
        return False

    def check_freshness_and_send_email(self):
        if self.check_if_data_files_are_fresh():
            return
        subject = "[WARNING] Provided data are not fresh"
        message = f"There has not been a new file with data provides for atleast {self._new_file_period} days. \n" \
                  f"Please upload new files for the ETL transformation within FHIR module."
        self.send_message(subject,message)
        return

    def __initialize_fresh_data_files_scheduler(self):
        logger.info("Initializing scheduler....")
        schedule.every().week.do(self.check_if_data_files_are_fresh)
        logger.info("Scheduler initialized.")

    def run_scheduler(self):
        self.__initialize_fresh_data_files_scheduler()
        logger.info("Running Scheduler.")
        while True:
            schedule.run_pending()
            time.sleep(1)

