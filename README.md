# Overmind

This project aims to provider a complete server provisioning and configuration management application.

The first version is a *unified front-end* to public and private clouds, custom server providers and dedicated hardware.

## Features

* EC2 and Rackspace server provisioning. All clouds supported by libcloud will be supported given enough testing
* Provider Plugins: Any provider can be integrated by writing either a libcloud driver or an Overmind provisioning plugin
* Import any server into Overmind witht the "Dedicated Hardware" plugin
* Complete REST API for provider and nodes
* Authentication with three user roles

See the wiki for architectural info and to know more about the future direction of the project.

## Installation

### Requirements

* Python 2.6+
* Django 1.2+
* libcloud
* django-celery
* RabbitMQ (or alternative message queue supported by Celery)

All python dependencies can be installed using the requirements file:

    $ pip install -r requirements.txt

### Install Overmind

* Download the last stable release from
  [http://github.com/tobami/overmind/downloads](http://github.com/tobami/overmind/downloads)
  and unpack it
* Create the DB by changing to the `overmind/` directory and running:

        python manage.py syncdb

* For testing purposes start the celery server on a console

        python manage.py celeryd -l info

  and the django development server

        python manage.py runserver

Now you can visit the Overmind overview page on `localhost:8000/overview`
