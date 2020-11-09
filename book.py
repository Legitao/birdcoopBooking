from splinter import Browser
import datetime
from time import sleep
from dotenv import load_dotenv
import os
import sys


# dd/mm/yyyy format
def getBookDate():
    dateObj = datetime.date.today() + datetime.timedelta(days=2)
    dateStr = dateObj.strftime('%d/%m/%Y')
    weekDay = dateObj.strftime('%w')
    return (dateStr, weekDay)


def launchBrowser():
    executable_path = {'executable_path': '/usr/local/bin/geckodriver'}
    browser = Browser(**executable_path)  # defaults to firefox
    return browser


# cwl login
def loginCWL(browser):
    browser.find_by_css('.pm-button, .pm-login-button').click()
    browser.links.find_by_href('/sso/index.php').click()
    browser.fill('j_username', os.getenv('username'))
    browser.fill('j_password', os.getenv('password'))
    browser.find_by_text('Login').click()
    # wait for CWL to asynchronosly verify
    # otherwise can't find 'jump-to-date'
    while (browser.is_text_not_present('BirdCoop Access')):
        pass


def waitUntil12PM():
    now = datetime.datetime.now().time()  # time object
    currHour = str(now).split(':')[0]
    while (currHour != '12'):
        now = datetime.datetime.now().time()  # time object
        currHour = str(now).split(':')[0]


def bookSession(browser, dateStr, weekDay):
    while True:
        browser.fill('jump-to-date', dateStr + '\n')
        sleep(3)
        print('reading session list...')
        session_list = browser.find_by_css('.bm-class-row')
        if (int(weekDay) < 5):
            # workday has 8 sessions
            session_list = session_list[0: 8]
        else:
            # weekend has 6 sessions
            session_list = session_list[0: 6]

        registered = False

        for idx, session in enumerate(session_list):
            # skip first session in the morning, too early
            if idx == 0:
                continue
            # can't register because session full or haven't open
            if session.find_by_css('.bm-group-item-link div label').html != 'Register Now':
                # find_by_text is too slow
                # if not session.find_by_text('Register Now'):
                continue
            # session havs spot left, can register
            sessionTime = session.find_by_css(
                '.bm-group-item-desc .anchor:first-child span').value
            print(f"booking session {sessionTime}......")
            session.find_by_css('.bm-class-details').click()
            registered = True
            break

        if registered:
            break
        else:
            print('No available session for now, reload...\n')
            browser.reload()

    # there are 2 register now buttons, first one is in the navbar, not what we want
    browser.find_by_css('.bm-book-button').click()
    while (browser.is_text_not_present('Next')):
        pass
    browser.find_by_text('Next').click()
    while (browser.is_text_not_present('Next')):
        pass
    browser.find_by_text('Next').click()
    while (browser.is_text_not_present('Checkout')):
        pass
    browser.find_by_text('Checkout').click()

    # loading the place order page is really slow
    sleep(10)

    # 'Place My Order' button is inside an iframe
    # must switch context to the iframe to get the element
    with browser.get_iframe(0) as iframe:
        iframe.find_by_css('.process-now').click()
        sleep(10)
        print('book success')


def main():
    try:
        load_dotenv()
        dateStr, weekDay = getBookDate()
        sys.stdout = open(f"logs/{dateStr.replace('/', '-')}.txt", "a+")
        # visit perfectmind site
        browser = launchBrowser()
        print('Start visiting booking stie...')
        browser.visit(os.getenv('URL'))
        loginCWL(browser)
        # waitUntil12PM()
        bookSession(browser, dateStr, weekDay)
    except Exception as e:
        print('Error occurs')
        print(e)
        print()
    finally:
        browser.quit()
        sys.stdout.close()


if __name__ == "__main__":
    main()
