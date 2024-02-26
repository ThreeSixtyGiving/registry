# 360Giving Registry

![360Giving registry logo](registry/static/images/360-logos/360giving-registry.svg)

The [360Giving Registry](http://data.threesixtygiving.org) lists files that use the [360Giving Standard](http://standard.threesixtygiving.org). The list of files is maintained by 360Giving, and this repo contains the source code for the website that obtains the listing from 360Giving (via the Salesforce API) and presents it as a website. The live website is updated once a day from this repo, unless manually triggered.

To download all the files listed in the registy, the 360Giving [datagetter](https://github.com/ThreeSixtyGiving/datagetter) tool is available.

## Install dependencies

```
$ python3 -m venv .ve
$ source .ve/bin/activate
$ pip install -r requirements_dev.txt
```

## Run

Development server
```
$ ./registry/manage.py runserver
```

## Tests
```
$ ./registry/manage.py test tests
```

## Update requirements

```
$ pip install pip-tools
$ pip-compile requirements.in
$ pip-compile requirements_dev.in
```


## Styles - 360-ds

The [360Giving design system](https://github.com/ThreeSixtyGiving/360-ds) is used for styling this project.

To compile the theme, check out the submodule then:

```
cd 360-ds
npm install
npm run compile-sass
cp ./build/360-ds/css/main.css ../registry/ui/static/css/
```

For more information on the design system see the [360-ds project](https://github.com/ThreeSixtyGiving/360-ds)
