EBI
===

Elastic Beanstalk Intelligence, Simple CLI tool for ElasticBeanstalk with Docker.

* Deploying apps more intuitively

  * Without git integration
  * Switch-able ``Dockerrun.aws.json``
  * Switch-able ``.ebextensions/``

Requires Python>=3.5

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
* ``--cfg``: Configuration template to use.
