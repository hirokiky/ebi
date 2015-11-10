EBI
===

Elastic Beanstalk Intelligence, Simple CLI tool for ElasticBeanstalk with Docker.

* Deploying apps more intuitively

  * Without git integration
  * Switch-able ``Dockerrun.aws.json``
  * Switch-able ``.ebextensions/``

Install
-------

::

    pip install ebi


Requires Python2.7 or 3.5

Usage
-----

deploy
~~~~~~

To deploy app, just type it on project root::

    $ ebi deploy <app_name> <env_name>

This will

1. Create zip file including ``Dockerrun.aws.json`` and ``.ebextensions``
2. Uploading zip to S3 as same directory as ``awsebcli``.
3. Deploying app (by calling ``eb deploy`` with uploaded --version)

options:

* ``--version``: version label for app. default is timestamp.
* ``--dockerrun``: File path used as ``Dockerrun.aws.json``.
* ``--ebext``: Directory path used as ``.ebextensions/``
* ``--profile``: Configured profile for AWS.
* ``--region``: region for AWS.

create
~~~~~~

To create app, just type it on project root::

    $ ebi create <app_name> <env_name> <cname_prefix>

This will

1. Create zip file including ``Dockerrun.aws.json`` and ``.ebextensions``
2. Uploading zip to S3 as same directory as ``awsebcli``.
3. Creating app (by calling ``eb create`` with uploaded --version)

options:

* ``--version``: version label for app. default is timestamp.
* ``--dockerrun``: File path used as ``Dockerrun.aws.json``.
* ``--ebext``: Directory path used as ``.ebextensions/``
* ``--profile``: Configured profile for AWS.
* ``--region``: region for AWS.
* ``--cfg``: Configuration template to use.

bgdeploy
~~~~~~~~

To Blue-Green deploye app, just type it on project root::

    $ ebi bgdeploy <app_name> <blue_env_name> <green_env_name> <master_env_cname>

This will

1. Create zip file including ``Dockerrun.aws.json`` and ``.ebextensions``
2. Uploading zip to S3 as same directory as ``awsebcli``.
3. Deploy new version to secondary environment which doen't have `master_env_cname`
   (by calling ``eb deploy`` with uploaded --version)
4. Apply cname for deployed environment

::

    +-------+              +------+
    | green |              | blue |
    +-------+              +------+
     pri.elastic...com      sec.elastic...com
                              ^
                              |
                          3. deploy!

options:

* ``--noswap``: Skip swapping to just deploy secondary environment.
* ``--version``: version label for app. default is timestamp.
* ``--dockerrun``: File path used as ``Dockerrun.aws.json``.
* ``--ebext``: Directory path used as ``.ebextensions/``
* ``--profile``: Configured profile for AWS.
* ``--region``: region for AWS.
* ``--cfg``: Configuration template to use.
