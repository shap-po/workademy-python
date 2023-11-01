import flask
from markupsafe import Markup
from bs4 import BeautifulSoup
import glob
import os
import json
import requests
from urllib.parse import urljoin


DEFAULT_PORT = 5000
FETCH_COURSE_CSS_URL = 'https://study.ed-era.com/uk/courses/course/'
FETCH_CERTIFICATE_CSS_URL = 'https://study.ed-era.com/uk/verifycertificate/'
FETCHED_COURSE_CSS_DIR = 'static/downloaded/course'
FETCHED_CERTIFICATE_CSS_DIR = 'static/downloaded/certificate'

# read config
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        COURSES_LOCATION = config.get('courses_location')
        PORT = config.get('port', DEFAULT_PORT)
        FETCH_CSS = config.get('fetch_css_on_startup', True)
        DEBUG = config.get('debug', False)
except FileNotFoundError:
    config = {
        'courses_location': "",
        'port': DEFAULT_PORT,
        'fetch_css_on_startup': True,
        'debug': False,
    }
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    print('Config file created. Please edit it and restart the server.')
    exit(0)

if not COURSES_LOCATION:
    print('Please specify courses location (/workademy-frontend/static/workspaces-assets/course-assets or /workademy-workspaces-assets/course-assets/) in config.json')
    exit(0)
if not os.path.exists(COURSES_LOCATION):
    print('Courses location not found, please specify it in config.json')
    exit(0)


app = flask.Flask(__name__)


def edit_course_content(content: str, course_id: str) -> str:
    content = content.replace(
        '_PROCEED_TO_COURSE_',
        f'''<a
        href="/uk/signin?enroll={course_id}&amp;usingVoucher=undefined"
        class="body-1 v-btn v-btn--block v-btn--has-bg v-btn--router theme--light elevation-0 v-size--default proceed-to-course-button"
        allow-overflow=""
        style="border-left: none;">
            <span class="v-btn__content">
                Записатися
            </span>
        </a>'''
    )

    soup = BeautifulSoup(content, 'html.parser')

    # replace v-expansion-panels
    for panel in soup.find_all('v-expansion-panel'):
        panel.name = 'div'
        panel['class'] = 'v-expansion-panel'
        panel['aria-expanded'] = 'false'
        header = panel.find('v-expansion-panel-header')
        if header:
            header.name = 'button'
            header['type'] = 'button'
            header['class'] = 'v-expansion-panel-header'
            icon = header.find('i')
            if icon:
                icon['class'] = 'v-icon notranslate mdi mdi-chevron-down theme--light'
        content = panel.find('v-expansion-panel-content')
        if content:
            content.name = 'div'
            content['class'] = 'v-expansion-panel-content'
            wrapper = soup.new_tag('div')
            wrapper['class'] = 'v-expansion-panel-content__wrap'
            # wrap all children
            for child in content.children:
                child.wrap(wrapper)

    for panels in soup.find_all('v-expansion-panels'):
        panels.name = 'div'
        panels['class'] = 'v-expansion-panels'

    return str(soup)


@app.route('/uk/courses/course/<course_id>')
@app.route('/courses/course/<course_id>')
@app.route('/courses/<course_id>')
@app.route('/course/<course_id>')
def course(course_id: str):
    courses_dir = os.path.join(COURSES_LOCATION, course_id)
    if not os.path.exists(courses_dir):
        return 'Course not found', 404

    with open(os.path.join(courses_dir, 'template/template.html'), 'r', encoding='utf-8') as f:
        content = f.read()
    content = edit_course_content(content, course_id)

    js_files = glob.glob(os.path.join(courses_dir, 'js', '*.js'))
    js_files = [os.path.basename(f) for f in js_files]

    return flask.render_template(
        'course.html',
        content=Markup(content),
        course_id=course_id,
        css_files=['style.css'],
        js_files=js_files,
        other_css=[
            f'/{FETCHED_COURSE_CSS_DIR}/{f}' for f in os.listdir(FETCHED_COURSE_CSS_DIR)],
        noheader=flask.request.args.get('noheader') is not None,
    )


