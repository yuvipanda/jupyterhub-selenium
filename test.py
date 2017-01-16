import os
import hmac
import hashlib
import time
import socket

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import nbformat

class NotebookHuman:
    """
    A fake Notebook User who can simulate human-ish activity
    """
    def __init__(self, driver, hub_url, username, password, timeout=60):
        self.driver = driver
        self.hub_url = hub_url
        self.username = username
        self.password = password
        self.timeout = timeout


    def login_to_jupyterhub(self):
        """
        Logs into a given jupyterhub instance.

        It expects to be using HMACAuthenticator
        """
        self.driver.get(self.hub_url)
        self.driver.find_element_by_name("username").send_keys(self.username)
        self.driver.find_element_by_name("password").send_keys(self.password)
        self.driver.find_element_by_id('login_submit').click()

        print("Submitted log in info")
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.visibility_of_element_located((By.ID, 'start'))
            )
            self.driver.find_element_by_id('start').click()
            print("Found start button and clicked it")
        except TimeoutException:
            # Is ok, probably just means this user's pod was already running
            # and just sent us straight to the home. We verify this after the
            # pass
            print("Could not find start button in time")
            pass

        WebDriverWait(self.driver, self.timeout).until(
            EC.visibility_of_element_located((By.ID, 'new-buttons'))
        )
        print("Found new-buttons")

    def logout(self):
        self.driver.find_element_by_id('logout').click()
        time.sleep(1)

    def wait_for_ready_kernel(self):
        """
        Waits until the kernel is ready to accept more code
        """
        WebDriverWait(self.driver, self.timeout).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'kernel_idle_icon'))
        )


    def create_new_notebook(self):
        """
        Create a new Python3 notebook in a notebook that's just been logged into

        This closes old notebook window, and sets driver to have the window
        with the notebook be the active one. It also waits for the kernel to be
        ready before returning
        """
        WebDriverWait(self.driver, self.timeout).until(
            EC.visibility_of_element_located((By.ID, 'new-buttons'))
        )
        print("found new buttons")
        self.driver.find_element_by_id('new-buttons').click()
        self.driver.find_element_by_id('kernel-python3').click()

        print("clicked new buttons")
        self.driver.switch_to_window(self.driver.window_handles[-1])
        self.wait_for_ready_kernel()
        print("kernel is ready")

    def run_new_code_cell(self, code):
        """
        Runs given code as a new cell at the bottom of the notebook.

        Waits for the execution to complete before returning
        """
        js = 'window.$(".input_area").last().children()[0].CodeMirror.setValue({code})'
        self.driver.execute_script(js.format(code=repr(code)))

        self.driver.find_element_by_css_selector('#run_int > button').click()
        self.wait_for_ready_kernel()
        # This is often needed because the kernel idle indicator doesn't actually
        # change for a lot of small bits of code - only for things that take longer.
        # it is, indeed, a hack!
        time.sleep(1)

    def get_last_output(self):
        els = self.driver.find_elements_by_class_name('output_area')
        return els[-1].text


if __name__ == '__main__':
    secret = os.environ['HMAC_SECRET_KEY']
    hub_url = os.environ['HUB_URL']
    selenium_url = os.environ['SELENIUM_URL']
    username = socket.gethostname()
    password = hmac.new(
        bytes.fromhex(secret),
        username.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    nbh = NotebookHuman(
        webdriver.WebDriver(
            selenium_url,
            desired_capabilities=DesiredCapabilities.CHROME),
        hub_url, username, password)
    try:
        print("attempting to log in to jupyterhub")
        nbh.login_to_jupyterhub()
        print("logged into jupyterhub")
        nbh.create_new_notebook()
        print("created new notebook")

        nb = nbformat.read(open('test.ipynb'), 4)
        for cell in nb.cells:
            if cell.cell_type == 'code' and cell.execution_count:
                print("attempting to run some code")
                nbh.run_new_code_cell(cell.source)
                real_output = nbh.get_last_output().strip()
                print(cell.source)
                print(real_output)
                assert real_output == cell.outputs[0].text.strip()

    finally:
        nbh.logout()
        nbh.driver.close()
