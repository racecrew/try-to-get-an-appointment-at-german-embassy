import base64
import binascii
import datetime
import json
import os.path
import sys

import clipboard
import requests
from bs4 import BeautifulSoup

from src.CaptchaSolverFacade import CaptchaSolverFacade


class Appointment:
    __parameter_data = {
        "kiew": {
            "locationCode": "kiew",
            "realmId": 561,
            "locationCode": "kiew",
            "visa": {
                "nationaleVisa": {
                    "categoryId": 1497
                },
                "Schengenvisum": {
                    "categoryId": 2053
                }
            }
        },
        "moskau": {
            "locationCode": "mosk",
            "realmId": 875,
            "locationCode": "mosk",
            "visa": {
                "nationaleVisa": {
                    "categoryId": 1925
                },
                "Schengenvisum": {
                    "categoryId": 0
                }
            }
        }
    }

    __url_base = "https://service2.diplo.de/rktermin/extern"
    __url_choose_location = __url_base + "/choose_locationList.do"
    __url_month_appointment = __url_base + "/appointment_showMonth.do"
    __request_locale = "de"
    __location_code = ""
    __visa = ""

    __headers = {'Content-Type': 'application/x-www-form-urlencoded',
                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}

    def __init__(self, location_code, visa):
        self.__location_code = location_code
        self.__visa = visa

    def get_realm_id(self):
        return self.__parameter_data[self.__location_code]["realmId"]

    def get_location_code(self):
        return self.__parameter_data[self.__location_code]["locationCode"]

    def get_category_id(self):
        return self.__parameter_data[self.__location_code]["visa"][self.__visa]["categoryId"]

    def get_url_month_appointment(self):
        return self.__url_month_appointment + \
               "?locationCode=" + self.get_location_code() + \
               "&realmId=" + str(self.get_realm_id()) + \
               "&categoryId=" + str(self.get_category_id()) + \
               "&dateStr=" + (datetime.date.today()).strftime("%d.%m.%Y")

    def get_captcha_as_base64(self, html_page_content):
        soup = BeautifulSoup(html_page_content, features="lxml")
        captcha_is_found = soup.find(name="captcha")
        captcha_div_is_found = None
        captcha_style_value = None
        if captcha_is_found:
            captcha_div_is_found = captcha_is_found.find(name="div")
            captcha_style_value = soup.find(name="captcha").find(name="div").get('style')

        if captcha_style_value:
            background_image_as_base64 = captcha_style_value[44:-78]
            if background_image_as_base64:
                # check if the string is base64 encoded, if not - return empty string
                try:
                    base64.b64decode(background_image_as_base64)
                    return background_image_as_base64
                except binascii.Error:
                    return "binascii.Error"
            else:
                return None
        else:
            return None

    def write_json_file(self, filename, data):
        with open(filename, 'w') as outfile:
            json.dump(data, outfile)

    def read_json_file(self, filename):
        if os.path.isfile(filename):
            with open(filename, 'r') as json_file:
                data = json_file.read()
            return json.loads(data)
        else:
            return {"jsessionid": "", "keks": ""}

    def do_request_new_session(self, base64_img, cookies):
        if base64_img != "":
            if base64_img != "binascii.Error":
                __CaptchaSolverFacade = CaptchaSolverFacade()
                clipboard.copy(base64_img)
                captcha_text = __CaptchaSolverFacade.solve_captcha(base64_img)

                date_to_check = (datetime.date.today()).strftime("%d.%m.%Y")

                payload = {
                    "locationCode": '"' + self.get_location_code() + '"',
                    "realmId": str(self.get_realm_id()),
                    "categoryId": str(self.get_category_id()),
                    "dateStr": date_to_check,
                    "captchaText": str(captcha_text),
                    "action": "appointment_showMonth:Weiter"
                }

                return requests.post(url=self.__url_month_appointment,
                                     headers=self.__headers,
                                     data=payload,
                                     cookies=cookies)
            else:
                sys.exit("extracted captcha is not a base64 encoded string")

    def try_monthly_appointments(self, months=3):
        session_data = self.read_json_file("session_data.json")
        cookies = dict(JSESSIONID=session_data["jsessionid"], KEKS=session_data["keks"])

        html_page = requests.get(url=self.get_url_month_appointment(),
                                 headers=self.__headers,
                                 cookies=cookies)
        base64_img = self.get_captcha_as_base64(html_page.content)

        request_new_session = base64_img and base64_img != "" and base64_img != "binascii.Error"
        if request_new_session:
            if 'JSESSIONID' in html_page.cookies:
                session_data["jsessionid"] = html_page.cookies['JSESSIONID']
            if 'KEKS' in html_page.cookies:
                session_data["keks"] = html_page.cookies['KEKS']
            self.write_json_file("session_data.json", session_data)
            cookies = dict(JSESSIONID=session_data["jsessionid"], KEKS=session_data["keks"])
            html_page = self.do_request_new_session(base64_img, cookies)

        today = datetime.date.today()
        cur_day = today.day
        cur_month = today.month
        cur_year = today.year
        for i in range(0, months):
            if cur_month == 12 and i < months:
                cur_year += 1

            if i > 0:
                cur_day = 1
                cur_month = cur_month + 1
                if cur_month > 12:
                    cur_month = 1

            date_to_check = str(cur_day) + "." + str(cur_month) + "." + str(cur_year)

            payload = {
                "locationCode": '"' + self.get_location_code() + '"',
                "realmId": str(self.get_realm_id()),
                "categoryId": str(self.get_category_id()),
                "dateStr": date_to_check,
                "action": "appointment_showMonth:Weiter"
            }

            html_page = requests.post(url=self.__url_month_appointment,
                                      headers=self.__headers,
                                      data=payload,
                                      cookies=cookies)

            resp = str(html_page.content)

            if str("Termine").lower() in resp.lower():
                if str("keine Termine").lower() in resp.lower():
                    print(date_to_check + ": keine Termine")
                else:
                    print(date_to_check + ": Termine verfügbar")
            else:
                print(date_to_check + ": keine Info über Termine")