@app.route('/uk/courses/course/<course_id>/certificate')
@app.route('/uk/courses/course/<course_id>/c')
@app.route('/courses/course/<course_id>/certificate')
@app.route('/courses/course/<course_id>/c')
@app.route('/course/<course_id>/certificate')
@app.route('/course/<course_id>/c')
@app.route('/uk/verifycertificate/<course_id>')
@app.route('/verifycertificate/<course_id>')
@app.route('/uk/verifycertificate/', defaults={'course_id': None})
@app.route('/verifycertificate/', defaults={'course_id': None})
@app.route('/uk/certificates/<course_id>')
@app.route('/certificates/<course_id>')
@app.route('/certificate/<course_id>')
def certificate(course_id: str):
    course_id = course_id or \
        flask.request.args.get('courseId') or \
        flask.request.args.get('courseID') or \
        flask.request.args.get('courseid') or \
        flask.request.args.get('course_id')

    if course_id is None:
        return 'Course not specified', 404

    courses_dir = os.path.join(COURSES_LOCATION, course_id)
    if not os.path.exists(courses_dir):
        return 'Course not found', 404

    with open(os.path.join(courses_dir, 'template/certificate.html'), 'r', encoding='utf-8') as f:
        content = f.read()

    return flask.render_template(
        'certificate.html',
        content=Markup(content),
        course_id=course_id,
        css_files=['certificate.css'],
        other_css=[
            f'/{FETCHED_CERTIFICATE_CSS_DIR}/{f}' for f in os.listdir(FETCHED_CERTIFICATE_CSS_DIR)],
        noheader=flask.request.args.get('noheader') is not None,
    )


@app.route('/workspaces-assets/course-assets/<course_id>/<path:file_path>')
@app.route('/data/<course_id>/<path:file_path>')
def serve_course_data(course_id: str, file_path: str):
    print(course_id, file_path)
    return flask.send_from_directory(os.path.join(COURSES_LOCATION, course_id), file_path)


def get_courses(certificate=False):
    courses = (c for c in glob.glob(os.path.join(COURSES_LOCATION,
                                                 '*/template/template.html' if not certificate else '*/template/certificate.html'
                                                 ), recursive=True))
    courses = (os.path.dirname(c) for c in courses)
    courses = (os.path.dirname(c) for c in courses)
    courses = (os.path.basename(c) for c in courses)
    courses = (int(c) for c in courses if c.isdigit())
    courses = sorted(courses, reverse=True)
    return courses


@app.route('/')
@app.route('/uk')
@app.route('/uk/courses')
@app.route('/uk/courses/course')
@app.route('/courses/course')
@app.route('/courses')
def index():
    count = flask.request.args.get('count', 10, type=int)
    courses = get_courses()
    courses = courses[:int(count)]
    return flask.render_template(
        'index.html',
        courses=courses,
        count=count,
    )


@app.route('/uk/certificates')
@app.route('/c')
@app.route('/uk/c')
@app.route('/certificates')
def certificates():
    count = flask.request.args.get('count', 10, type=int)
    courses = get_courses(certificate=True)
    courses = courses[:int(count)]
    return flask.render_template(
        'certificates.html',
        courses=courses,
        count=count,
    )


def fetch_css_files(url: str, dir: str):
    os.makedirs(dir, exist_ok=True)
    response = requests.get(url)
    if response.status_code != 200:
        print('Error fetching css')
    # make sure directory is empty
    for f in glob.glob(os.path.join(dir, '*')):
        os.remove(f)
    soup = BeautifulSoup(response.text, 'html.parser')
    css_links = soup.find_all('link', {'rel': 'stylesheet'})
    for link in css_links:
        href = link.get('href', '')
        if not href:
            continue
        response = requests.get(urljoin(url, href))
        if response.status_code != 200:
            print(f'Error fetching {href}')
            continue
        # get filename from url
        filename = os.path.basename(
            href) if 'https://fonts.googleapis.com/' not in href else 'google_fonts.css'

        with open(os.path.join(dir, filename), 'w', encoding='utf-8') as f:
            f.write(response.text)


if __name__ == '__main__':
    if (not DEBUG and FETCH_CSS) or not os.path.exists(FETCHED_COURSE_CSS_DIR):
        print('Fetching course css...')
        fetch_css_files(FETCH_COURSE_CSS_URL, FETCHED_COURSE_CSS_DIR)
    if (not DEBUG and FETCH_CSS) or not os.path.exists(FETCHED_CERTIFICATE_CSS_DIR):
        print('Fetching certificate css...')
        fetch_css_files(FETCH_CERTIFICATE_CSS_URL, FETCHED_CERTIFICATE_CSS_DIR)

    app.run(port=PORT, debug=DEBUG)
