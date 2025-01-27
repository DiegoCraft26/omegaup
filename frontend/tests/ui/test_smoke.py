#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# type: ignore

'''Run Selenium end-to-end tests.'''

import os

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ui import util  # pylint: disable=no-name-in-module


@util.no_javascript_errors()
@util.annotate
def test_create_user(driver):
    '''Tests basic functionality.'''

    username = 'unittest_user_%s' % driver.generate_id()
    password = 'p@ssw0rd'
    driver.register_user(username, password)

    with driver.login(username, password):
        pass


@util.no_javascript_errors()
@util.annotate
def test_login(driver):
    '''Tests login with a normal and an admin user.'''

    with driver.login_user():
        pass

    with driver.login_admin():
        pass


@util.no_javascript_errors()
@util.annotate
def test_js_errors(driver):
    '''Tests assert{,_no}_js_errors().'''

    # console.log() is not considered an error.
    with util.assert_no_js_errors(driver):
        driver.browser.execute_script('console.log("foo");')

    if driver.browser_name != 'firefox':
        # Firefox does not support this.
        with util.assert_js_errors(driver, expected_messages=('bar', )):
            driver.browser.execute_script('console.error("bar");')

        with util.assert_no_js_errors(driver):
            # Within an asset_js_error() context manager, messages should not
            # be bubbled up.
            with util.assert_js_errors(driver, expected_messages=('baz', )):
                driver.browser.execute_script('console.error("baz");')


@util.no_javascript_errors()
@util.annotate
def test_create_problem(driver):
    '''Tests creating a public problem and retrieving it.'''

    problem_alias = 'ut_problem_%s' % driver.generate_id()
    with driver.login_admin():
        util.create_problem(driver, problem_alias)

    remove_problem_images()

    with driver.login_user():
        prepare_run(driver, problem_alias)
        assert (problem_alias in driver.browser.find_element(
            By.XPATH, '//h3[@data-problem-title]').get_attribute('innerText'))

        img = driver.browser.find_elements(
            By.XPATH,
            '//div[contains(concat(" ", normalize-space(@class), " "), " '
            'markdown ")]/div/p/img')
        assert len(img) > 0

        runs_before_submit = driver.browser.find_elements(
            By.XPATH,
            '//div[contains(concat(" ", normalize-space(@class), " "), " '
            'active ")]/div/div/table[contains(concat(" ", normalize-space('
            '@class), " "), " runs ")]/tbody/tr/td[@data-run-status]')

        filename = 'Main.java'
        util.create_run(driver, problem_alias, filename)

        runs_after_submit = driver.browser.find_elements(
            By.XPATH,
            '//div[contains(concat(" ", normalize-space(@class), " "), " '
            'active ")]/div/div/table[contains(concat(" ", normalize-space('
            '@class), " "), " runs ")]/tbody/tr/td[@data-run-status]')

        assert len(runs_before_submit) + 1 == len(runs_after_submit)

        driver.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 '//button[contains(concat(" ", normalize-space(@class), " "),'
                 ' " details ")]'))).click()

        driver.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH,
                 '//div[contains(concat(" ", normalize-space(@class), " "), " '
                 'active ")]/div[@data-overlay]/div[@data-overlay-popup]/form['
                 '@data-run-details-view]')))

        textarea = driver.browser.find_element(
            By.XPATH,
            '//div[contains(concat(" ", normalize-space(@class), " "), " '
            'active ")]/div[@data-overlay]/div[@data-overlay-popup]/form['
            '@data-run-details-view]//div[@class="CodeMirror-code"]')

        assert textarea.text is not None

        resource_path = os.path.join(util.OMEGAUP_ROOT,
                                     'frontend/tests/resources', filename)
        # The text of the CodeMirror editor contains the line number.
        # Non-exact match is needed.
        with open(resource_path, 'r', encoding='utf-8') as f:
            for row in f.read().splitlines():
                if row is not None:
                    assert (row in textarea.text), row

        driver.browser.find_element(
            By.XPATH,
            '//div[contains(concat(" ", normalize-space(@class), " "), " '
            'active ")]/div[@data-overlay]').click()
        driver.update_score(problem_alias)

    with driver.login_user():
        prepare_run(driver, problem_alias)
        driver.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH,
                 '//div[contains(concat(" ", normalize-space(@class), " "), " '
                 'active ")]/div[@data-overlay]/div[@data-overlay-popup]/form['
                 '@data-promotion-popup]')))

    with driver.login_admin():
        prepare_run(driver, problem_alias)
        util.show_run_details(driver, code='java.util.Scanner')

        driver.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 '//div[contains(concat(" ", normalize-space(@class), " "), '
                 '" tab-content ")]/div[contains(concat(" ", '
                 'normalize-space(@class), " "), " show ")]/div[@data-overlay]'
                 '/div[@data-overlay-popup]/button'))).click()

        assert driver.browser.current_url.endswith('#runs')

        driver.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 '//table[contains(concat(" ", normalize-space(@class), " "), '
                 '" runs ")]/tbody/tr/td/div[contains(concat(" ", '
                 'normalize-space(@class), " "), " dropdown ")]/'
                 'button'))).click()

        driver.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 '//table[contains(concat(" ", normalize-space(@class), " "), '
                 '" runs ")]/tbody/tr/td/div[contains(concat(" ", '
                 'normalize-space(@class), " "), " show ")]/div/button['
                 '@data-actions-rejudge]'))).click()

        global_run = driver.browser.find_element(
            By.XPATH,
            '//table[contains(concat(" ", normalize-space(@class), " "), " '
            'runs ")]/tbody/tr/td[@data-run-status]/span')

        assert global_run.text in ('rejudging', 'AC')


@util.annotate
@util.no_javascript_errors()
def prepare_run(driver, problem_alias):  # pylint: disable=redefined-outer-name
    '''Entering to a problem page to create a submission.'''

    driver.wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR,
             'a[data-nav-problems]'))).click()
    with driver.page_transition():
        driver.wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 'a[data-nav-problems-collection]'))).click()

    driver.wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR,
             'a[data-nav-problems-all]'))).click()

    driver.wait.until(
        EC.element_to_be_clickable(
            (By.XPATH,
             '//a[text() = "%s"]' % problem_alias))).click()


def remove_problem_images() -> None:
    '''Removes the problem's images.'''

    img_path = os.path.join(util.OMEGAUP_ROOT, 'frontend/www/img')
    is_dir = os.path.isdir(img_path)
    if is_dir is False:
        return
    for dirname in os.listdir(img_path):
        directory = os.path.join(img_path, dirname)
        if os.path.isdir(directory):
            for file in os.listdir(directory):
                file_location = os.path.join(directory, file)
                if os.path.isfile(file_location):
                    os.remove(file_location)
            os.rmdir(directory)
