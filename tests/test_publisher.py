import pytest

from registry.views import app


@pytest.fixture
def client():
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client


def test_publisher_page(client):
    rv = client.get('/publisher/360G-blf')
    assert b"Big Lottery Fund - grants data 2015 to 2017" in rv.data
    assert b"Big Lottery Fund - grants data 2017-18" in rv.data
    assert b"10,674" in rv.data
    assert b"35,470" in rv.data  # count of two files together
    assert b"Missing grant programme" in rv.data
