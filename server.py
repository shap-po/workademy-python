import flask
from markupsafe import Markup
from bs4 import BeautifulSoup
import glob
import os
import json

DEFAULT_PORT = 5000

# read config
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        COURSES_LOCATION = config.get('courses_location')
        PORT = config.get('port', DEFAULT_PORT)
except FileNotFoundError:
    config = {
        'courses_location': "",
        'port': DEFAULT_PORT,
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
            p = content.find('p')
            if p:
                wrapper = soup.new_tag('div')
                wrapper['class'] = 'v-expansion-panel-content__wrap'
                p.wrap(wrapper)

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
        noheader=flask.request.args.get('noheader') is not None,
    )


@app.route('/workspaces-assets/course-assets/<course_id>/<path:file_path>')
@app.route('/data/<course_id>/<path:file_path>')
def serve_course_data(course_id: str, file_path: str):
    print(course_id, file_path)
    return flask.send_from_directory(os.path.join(COURSES_LOCATION, course_id), file_path)


@app.route('/')
@app.route('/uk/')
@app.route('/uk/courses/')
@app.route('/uk/courses/course/')
@app.route('/courses/')
@app.route('/courses/course/')
def index():
    courses = (c for c in glob.glob(
        os.path.join(COURSES_LOCATION, '*/template/template.html'), recursive=True))
    courses = (os.path.dirname(c) for c in courses)
    courses = (os.path.dirname(c) for c in courses)
    courses = (os.path.basename(c) for c in courses)
    courses = (int(c) for c in courses if c.isdigit())
    courses = sorted(courses, reverse=True)
    return flask.render_template(
        'index.html',
        courses=courses,
    )


if __name__ == '__main__':
    app.run(port=PORT, debug=True)
