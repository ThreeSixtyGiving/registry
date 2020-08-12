from datetime import datetime
import json
import os

from flask import Flask, render_template, current_app, abort
from raven.contrib.flask import Sentry

from registry.registry import get_data_sorted_by_prefix, get_schema_org_list, get_raw_data, RegistryFile
from registry.salesforce import get_salesforce_data

app = Flask(
    __name__,
    static_url_path='',
    static_folder='./static',
    template_folder='./templates',
)
sentry = Sentry(app)


@app.context_processor
def inject_footer_menu():
    with open(os.path.join(os.path.dirname(__file__), 'footer.json')) as a:
        return dict(
            settings360=json.load(a),
            now=datetime.now(),
        )


@app.route('/')
def data_registry():
    raw_data = get_raw_data()
    data = get_data_sorted_by_prefix(raw_data)
    schema = get_schema_org_list(raw_data)

    return render_template(
        'registry.html.j2',
        data=data,
        schema=schema,
        num_of_publishers=len(data)
    )


@app.route('/publisher/<string:prefix>')
def show_publisher(prefix):
    raw_data = get_raw_data()
    files = [
        RegistryFile(f)
        for f in raw_data
        if f.get("publisher", {}).get("prefix") == prefix
    ]

    if not files:
        abort(404)

    publisher = files[0].publisher
    publisher['records'] = 0
    for f in files:
        if f.aggregates.get("count"):
            publisher['records'] += f.aggregates.get("count", 0)

    return render_template(
        'publisher.html.j2',
        publisher=publisher,
        files=files
    )


@app.route('/terms-conditions')
def terms_and_conditions():
    return render_template('terms.html.j2')


@app.route('/data.json')
def salesforce_data():
    data = get_salesforce_data()
    return current_app.response_class(data, mimetype="application/json")


@app.route('/500')
def test_500_error():
    """
    Function to test a 500 error.
    """
    raise Exception
