from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import nbformat


class NotebookHuman:
    """
    A fake Notebook User who can simulate human-ish activity
    """
    def __init__(self, driver, hub_url, username):
        self.driver = driver
        self.hub_url = hub_url
        self.username = username

    def login_to_jupyterhub(self):
        """
        Logs into a given jupyterhub instance.

        It expects to be using DummyAuthenticator, which accepts all usernames
        and passwords.
        """
        self.driver.get(self.hub_url)
        self.driver.find_element_by_name("username").send_keys(self.username)
        self.driver.find_element_by_name("password").send_keys('wat')
        self.driver.find_element_by_id('login_submit').click()

    def wait_for_ready_kernel(self, timeout=10):
        """
        Waits until the kernel is ready to accept more code
        """
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'kernel_idle_icon'))
        )


    def create_new_notebook(self):
        """
        Create a new Python3 notebook in a notebook that's just been logged into

        This closes old notebook window, and sets driver to have the window
        with the notebook be the active one. It also waits for the kernel to be
        ready before returning
        """
        self.driver.find_element_by_id('new-buttons').click()
        self.driver.find_element_by_id('kernel-python3').click()

        self.driver.close()

        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.wait_for_ready_kernel()

    def run_new_code_cell(self, code):
        """
        Runs given code as a new cell at the bottom of the notebook.

        Waits for the execution to complete before returning
        """
        # HACK: .send_keys does not seem to work for CodeMirror :(
        js = '$(".input_area").last().children()[0].CodeMirror.setValue({code})'
        self.driver.execute_script(js.format(code=repr(code)))

        self.driver.find_element_by_css_selector('#run_int > button').click()
        self.wait_for_ready_kernel()

    def get_last_output(self):
        return self.driver.find_elements_by_css_selector('.output_area')[-1].text


if __name__ == '__main__':
    nbh = NotebookHuman(webdriver.Firefox(), 'http://localhost:8000', 'test')
    nbh.login_to_jupyterhub()
    nbh.create_new_notebook()

    nb = nbformat.read(open('test.ipynb'), 4)
    for cell in nb.cells:
        if cell.cell_type == 'code' and cell.execution_count:
            nbh.run_new_code_cell(cell.source)
            assert nbh.get_last_output().strip() == cell.outputs[0].text.strip()
