from src.CaptchaSolverFacade import CaptchaSolverFacade
import requests
from bs4 import BeautifulSoup
import clipboard
import datetime
import base64
import binascii
import sys


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

    __headers = {'content-type': 'text/html;charset=UTF-8'}

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
               "&categoryId=" + str(self.get_category_id())

    def get_html_page(self, url):
        return requests.get(url, headers=self.__headers)

    def get_captcha_as_base64(self, html_page_content):
        soup = BeautifulSoup(html_page_content, features="lxml")
        captcha_style_value = soup.find(name="captcha").find(name="div").get('style')
        background_image_as_base64 = captcha_style_value[44:-78]
        if background_image_as_base64:
            # check if the string is base64 encoded, if not - return empty string
            try:
                base64.b64decode(background_image_as_base64)
                return background_image_as_base64
            except binascii.Error:
                return "binascii.Error"
        else:
            return ""

    def try_monthly_appointments(self):
        html_page = self.get_html_page(self.get_url_month_appointment())
        jsessionid = html_page.cookies['JSESSIONID']
        keks = html_page.cookies['KEKS']
        cookies = dict(JSESSIONID=jsessionid, KEKS=keks)

        base64_img = self.get_captcha_as_base64(html_page.content)
        if base64_img != "":
            if base64_img != "binascii.Error":
                __CaptchaSolverFacade = CaptchaSolverFacade()
                clipboard.copy(base64_img)
                captcha_text = __CaptchaSolverFacade.solve_captcha(base64_img)

                date_to_check = (datetime.date.today() + datetime.timedelta(0)).strftime("%d.%m.%Y")

                payload = {
                    "locationCode": '"' + self.get_location_code() + '"',
                    "realmId": str(self.get_realm_id()),
                    "categoryId": str(self.get_category_id()),
                    "dateStr": date_to_check,
                    "captchaText": str(captcha_text),
                    "action": "appointment_showMonth:Weiter"
                }

                html_page_monthly = requests.post(url=self.__url_month_appointment, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=payload, cookies=cookies)
            else:
                sys.exit("extracted captcha is not a base64 encoded string")

        for i in range(0, 90):
            date_to_check = (datetime.date.today() + datetime.timedelta(i)).strftime("%d.%m.%Y")

            payload = {
                "locationCode": '"' + self.get_location_code() + '"',
                "realmId": str(self.get_realm_id()),
                "categoryId": str(self.get_category_id()),
                "dateStr": date_to_check,
                "action": "appointment_showMonth:Weiter"
            }

            html_page_monthly = requests.post(url=self.__url_month_appointment, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=payload, cookies=cookies)

            resp = str(html_page_monthly.content)

            if str("keine Termine").lower() in resp.lower():
                print(date_to_check + ": keine Termine")
            else:
                print(date_to_check + ": Termine vorhanden")
