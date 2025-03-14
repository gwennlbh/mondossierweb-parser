#!/usr/bin/env python
"""
Usage: mondossierweb [SAVE_AS] [URL] [GRADE_CODE] [USERNAME] [PASSWORD_COMMAND] [PUSHBULLET_LINK]
       mondossierweb --help 

Environment variables:
    MDW_USE_CACHE: if set to 1, the HTML will be cached to mdw.html and will be reused if it exists.
"""

from pathlib import Path
from datetime import datetime
import json
from subprocess import run
from time import sleep
from pyvirtualdisplay import Display
from docopt import docopt
from bs4 import BeautifulSoup
from helium import write, click, S, start_firefox, kill_browser,scroll_down, find_all
from typing import NamedTuple, Literal
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium import webdriver
import selenium.common.exceptions
import sys
import os
from gotify import Gotify
import requests

HEADLESS = True



class Grade(NamedTuple):
    code: str
    label: str
    grade: float | Literal["ABJ"] | Literal["ABI"]
    indentation: int

    def __str__(self):
        return f"[{self.code}] {self.label}: {self.grade}"


def configure():
    opts = docopt(__doc__)

    def cli_arg_or(key, ask_message):
        if (arg := opts.get(key)) is not None:
            return arg
        elif (arg := os.getenv(key)) is not None and arg != "":
            return arg
        return input(ask_message)

    def cli_arg_optional(key):
        if (arg := opts.get(key)) is not None:
            return arg
        elif (arg := os.getenv(key)) is not None and arg != "":
            return arg
        return None

    username = cli_arg_or("USERNAME", "Username: ")
    password_command = cli_arg_or("PASSWORD_COMMAND", "Command to get password: ")
    grade_code = cli_arg_or("GRADE_CODE", "Grade code (e.g. N7I51 for SN 1A): ")
    save_as = Path(cli_arg_or("SAVE_AS", "Save JSON file as: "))
    url = cli_arg_or("URL", "URL de mondossierweb: ")
    gotify_base_url = cli_arg_optional("GOTIFY_URL")
    gotify_app_token = cli_arg_optional("GOTIFY_APP_TOKEN")
    ntfy_url = cli_arg_optional("NTFY_URL")
    hide_grade = cli_arg_or("HIDE_GRADES", "Hide grades? (1/0): ")
    return username, password_command, grade_code, save_as, url, gotify_base_url, gotify_app_token, hide_grade, ntfy_url


def get_password(password_command):
    result = run(password_command, shell=True, capture_output=True)
    error = result.stderr.decode("utf-8")

    if f"{password_command}: command not found" in error:
        print(
            f"\t\tPassword command {password_command} not found, trying to use it as a password."
        )
        return password_command

    if result.returncode != 0:
        raise RuntimeError(
            f"Command {password_command} failed with code {result.returncode}: {error}"
        )

    return result.stdout.decode("utf-8").strip()


def get_html(username, password_command, grade_code, url):
    if os.getenv("MDW_USE_CACHE") == "1" and Path("mdw.html").exists():
        print("\tUsing cached HTML")
        return BeautifulSoup(Path("mdw.html").read_text(), features="lxml")

    display = Display(visible=int(not HEADLESS), size=(1920, 1080))
    display.start()
    try:
        print(f"\tOpening {url}…")
        profile = FirefoxProfile()
        profile.set_preference('general.useragent.override', "Ceci est un script d'automatisation inoffensif réalisé par des étudiant·e·s de l'n7. Code source: https://github.com/gwennlbh/mondossierweb-parser")
        driver = start_firefox(url, headless=False, profile=profile)
        print("\tTyping username")
        write(username, into="Username")
        print("\tTyping password")
        write(get_password(password_command), into="Password")
        print("\tLogging in…")
        scroll_down(500)
        click("Login")
        try:
            if "Invalid credentials" in S("body").web_element.text:
                print("\t\tInvalid credentials, exiting.")
                kill_browser()
                display.stop()
                driver.quit()
                sys.exit(2)
        except selenium.common.exceptions.StaleElementReferenceException:
            pass

        print("\tWaiting for page to load…")
        sleep(3)
        try:
            print("\tClosing reminder")
            click("Fermer")
        except:
            pass
        print("\tNavigating to grades page")
        click("Notes & résultats")
        print("\tOpening grades table")
        click(grade_code)
        try:
            print("\tClosing annoying reminder")
            click("Fermer")
        except:
            pass
        element = driver.find_element(By.XPATH, "//div[@class='v-scrollable']//div[@class='v-scrollable v-table-body-wrapper v-table-body']")
        driver.execute_script("arguments[0].scrollBy(0,1000)", element)
        sleep(1)
        print("\tCapturing page body")
        html = S("body").web_element.get_attribute("innerHTML")
        if os.getenv("MDW_USE_CACHE"):
            print("\tCaching HTML to mdw.html") 
            Path("mdw.html").write_text(html)
        parsed = BeautifulSoup(html, features="lxml")
    finally:
        kill_browser()
        display.stop()
        driver.quit()
    return parsed


def grade_or_none(string):
    if string.upper() in {"ABJ", "ABI"}:
        return string.upper()
    try:
        return float(string)
    except ValueError:
        return None


def to_dict(document, grade_code):
    print("\tGetting the right table")
    table = [t for t in document("table") if grade_code in t.strings][0]
    print("\tExtracting cells")
    cells = [
        [cell.replace("\xa0", "\t") for cell in row.strings] for row in table("tr")
    ]
    Path("mdw-cells.json").write_text(json.dumps(cells, indent=4))
    print("\tExtracting grades")
    grades = {}
    for row in cells:
        label = [cell for cell in row[1:] if cell.strip()][0]
        label, indentation = label.strip(), label.count("\t")
        numbers = [grade_or_none(cell) for cell in row if grade_or_none(cell)]
        if not numbers:
            print(f"\t\tSkipping row {label}: no grades found")
            continue
        grades[label] = {
            "code": row[0],
            "label": label,
            "grade": numbers[0],
            "indentation": indentation,
        }
    return grades


def diff_with_previous(new_grades, save_as):
    changes = {}
    if not save_as.exists():
        return
    print("Previous grades file found, checking for differences.")
    print("\tLoading previous grades")
    old_grades = json.loads(save_as.read_text())

    print("\n")
    for key in new_grades.keys() - old_grades.keys():
        print(f"- New grade: {Grade(**new_grades[key])}")
        changes[key] = new_grades[key]

    for key in new_grades.keys() & old_grades.keys():
        if (new_grade := new_grades[key]["grade"]) != (
            old_grade := old_grades[key]["grade"]
        ):
            print(f"- Grade for {key} changed: {old_grade} -> {new_grade}.")
            changes[key] = new_grade

    if not changes:
        print("No changes found.")

    print("\n")

    return changes


def main():
    username, password_command, grade_code, save_as, url, gotify_base_url, gotify_app_token, hide_grade, ntfy_url = configure()
    if not gotify_base_url or not gotify_app_token:
        print("Missing GOTIFY_URL or GOTIFY_APP_TOKEN, gotify will be disabled")
        use_gotify = False
    else:
        use_gotify = True
    if not ntfy_url:
        print("Missing NTFY_URL, ntfy will be disabled")
        use_ntfy = False
    else:
        use_ntfy = True

    print("Getting HTML")
    document = get_html(username, password_command, grade_code, url)
    print("Parsing HTML table into dict")
    grades = to_dict(document, grade_code)
    print(f"Got grades: {grades}")
    changes = diff_with_previous(grades, save_as)
    print(f"Writing to {save_as}")
    save_as.write_text(json.dumps({"updated_at": str(datetime.now())} | grades, indent=4))

    if changes:
        if use_gotify:
            assert gotify_base_url is not None # remove warning from LSP
            assert gotify_app_token is not None
            gotify = Gotify(
                base_url = gotify_base_url,
                app_token = gotify_app_token,
            )
            gotify.create_message(
                title = "Nouvelles notes",
                message = '\n'.join(f"{label}: {grade['grade']}" if not hide_grade else f"{label}" for label, grade in changes.items()),
                priority = 5,
            )
        if use_ntfy:
            assert ntfy_url is not None # remove warning from LSP
            requests.post(ntfy_url,
                          data='\n'.join(f"{label}: {grade['grade']}" if not hide_grade else f"{label}" for label, grade in changes.items()),
                          headers={
                              "Title": "New grades",
                              "Tags": "school,scroll"
                              })

    sys.exit(1 if changes else 0)

if __name__ == "__main__":
    main()